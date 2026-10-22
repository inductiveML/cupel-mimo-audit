"""Informed-agent analysis (pre-registered in results/informed_plan.md). Output: results/informed_analysis.json,
results/informed_cmd_audit.json. Statistics as stepB_analyze.py (exact McNemar, paired bootstrap 10,000, seed 1).
Classification of time-based commands is recomputed from saved trajectories with the unchanged Step-B regexes."""
import glob, json, os, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from analysis_common import classify, strip_heredocs, MT_TARGETED, late_files
from stepB_analyze import mcnemar_exact, boot_ci
import re
# verbatim copies of the regexes in audit_mtime_cmds.py (importing that module would re-run the old audit and
# overwrite results/mtime_cmd_audit.json)
BROAD = re.compile(r"mtime|mmin|newer|--sort|\bls\s+-\S*t|\bstat\b|getmtime|st_mtime|%T|%Y|time-style|full-time|-printf|\bls\s+-\S*l", re.I)
GITHUNT = re.compile(r"git\s+(fsck|reflog|log\s[^|;&]*--all|branch\s+-a|stash\s+list|show-ref|cat-file\s+--batch-all)")

ROOT = CUPEL_ROOT + ""
RES = f"{ROOT}/results"
CAP = 40


def load(path, conds):
    runs = [json.loads(l) for l in open(path)]
    by = {}
    for r in runs:
        if r["cond"] not in conds:
            continue
        tp = f"{ROOT}/runs/{r['task_id']}/{r['cond']}/trajectory.jsonl"
        steps = [json.loads(l) for l in open(tp)]
        cmds = [e["cmd"] for e in steps if e.get("cmd") and e["cmd"].strip() != "echo SUBMIT"]
        pre = [e["cmd"] for e in steps if e.get("cmd") and (not r["first_edit_step"] or e["step"] < r["first_edit_step"])]
        r.update(classify(cmds))
        r["mtime_targeted_before_first_edit"] = classify(pre)["mtime_targeted"]
        r["first_mtime_targeted_step"] = next((e["step"] for e in steps if e.get("cmd") and
                                               MT_TARGETED.search(strip_heredocs(e["cmd"]))), None)
        r["mtime_targeted_in_reply_text"] = any(MT_TARGETED.search(strip_heredocs(e.get("content") or "")) for e in steps)
        ft = next((e for e in steps if e.get("cmd") and MT_TARGETED.search(strip_heredocs(e["cmd"]))), None)
        r["_first_time_cmd"] = (ft["cmd"], ft.get("obs", "")) if ft else None
        eff = next((e["step"] for e in steps if e.get("cmd") and "echo SUBMIT" in e["cmd"]), None)
        r["steps_eff"] = eff or r["steps"]
        by.setdefault(r["task_id"], {})[r["cond"]] = r  # last record wins
    return by


def summarize(P, A, B, label):
    """P: list of (task, recA, recB). Paired A vs B."""
    a = np.array([p[1]["passed"] for p in P], int)
    z = np.array([p[2]["passed"] for p in P], int)
    b = int(((a == 1) & (z == 0)).sum()); c = int(((a == 0) & (z == 1)).sum())
    res = {"label": label, "A": A, "B": B, "n_pairs": len(P), f"pass_A": int(a.sum()), f"pass_B": int(z.sum()),
           "both_pass": int(((a == 1) & (z == 1)).sum()), "both_fail": int(((a == 0) & (z == 0)).sum()),
           "b_Aonly": b, "c_Bonly": c, "mcnemar_exact_p": round(mcnemar_exact(b, c), 4),
           "diff_A_minus_B": boot_ci(a - z) if len(P) else None}
    if not len(P):
        return res

    def paired(key, f=lambda r, k: r[k], only=None):
        sel = [p for p in P if only is None or only(p)]
        if not sel:
            return None
        x = np.array([f(p[1], key) for p in sel], float); y = np.array([f(p[2], key) for p in sel], float)
        return {"n": len(sel), "median_A": float(np.median(x)), "median_B": float(np.median(y)),
                "mean_A": round(float(x.mean()), 4), "mean_B": round(float(y.mean()), 4),
                "mean_diff_ci": boot_ci(x - y), "median_diff_ci": boot_ci(x - y, stat=np.median)}

    both = lambda p: p[1]["passed"] and p[2]["passed"]
    res["steps_both_pass"] = paired("steps", only=both)
    res["steps_all_fail_at_cap"] = paired("steps", f=lambda r, k: r["steps"] if r["passed"] else CAP)
    res["steps_eff_both_pass"] = paired("steps_eff", only=both)
    res["steps_eff_all_fail_at_cap"] = paired("steps_eff", f=lambda r, k: r["steps_eff"] if r["passed"] else CAP)
    for k in ("prompt_tokens", "completion_tokens", "cached_tokens", "cost", "wall_s"):
        res[k] = paired(k)
        res[k + "_both_pass"] = paired(k, only=both)
    res["files_opened_before_first_edit"] = paired("n_files_opened_before_first_edit")
    res["first_edit_step_noedit_as_41"] = paired("first_edit_step", f=lambda r, k: r["first_edit_step"] or CAP + 1)
    res["opened_late_file_before_first_edit"] = paired("x", f=lambda r, k: float(bool(r["late_opened_before_first_edit"])))
    res["final_touches_late"] = paired("x", f=lambda r, k: float(bool(r["final_touches_late"])))
    res["mtime_targeted_before_first_edit"] = paired("x", f=lambda r, k: float(r["mtime_targeted_before_first_edit"]))
    for cond, i in ((A, 1), (B, 2)):
        R = [p[i] for p in P]
        npass = sum(r["passed"] for r in R)
        tot = sum(r["cost"] for r in R)
        res[f"per_cond_{cond}"] = {
            "n": len(R), "pass": npass, "total_cost": round(tot, 4),
            "cost_per_solved": round(tot / npass, 4) if npass else None,
            "mean_cost_solved_runs": round(float(np.mean([r["cost"] for r in R if r["passed"]])), 4) if npass else None,
            "median_steps_solved_runs": float(np.median([r["steps"] for r in R if r["passed"]])) if npass else None,
            "mtime_targeted": sum(r["mtime_targeted"] for r in R),
            "mtime_targeted_before_first_edit": sum(r["mtime_targeted_before_first_edit"] for r in R),
            "mtime_targeted_in_reply_text_attempted": sum(r["mtime_targeted_in_reply_text"] for r in R),
            "mtime_visible_only": sum(r["mtime_visible"] for r in R),
            "median_first_mtime_targeted_step": (float(np.median([r["first_mtime_targeted_step"] for r in R
                                                 if r["first_mtime_targeted_step"]])) if any(r["first_mtime_targeted_step"] for r in R) else None),
            "late_opened_before_first_edit": sum(bool(r["late_opened_before_first_edit"]) for r in R),
            "final_touches_late": sum(bool(r["final_touches_late"]) for r in R),
            "submitted": sum(r["submitted"] for r in R),
            "stop_reasons": {s: sum(r["stop_reason"] == s for r in R) for s in sorted({str(r["stop_reason"]) for r in R})}}
    return res


def audit():
    out = {"n_commands": {}, "broad_hits": [], "githunt_runs": {}}
    for tp in sorted(glob.glob(f"{ROOT}/runs/*/INF-*/trajectory.jsonl")):
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
                          "neither": sum(h["cond"] == c and not h["targeted"] and not h["visible"] for h in H),
                          "runs_with_broad_hit": len({h["task"] for h in H if h["cond"] == c})}
                      for c in sorted(out["n_commands"])}
    out["githunt_runs"] = {k: len(v) for k, v in out["githunt_runs"].items()}
    json.dump(out, open(f"{RES}/informed_cmd_audit.json", "w"), indent=1)
    return {k: v for k, v in out.items() if k != "broad_hits"}


def main():
    inf = load(f"{RES}/informed_runs.jsonl", {"INF-ORIG", "INF-NORM"})
    old = load(f"{RES}/stepB_runs.jsonl", {"ORIG", "NORM"})
    excluded = set(json.load(open(f"{RES}/informed_pilot_excluded.json"))) if os.path.exists(f"{RES}/informed_pilot_excluded.json") else set()
    order = json.load(open(f"{RES}/informed_order.json"))
    prim = set(order["primary_set"])
    strat = {e["task_id"]: e["stratum"] for e in order["order"]}
    allr = {t: {**old.get(t, {}), **inf.get(t, {})} for t in set(old) | set(inf)}

    def pairs(A, B, S=None):
        return [(t, d[A], d[B]) for t, d in sorted(allr.items())
                if A in d and B in d and t not in excluded and (S is None or t in S)]

    out = {"n_tasks_with_INF_pair": len(pairs("INF-ORIG", "INF-NORM")), "excluded_pilot_tasks": sorted(excluded),
           "primary_set": sorted(prim),
           "primary_set_complete": all(len(pairs("INF-ORIG", "INF-NORM", {t})) for t in prim)}
    comps = {"infORIG_vs_infNORM": ("INF-ORIG", "INF-NORM", "primary 1: leak value to an informed agent"),
             "infORIG_vs_ORIG": ("INF-ORIG", "ORIG", "primary 2: value of knowing the trick (ORIG from an earlier day)"),
             "infNORM_vs_NORM": ("INF-NORM", "NORM", "secondary: hint effect without the leak (NORM from an earlier day)"),
             "ORIG_vs_NORM_stepB": ("ORIG", "NORM", "reference: Step B uninformed")}
    for key, (A, B, lab) in comps.items():
        out[key] = {"primary30": summarize(pairs(A, B, prim), A, B, lab + " [primary 30]"),
                    "all": summarize(pairs(A, B), A, B, lab + " [all]")}
        for s_ in ("strong", "random"):
            out[key][f"all_stratum_{s_}"] = summarize(pairs(A, B, {t for t in strat if strat[t] == s_}), A, B,
                                                      lab + f" [all, stratum {s_}]")
    # restrict the cross-day comparisons to tasks that also have the INF pair complete
    # (they are, by construction, unless a pair is incomplete)
    obs = {}
    for S, nm in ((prim, "primary30"), (None, "all")):
        P = pairs("INF-ORIG", "INF-NORM", S)
        for flag in (True, False):
            Q = [p for p in P if p[1]["mtime_targeted_before_first_edit"] == flag]
            obs[f"{nm}:INF-ORIG_time_cmd_before_first_edit={flag}"] = {
                "n": len(Q), "INF-ORIG_pass": sum(p[1]["passed"] for p in Q),
                "INF-NORM_pass_same_tasks": sum(p[2]["passed"] for p in Q),
                "ORIG_pass_same_tasks": sum(allr[p[0]]["ORIG"]["passed"] for p in Q if "ORIG" in allr[p[0]])}
    out["observational_INF-ORIG_time_cmd"] = obs
    # Amendment 2 (post hoc, descriptive): did the output of the first executed time-based command name a late-cluster
    # file? Heuristic: the late file's relative path occurs in the output, or its basename occurs as a whitespace-
    # delimited token and the file is top-level or its parent dir is named in the command. INF-NORM is the control
    # (no time signal, so any 'shown' there is incidental).
    ls_ = {}
    for c in ("INF-ORIG", "INF-NORM"):
        n = shown = opened = shown10 = 0
        ex = []
        for t, d in allr.items():
            r = d.get(c)
            if not r or t in excluded or not r["_first_time_cmd"]:
                continue
            n += 1
            cmd, obs_txt = r["_first_time_cmd"]
            toks = set(obs_txt.split())
            late, _ = late_files(t)
            hit = [f for f in late if f in obs_txt or (os.path.basename(f) in toks and
                   (os.path.dirname(f) == "" or os.path.dirname(f) in cmd))]
            shown += bool(hit)
            opened += bool(set(hit) & set(r["late_opened_before_first_edit"]))
            # stricter: a late file named within the first 10 non-empty lines of the command output
            body = obs_txt.split("<output>", 1)[-1]
            top = [ln for ln in body.splitlines() if ln.strip()][:10]
            top_txt = "\n".join(top); top_toks = set(top_txt.split())
            hit10 = [f for f in late if f in top_txt or (os.path.basename(f) in top_toks and
                     (os.path.dirname(f) == "" or os.path.dirname(f) in cmd))]
            shown10 += bool(hit10)
            ex.append({"task": t, "cmd": cmd[:200], "late_in_top10": bool(hit10)})
        ls_[c] = {"n_runs_time_cmd": n, "output_shows_late": shown, "late_shown_then_opened_pre_edit": opened,
                  "late_in_first_10_output_lines": shown10, "examples": ex}
    out["leak_surfaced"] = ls_
    # descriptive: kind of time-based command executed (any step). find_time = find with -newer*/-mtime/-mmin/-printf %T
    # (file-level, usually recursive); ls_t_only = only `ls -t`-type listings (one directory level each).
    FIND_T = re.compile(r"\bfind\b[^|;&\n]*-(newer\w*|mtime|mmin|ctime|cmin|printf[^|;&\n]*%[TtCc@])")
    kinds = {}
    for c in ("INF-ORIG", "INF-NORM"):
        k = {"runs_any_time_cmd": 0, "runs_find_time": 0, "runs_ls_t_only": 0, "runs_other_only": 0,
             "runs_find_time_before_first_edit": 0}
        for t, d in allr.items():
            r = d.get(c)
            if not r or t in excluded:
                continue
            tp = f"{ROOT}/runs/{t}/{c}/trajectory.jsonl"
            steps = [json.loads(l) for l in open(tp)]
            tc = [(e["step"], strip_heredocs(e["cmd"])) for e in steps if e.get("cmd") and MT_TARGETED.search(strip_heredocs(e["cmd"]))]
            if not tc:
                continue
            k["runs_any_time_cmd"] += 1
            if any(FIND_T.search(x) for _, x in tc):
                k["runs_find_time"] += 1
                if any(FIND_T.search(x) and (not r["first_edit_step"] or st < r["first_edit_step"]) for st, x in tc):
                    k["runs_find_time_before_first_edit"] += 1
            elif all(re.search(r"\bls\b", x) for _, x in tc):
                k["runs_ls_t_only"] += 1
            else:
                k["runs_other_only"] += 1
        kinds[c] = k
    out["time_cmd_kinds"] = kinds
    out["audit_INF"] = audit()
    sp = [json.loads(l) for l in open(f"{RES}/spend_informed.jsonl")] if os.path.exists(f"{RES}/spend_informed.jsonl") else []
    out["spend_informed_total"] = round(sum(r.get("cost") or 0 for r in sp), 4)
    out["spend_informed_n_calls"] = len(sp)
    out["spend_informed_by_kind"] = {}
    for r in sp:
        k = "smoke" if r["run_id"] == "smoke" else ("pilot_excluded" if r["run_id"].split(":")[0] in excluded else r["run_id"].split(":")[1])
        out["spend_informed_by_kind"][k] = out["spend_informed_by_kind"].get(k, 0) + (r.get("cost") or 0)
    out["spend_informed_by_kind"] = {k: round(v, 5) for k, v in out["spend_informed_by_kind"].items()}
    tot_prompt = sum(r.get("prompt_tokens") or 0 for r in sp); tot_cached = sum(r.get("cached_tokens") or 0 for r in sp)
    out["cache_hit_share_prompt_tokens"] = round(tot_cached / tot_prompt, 4) if tot_prompt else None
    out["per_task"] = [{"task_id": t, "primary": t in prim, "stratum": strat.get(t),
                        **{c: d[c]["passed"] for c in ("ORIG", "NORM", "INF-ORIG", "INF-NORM") if c in d},
                        "mt_pre_edit": {c: d[c]["mtime_targeted_before_first_edit"] for c in ("INF-ORIG", "INF-NORM") if c in d},
                        "steps": {c: d[c]["steps"] for c in ("ORIG", "NORM", "INF-ORIG", "INF-NORM") if c in d},
                        "cost": {c: round(d[c]["cost"], 4) for c in ("INF-ORIG", "INF-NORM") if c in d}}
                       for t, d in sorted(allr.items()) if "INF-ORIG" in d or "INF-NORM" in d]
    json.dump(out, open(f"{RES}/informed_analysis.json", "w"), indent=1)
    for key in comps:
        for s in ("primary30", "all"):
            p = out[key][s]
            print(key, s, json.dumps({k: p.get(k) for k in ("n_pairs", "pass_A", "pass_B", "b_Aonly", "c_Bonly",
                                                             "mcnemar_exact_p", "diff_A_minus_B")}))
    print("compliance", {c: out["infORIG_vs_infNORM"]["all"].get(f"per_cond_{c}", {}).get("mtime_targeted_before_first_edit")
                         for c in ("INF-ORIG", "INF-NORM")})
    print("spend", out["spend_informed_total"], "primary complete", out["primary_set_complete"])


if __name__ == "__main__":
    main()
