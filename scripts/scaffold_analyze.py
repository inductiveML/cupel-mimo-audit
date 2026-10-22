"""Scaffold-arm analysis (pre-registered in results/scaffold_plan.md). Output: results/scaffold_analysis.json,
results/scaffold_cmd_audit.json. Statistics as stepB_analyze.py / informed_analyze.py (exact McNemar, paired bootstrap
10,000, seed 1); the paired-summary and loader functions are imported unchanged from informed_analyze.py."""
import glob, json, os, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from analysis_common import classify, strip_heredocs
from stepB_analyze import boot_ci
from informed_analyze import load, summarize, BROAD, GITHUNT

ROOT = CUPEL_ROOT + ""
RES = f"{ROOT}/results"
CONDS = ("ORIG", "NORM", "INF-ORIG", "INF-NORM", "SCF-ORIG", "SCF-NORM")


def first_edit_files(t, c):
    for l in open(f"{ROOT}/runs/{t}/{c}/trajectory.jsonl"):
        e = json.loads(l)
        if e.get("git_state_changed"):
            g = e["git_state_changed"]
            return sorted(set(g["diff"]) | set(g["new_untracked"]))
    return []


def audit():
    out = {"n_commands": {}, "broad_hits": [], "githunt_runs": {}}
    for tp in sorted(glob.glob(f"{ROOT}/runs/*/SCF-*/trajectory.jsonl")):
        t, c = tp.split("/")[-3], tp.split("/")[-2]
        for l in open(tp):
            e = json.loads(l); cmd = e.get("cmd")
            if not cmd:
                continue
            out["n_commands"][c] = out["n_commands"].get(c, 0) + 1
            c2 = strip_heredocs(cmd)
            m = BROAD.search(c2)
            if m:
                k = classify([cmd])
                out["broad_hits"].append({"task": t, "cond": c, "step": e["step"], "targeted": k["mtime_targeted"],
                                          "visible": k["mtime_visible"], "snippet": c2[max(0, m.start() - 60):m.end() + 60]})
            if GITHUNT.search(c2):
                out["githunt_runs"].setdefault(c, set()).add(t)
    H = out["broad_hits"]
    out["summary"] = {c: {"broad_hits": sum(h["cond"] == c for h in H),
                          "targeted": sum(h["cond"] == c and h["targeted"] for h in H),
                          "visible_only": sum(h["cond"] == c and h["visible"] for h in H),
                          "runs_with_broad_hit": len({h["task"] for h in H if h["cond"] == c})}
                      for c in sorted(out["n_commands"])}
    out["githunt_runs"] = {k: len(v) for k, v in out["githunt_runs"].items()}
    json.dump(out, open(f"{RES}/scaffold_cmd_audit.json", "w"), indent=1)
    return {k: v for k, v in out.items() if k != "broad_hits"}


def main():
    scf = load(f"{RES}/scaffold_runs.jsonl", {"SCF-ORIG", "SCF-NORM"})
    inf = load(f"{RES}/informed_runs.jsonl", {"INF-ORIG", "INF-NORM"})
    old = load(f"{RES}/stepB_runs.jsonl", {"ORIG", "NORM"})
    exf = f"{RES}/scaffold_pilot_excluded.json"
    excluded = set(json.load(open(exf))) if os.path.exists(exf) else set()
    order = json.load(open(f"{RES}/scaffold_order.json"))
    prim = set(order["primary_set"])
    strat = {e["task_id"]: e["stratum"] for e in order["order"]}
    allr = {t: {**old.get(t, {}), **inf.get(t, {}), **scf.get(t, {})} for t in set(old) | set(inf) | set(scf)}
    # scaffold-list metrics: own list for SCF-ORIG; the task's SCF-ORIG list ("would-have-been list") for the others
    for t, d in allr.items():
        lst = set(d["SCF-ORIG"]["scaffold_list"]) if "SCF-ORIG" in d else None
        for c, r in d.items():
            fe = first_edit_files(t, c)
            r["_fe"] = fe
            if lst is None:
                continue
            r["fe_in_scf_list"] = float(bool(set(fe) & lst))
            r["final_in_scf_list"] = float(bool(set(r["final_diff_files"]) & lst))
            r["opened_scf_listed_pre_edit"] = float(bool(set(r["files_opened_before_first_edit"]) & lst))

    def pairs(A, B, S=None):
        return [(t, d[A], d[B]) for t, d in sorted(allr.items())
                if A in d and B in d and t not in excluded and (S is None or t in S)]

    def extra(P):
        if not P:
            return None
        o = {}
        for k in ("fe_in_scf_list", "final_in_scf_list", "opened_scf_listed_pre_edit"):
            Q = [p for p in P if k in p[1] and k in p[2]]
            if Q:
                x = np.array([p[1][k] for p in Q]); y = np.array([p[2][k] for p in Q])
                o[k] = {"n": len(Q), "A": int(x.sum()), "B": int(y.sum()), "mean_diff_ci": boot_ci(x - y)}
        return o

    out = {"n_tasks_with_SCF_pair": len(pairs("SCF-ORIG", "SCF-NORM")), "excluded_pilot_tasks": sorted(excluded),
           "primary_set": sorted(prim),
           "primary_set_complete": all(len(pairs("SCF-ORIG", "SCF-NORM", {t})) for t in prim)}
    comps = {"scfORIG_vs_scfNORM": ("SCF-ORIG", "SCF-NORM", "primary: leak value under forced compliance"),
             "scfORIG_vs_infORIG": ("SCF-ORIG", "INF-ORIG", "secondary: scaffold vs hint (cross-day)"),
             "scfORIG_vs_ORIG": ("SCF-ORIG", "ORIG", "secondary: scaffold vs uninformed (cross-day)"),
             "scfNORM_vs_NORM": ("SCF-NORM", "NORM", "secondary: empty scaffold block vs uninformed NORM (cross-day)"),
             "scfNORM_vs_infNORM": ("SCF-NORM", "INF-NORM", "descriptive: empty scaffold vs hinted NORM (cross-day)"),
             "infORIG_vs_infNORM": ("INF-ORIG", "INF-NORM", "reference: section 7"),
             "ORIG_vs_NORM_stepB": ("ORIG", "NORM", "reference: Step B")}
    for key, (A, B, lab) in comps.items():
        out[key] = {}
        for nm, S in (("primary30", prim), ("all", None)):
            P = pairs(A, B, S)
            out[key][nm] = summarize(P, A, B, lab + f" [{nm}]")
            out[key][nm]["scaffold_list_metrics"] = extra(P)
        for s_ in ("strong", "random"):
            out[key][f"all_stratum_{s_}"] = summarize(pairs(A, B, {t for t in strat if strat[t] == s_}), A, B,
                                                      lab + f" [all, stratum {s_}]")
    # scaffold output descriptives
    sd = {}
    for c in ("SCF-ORIG", "SCF-NORM"):
        R = [d[c] for t, d in allr.items() if c in d and t not in excluded]
        sd[c] = {"n": len(R), "n_lines_hist": {str(k): sum(r["scaffold_n_lines"] == k for r in R)
                                               for k in sorted({r["scaffold_n_lines"] for r in R})},
                 "empty_output": sum(r["scaffold_n_lines"] == 0 for r in R),
                 "rank1_is_late": sum(r["scaffold_rank1_is_late"] for r in R),
                 "scaffold_rc_nonzero": sum(r["scaffold_rc"] != 0 for r in R),
                 "n_newer_than_epoch1_zero": sum(r["n_newer_than_epoch1"] == 0 for r in R)}
    out["scaffold_output"] = sd
    # per-condition first-edit-in-list counts (vs the task's SCF-ORIG list), all tasks with an SCF-ORIG run
    fe = {}
    for c in CONDS:
        R = [d[c] for t, d in allr.items() if c in d and "fe_in_scf_list" in d[c] and t not in excluded]
        fe[c] = {"n": len(R), "first_edit_in_list": int(sum(r["fe_in_scf_list"] for r in R)),
                 "final_in_list": int(sum(r["final_in_scf_list"] for r in R)),
                 "no_edit": sum(1 for r in R if not r["first_edit_step"])}
    out["scaffold_list_overlap_by_cond"] = fe
    # observational: SCF-ORIG pass by whether the first edit was in the list
    P = pairs("SCF-ORIG", "SCF-NORM")
    out["observational_fe_in_list"] = {str(f): {"n": len(Q), "SCF-ORIG_pass": sum(p[1]["passed"] for p in Q),
                                                "SCF-NORM_pass": sum(p[2]["passed"] for p in Q)}
                                       for f in (True, False) for Q in [[p for p in P if bool(p[1]["fe_in_scf_list"]) == f]]}
    # decision rule (pre-registered verbatim in scaffold_plan.md)
    a = out["scfORIG_vs_scfNORM"]["all"]
    d, lo, hi = a["diff_A_minus_B"] if a["diff_A_minus_B"] else (None, None, None)
    out["decision_rule"] = {"n_pairs": a["n_pairs"], "diff_pp": round(100 * d, 2) if d is not None else None,
                            "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)] if d is not None else None,
                            "threshold_pp": 15.0,
                            "verdict": (None if d is None else ("Medium" if 100 * d >= 15.0 - 1e-9 else "Low"))}
    out["audit_SCF"] = audit()
    sp = [json.loads(l) for l in open(f"{RES}/spend_scaffold.jsonl")] if os.path.exists(f"{RES}/spend_scaffold.jsonl") else []
    out["spend_scaffold_total"] = round(sum(r.get("cost") or 0 for r in sp), 4)
    out["spend_scaffold_n_calls"] = len(sp)
    bk = {}
    for r in sp:
        k = "smoke" if r["run_id"] == "smoke" else ("pilot_excluded" if r["run_id"].split(":")[0] in excluded else r["run_id"].split(":")[1])
        bk[k] = bk.get(k, 0) + (r.get("cost") or 0)
    out["spend_scaffold_by_kind"] = {k: round(v, 5) for k, v in bk.items()}
    tp_ = sum(r.get("prompt_tokens") or 0 for r in sp); tc_ = sum(r.get("cached_tokens") or 0 for r in sp)
    out["cache_hit_share_prompt_tokens"] = round(tc_ / tp_, 4) if tp_ else None
    out["per_task"] = [{"task_id": t, "primary": t in prim, "stratum": strat.get(t),
                        "pass": {c: d[c]["passed"] for c in CONDS if c in d},
                        "steps": {c: d[c]["steps"] for c in CONDS if c in d},
                        "first_edit_step": {c: d[c]["first_edit_step"] for c in ("SCF-ORIG", "SCF-NORM") if c in d},
                        "fe_in_scf_list": {c: d[c].get("fe_in_scf_list") for c in ("SCF-ORIG", "SCF-NORM") if c in d},
                        "scaffold_rank1": d["SCF-ORIG"]["scaffold_rank1"] if "SCF-ORIG" in d else None,
                        "scaffold_n_lines": {c: d[c]["scaffold_n_lines"] for c in ("SCF-ORIG", "SCF-NORM") if c in d},
                        "cost": {c: round(d[c]["cost"], 4) for c in ("SCF-ORIG", "SCF-NORM") if c in d}}
                       for t, d in sorted(allr.items()) if "SCF-ORIG" in d or "SCF-NORM" in d]
    for d in allr.values():
        for r in d.values():
            r.pop("_fe", None); r.pop("_first_time_cmd", None)
    json.dump(out, open(f"{RES}/scaffold_analysis.json", "w"), indent=1)
    for key in comps:
        for s in ("primary30", "all"):
            p = out[key][s]
            print(key, s, json.dumps({k: p.get(k) for k in ("n_pairs", "pass_A", "pass_B", "b_Aonly", "c_Bonly",
                                                             "mcnemar_exact_p", "diff_A_minus_B")}))
    print("decision", out["decision_rule"]); print("scaffold_output", sd)
    print("spend", out["spend_scaffold_total"], "primary complete", out["primary_set_complete"])


if __name__ == "__main__":
    main()
