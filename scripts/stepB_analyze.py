"""Step B analysis (pre-registered in results/stepB_plan.md). Output: results/stepB_analysis.json"""
import json, os
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
from math import comb
import numpy as np
import sys
sys.path.insert(0, os.path.dirname(__file__))
from analysis_common import classify

RES = CUPEL_ROOT + "/results"
CAP = 40
B = 10000


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


def boot_ci(diff, stat=np.mean, seed=1):
    diff = np.asarray(diff, float)
    if len(diff) == 0:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), (B, len(diff)))
    bs = np.array([stat(diff[i]) for i in idx]) if stat is not np.mean else diff[idx].mean(1)
    return [round(float(stat(diff)), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


def main():
    runs = [json.loads(l) for l in open(f"{RES}/stepB_runs.jsonl")]
    state = json.load(open(f"{RES}/stepB_state.json"))
    excluded_pilot = set(json.load(open(f"{RES}/stepB_pilot_excluded.json"))) if os.path.exists(f"{RES}/stepB_pilot_excluded.json") else set()
    for r in runs:  # re-classify from saved trajectories (same regexes for every run)
        tp = f"{CUPEL_ROOT}/runs/{r['task_id']}/{r['cond']}/trajectory.jsonl"
        cmds = [json.loads(l).get("cmd") for l in open(tp)]
        cmds = [c for c in cmds if c and c.strip() != "echo SUBMIT"]
        steps_cmd = [json.loads(l) for l in open(tp)]
        pre = [e["cmd"] for e in steps_cmd if e.get("cmd") and (not r["first_edit_step"] or e["step"] < r["first_edit_step"])]
        r.update(classify(cmds))
        # effective steps: first step whose command contains `echo SUBMIT` in any form (the loop only stops on a
        # bare `echo SUBMIT`; e.g. `cd /testbed && echo SUBMIT` kept some runs going until the cap)
        eff = next((e["step"] for e in steps_cmd if e.get("cmd") and "echo SUBMIT" in e["cmd"]), None)
        r["steps_eff"] = eff or r["steps"]
        r["submitted_eff"] = eff is not None
        r["mtime_targeted_before_first_edit"] = classify(pre)["mtime_targeted"]
    by = {}
    for r in runs:
        by.setdefault(r["task_id"], {})[r["cond"]] = r  # last record wins
    pairs = [(t, d["ORIG"], d["NORM"]) for t, d in by.items() if "ORIG" in d and "NORM" in d and t not in excluded_pilot]
    out = {"n_pairs": len(pairs), "excluded_pilot_tasks": sorted(excluded_pilot)}

    def summarize(P, label):
        o = np.array([p[1]["passed"] for p in P], int)
        n = np.array([p[2]["passed"] for p in P], int)
        b = int(((o == 1) & (n == 0)).sum()); c = int(((o == 0) & (n == 1)).sum())
        res = {"label": label, "n_pairs": len(P), "pass_ORIG": int(o.sum()), "pass_NORM": int(n.sum()),
               "both_pass": int(((o == 1) & (n == 1)).sum()), "both_fail": int(((o == 0) & (n == 0)).sum()),
               "b_ORIGonly": b, "c_NORMonly": c, "mcnemar_exact_p": round(mcnemar_exact(b, c), 4),
               "diff_ORIG_minus_NORM": boot_ci(o - n) if len(P) else None}
        if not len(P):
            return res

        def paired(key, f=lambda r, k: r[k], only=None):
            sel = [p for p in P if only is None or only(p)]
            a = np.array([f(p[1], key) for p in sel], float); z = np.array([f(p[2], key) for p in sel], float)
            if not len(sel):
                return None
            return {"n": len(sel), "median_ORIG": float(np.median(a)), "median_NORM": float(np.median(z)),
                    "mean_ORIG": round(float(a.mean()), 3), "mean_NORM": round(float(z.mean()), 3),
                    "mean_diff_ci": boot_ci(a - z), "median_diff_ci": boot_ci(a - z, stat=np.median)}

        steps_cap = lambda r, k: r["steps"] if r["passed"] else CAP
        res["steps_both_pass"] = paired("steps", only=lambda p: p[1]["passed"] and p[2]["passed"])
        res["steps_all_fail_at_cap"] = paired("steps", f=steps_cap)
        res["steps_eff_both_pass"] = paired("steps_eff", only=lambda p: p[1]["passed"] and p[2]["passed"])
        res["steps_eff_all_fail_at_cap"] = paired("steps_eff", f=lambda r, k: r["steps_eff"] if r["passed"] else CAP)
        res["prompt_tokens"] = paired("prompt_tokens")
        res["completion_tokens"] = paired("completion_tokens")
        res["cost"] = paired("cost")
        res["wall_s"] = paired("wall_s")
        res["files_opened_before_first_edit"] = paired("n_files_opened_before_first_edit")
        fe = lambda r, k: r["first_edit_step"] if r["first_edit_step"] else CAP + 1
        res["first_edit_step_noedit_as_41"] = paired("first_edit_step", f=fe)
        late_pre = lambda r, k: float(bool(r["late_opened_before_first_edit"]))
        res["opened_late_file_before_first_edit"] = paired("x", f=late_pre)
        res["final_touches_late"] = paired("x", f=lambda r, k: float(bool(r["final_touches_late"])))
        for cond, i in (("ORIG", 1), ("NORM", 2)):
            R = [p[i] for p in P]
            res[f"rate_{cond}"] = {"mtime_targeted": sum(r["mtime_targeted"] for r in R),
                                   "mtime_targeted_before_first_edit": sum(r["mtime_targeted_before_first_edit"] for r in R),
                                   "mtime_visible": sum(r["mtime_visible"] for r in R), "n": len(R),
                                   "submitted": sum(r["submitted"] for r in R),
                                   "stop_reasons": {s: sum(r["stop_reason"] == s for r in R) for s in {r["stop_reason"] for r in R}}}
        return res

    strat = {t: v.get("stratum") for t, v in state["tasks"].items()}
    sel = json.load(open(f"{RES}/stepB_selection.json"))
    valid = {t for t, v in state["tasks"].items() if (v.get("validation") or {}).get("ok")}
    prim = set([t for t in sel["strong_order"] if t in valid][:20] + [t for t in sel["random_order"] if t in valid][:10])
    as_run = set(json.load(open(f"{RES}/stepB_primary_prebug_set.json"))["primary_taken_order"]) \
        if os.path.exists(f"{RES}/stepB_primary_prebug_set.json") else set()
    out["primary_set"] = sorted(prim)
    out["primary_set_complete"] = all(t in by and "ORIG" in by[t] and "NORM" in by[t] for t in prim)
    out["primary"] = summarize([p for p in pairs if p[0] in prim], "primary: pre-registered 20 strong + 10 random (Amendment 2 corrected)")
    out["prereg_as_run"] = summarize([p for p in pairs if p[0] in as_run], "sensitivity: the 30 tasks as originally run (with the network-regex bug)")
    out["all_pairs"] = summarize(pairs, "secondary: all pairs incl. extension (Amendment 3)")
    for s_ in ("strong", "random"):
        out[f"primary_stratum_{s_}"] = summarize([p for p in pairs if p[0] in prim and strat.get(p[0]) == s_], f"primary, stratum {s_}")
        out[f"all_stratum_{s_}"] = summarize([p for p in pairs if strat.get(p[0]) == s_], f"all pairs, stratum {s_}")
    # observational: ORIG runs with vs without mtime-targeted command
    obs = {}
    for flag in (True, False):
        P = [p for p in pairs if p[1]["mtime_targeted"] == flag]  # all pairs
        obs[f"ORIG_mtime_targeted={flag}"] = {"n": len(P), "ORIG_pass": sum(p[1]["passed"] for p in P),
                                              "NORM_pass_same_tasks": sum(p[2]["passed"] for p in P)}
    out["observational_ORIG_mtime_targeted"] = obs
    out["total_cost_runs"] = round(sum(r["cost"] for r in runs), 4)
    out["per_pair"] = [{"task_id": t, "stratum": strat.get(t), "ORIG": o["passed"], "NORM": n["passed"],
                        "steps": [o["steps"], n["steps"]], "cost": [round(o["cost"], 4), round(n["cost"], 4)],
                        "mt_targeted": [o["mtime_targeted"], n["mtime_targeted"]],
                        "late_touched": [bool(o["final_touches_late"]), bool(n["final_touches_late"])]}
                       for t, o, n in pairs]
    json.dump(out, open(f"{RES}/stepB_analysis.json", "w"), indent=1)
    for k in ("primary", "prereg_as_run", "all_pairs"):
        p = out[k]
        print(k, json.dumps({k: p.get(k) for k in ("n_pairs", "pass_ORIG", "pass_NORM", "b_ORIGonly", "c_NORMonly",
                                            "mcnemar_exact_p", "diff_ORIG_minus_NORM")}))
    print("primary complete:", out["primary_set_complete"])


if __name__ == "__main__":
    main()
