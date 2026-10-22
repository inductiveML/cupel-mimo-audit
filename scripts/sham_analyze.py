"""Cupel sham-arm analysis (pre-registered in results/sham_plan.md). Outputs: results/sham_analysis.json,
results/sham_task_buckets.csv. Statistics as §8 (exact McNemar, paired bootstrap 10,000, seed 1); summarize/boot_ci
imported unchanged."""
import csv, json, os, re, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from analysis_common import strip_heredocs
from stepB_analyze import boot_ci
from informed_analyze import load, summarize, GITHUNT

ROOT = CUPEL_ROOT + ""
RES = f"{ROOT}/results"
CONDS = ("ORIG", "NORM", "INF-ORIG", "INF-NORM", "SCF-ORIG", "SCF-NORM", "SCF-SHAM")
CAP = 40


def traj(t, c):
    return [json.loads(l) for l in open(f"{ROOT}/runs/{t}/{c}/trajectory.jsonl")]


ALL_AVAILABLE = "--all-available" in sys.argv  # sensitivity: include runs outside the $2.00-cap set
SUF = "_all_available" if ALL_AVAILABLE else ""


def main():
    sham = load(f"{RES}/sham_runs.jsonl", {"SCF-SHAM"})
    capf = f"{RES}/sham_capset.json"
    capset = set(json.load(open(capf))["tasks"]) if os.path.exists(capf) else None
    if capset is not None and not ALL_AVAILABLE:
        sham = {t: v for t, v in sham.items() if t in capset}
    scf = load(f"{RES}/scaffold_runs.jsonl", {"SCF-ORIG", "SCF-NORM"})
    inf = load(f"{RES}/informed_runs.jsonl", {"INF-ORIG", "INF-NORM"})
    old = load(f"{RES}/stepB_runs.jsonl", {"ORIG", "NORM"})
    exf = f"{RES}/sham_pilot_excluded.json"
    excluded = set(json.load(open(exf))) if os.path.exists(exf) else set()
    order = json.load(open(f"{RES}/scaffold_order.json"))
    prim = set(order["primary_set"]); strat = {e["task_id"]: e["stratum"] for e in order["order"]}
    SL = {p["task_id"]: p for p in json.load(open(f"{RES}/sham_lists.json"))["per_task"]}
    sa = {json.loads(l)["task_id"]: json.loads(l) for l in open(f"{RES}/stepA_per_task.jsonl")}
    allr = {t: {**old.get(t, {}), **inf.get(t, {}), **scf.get(t, {}), **sham.get(t, {})}
            for t in set(old) | set(inf) | set(scf) | set(sham)}
    for t, d in allr.items():
        olist = set(SL[t]["orig_list"]) if t in SL else set()
        slist = set(SL[t]["sham_list"]) if t in SL else set()
        for c, r in d.items():
            steps = traj(t, c)
            fe = next((sorted(set(e["git_state_changed"]["diff"]) | set(e["git_state_changed"]["new_untracked"]))
                       for e in steps if e.get("git_state_changed")), [])
            gh = [e["step"] for e in steps if e.get("cmd") and GITHUNT.search(strip_heredocs(e["cmd"]))]
            r["githunt"] = float(bool(gh))
            r["githunt_pre_edit"] = float(bool(gh) and gh[0] < (r["first_edit_step"] or CAP + 1))
            r["n_githunt_cmds"] = len(gh)
            r["step_cap_stop"] = float(r["stop_reason"] == "step_cap")
            r["fe_in_orig_list"] = float(bool(set(fe) & olist))
            r["final_in_orig_list"] = float(bool(set(r["final_diff_files"]) & olist))
            r["fe_in_sham_list"] = float(bool(set(fe) & slist))
            r["final_in_sham_list"] = float(bool(set(r["final_diff_files"]) & slist))
            r["opened_sham_pre_edit"] = float(bool(set(r["files_opened_before_first_edit"]) & slist))
            r["opened_orig_pre_edit"] = float(bool(set(r["files_opened_before_first_edit"]) & olist))

    def pairs(A, B, S=None):
        return [(t, d[A], d[B]) for t, d in sorted(allr.items())
                if A in d and B in d and t not in excluded and (S is None or t in S)]

    def extra(P):
        if not P:
            return None
        o = {}
        for k in ("githunt", "githunt_pre_edit", "n_githunt_cmds", "step_cap_stop", "fe_in_orig_list",
                  "final_in_orig_list", "fe_in_sham_list", "final_in_sham_list", "opened_sham_pre_edit",
                  "opened_orig_pre_edit"):
            x = np.array([p[1][k] for p in P], float); y = np.array([p[2][k] for p in P], float)
            o[k] = {"n": len(P), "A": round(float(x.sum()), 2), "B": round(float(y.sum()), 2), "mean_diff_ci": boot_ci(x - y)}
        return o

    out = {"analysed_set": "all available SCF-SHAM runs (sensitivity, includes runs outside the $2.00 cap)" if ALL_AVAILABLE
           else "SCF-SHAM runs completed under the pre-registered $2.00 cap (results/sham_capset.json)",
           "n_tasks_with_SHAM": sum("SCF-SHAM" in d for t, d in allr.items() if t not in excluded),
           "excluded_pilot_tasks": sorted(excluded),
           "primary_set_complete": all(len(pairs("SCF-ORIG", "SCF-SHAM", {t})) for t in prim),
           "note": "SCF-ORIG/SCF-NORM ran 2026-10-20/21 (results/scaffold_runs.jsonl, not re-run); cross-day pairing."}
    comps = {"scfORIG_vs_scfSHAM": ("SCF-ORIG", "SCF-SHAM", "primary: ORIG list vs sham list"),
             "scfSHAM_vs_scfNORM": ("SCF-SHAM", "SCF-NORM", "secondary: sham list vs empty list"),
             "scfSHAM_vs_NORM": ("SCF-SHAM", "NORM", "secondary: sham list vs Step-B NORM (no list)"),
             "scfORIG_vs_scfNORM": ("SCF-ORIG", "SCF-NORM", "reference: section 8"),
             "scfSHAM_vs_ORIG": ("SCF-SHAM", "ORIG", "descriptive: sham vs Step-B ORIG"),
             "scfSHAM_vs_infNORM": ("SCF-SHAM", "INF-NORM", "descriptive: sham vs INF-NORM")}
    for key, (A, B, lab) in comps.items():
        out[key] = {}
        for nm, S in (("primary30", prim), ("all", None)):
            P = pairs(A, B, S)
            out[key][nm] = summarize(P, A, B, lab + f" [{nm}]")
            out[key][nm]["extra"] = extra(P)
        for s_ in ("strong", "random"):
            out[key][f"all_stratum_{s_}"] = summarize(pairs(A, B, {t for t in strat if strat[t] == s_}), A, B,
                                                      lab + f" [all, stratum {s_}]")
    # per-condition efficiency (all tasks with a SHAM run)
    T = sorted(t for t, d in allr.items() if "SCF-SHAM" in d and t not in excluded)
    pc = {}
    for c in CONDS:
        R = [allr[t][c] for t in T if c in allr[t]]
        npass = sum(r["passed"] for r in R); tot = sum(r["cost"] for r in R)
        pc[c] = {"n": len(R), "pass": npass, "step_cap_stops": int(sum(r["step_cap_stop"] for r in R)),
                 "stop_reasons": {s: sum(str(r["stop_reason"]) == s for r in R) for s in sorted({str(r["stop_reason"]) for r in R})},
                 "no_edit": sum(1 for r in R if not r["first_edit_step"]),
                 "median_first_edit_step_noedit41": float(np.median([r["first_edit_step"] or 41 for r in R])),
                 "mean_first_edit_step_noedit41": round(float(np.mean([r["first_edit_step"] or 41 for r in R])), 2),
                 "median_steps_solved": float(np.median([r["steps"] for r in R if r["passed"]])) if npass else None,
                 "mean_steps_fail_at_40": round(float(np.mean([r["steps"] if r["passed"] else CAP for r in R])), 2),
                 "mean_files_opened_pre_edit": round(float(np.mean([r["n_files_opened_before_first_edit"] for r in R])), 2),
                 "githunt_runs": int(sum(r["githunt"] for r in R)),
                 "githunt_pre_edit_runs": int(sum(r["githunt_pre_edit"] for r in R)),
                 "total_cost": round(tot, 4), "cost_per_solved": round(tot / npass, 4) if npass else None,
                 "fe_in_orig_list": int(sum(r["fe_in_orig_list"] for r in R)),
                 "final_in_orig_list": int(sum(r["final_in_orig_list"] for r in R)),
                 "fe_in_sham_list": int(sum(r["fe_in_sham_list"] for r in R)),
                 "final_in_sham_list": int(sum(r["final_in_sham_list"] for r in R)),
                 "opened_sham_pre_edit": int(sum(r["opened_sham_pre_edit"] for r in R)),
                 "late_opened_before_first_edit": sum(bool(r["late_opened_before_first_edit"]) for r in R),
                 "mtime_targeted": sum(r["mtime_targeted"] for r in R)}
    out["per_condition"] = pc
    out["scfORIG_vs_scfNORM_on_sham_tasks"] = summarize(pairs("SCF-ORIG", "SCF-NORM", set(T)), "SCF-ORIG", "SCF-NORM",
                                                        "reference: section 8 contrast restricted to the analysed SCF-SHAM tasks")
    # heterogeneity (exploratory)
    def grp_short_src(t):
        s = sa[t]; return 1 <= s["n_late"] <= 10 and s["n_late_source"] >= 1

    def size_bin(t):
        n = sa[t]["n_late"]; return "1-2" if n <= 2 else "3-4" if n <= 4 else "5-10" if n <= 10 else ">10"

    het = {}
    for gname, gf in (("stratum", lambda t: strat[t]), ("short_src_cluster", lambda t: "yes" if grp_short_src(t) else "no"),
                      ("late_size_bin", size_bin)):
        het[gname] = {}
        for g in sorted({gf(t) for t in T}):
            S = {t for t in T if gf(t) == g}
            P = pairs("SCF-ORIG", "SCF-SHAM", S)
            s_ = summarize(P, "SCF-ORIG", "SCF-SHAM", f"exploratory {gname}={g}")
            Pn = pairs("SCF-ORIG", "SCF-NORM", S)
            het[gname][g] = {"n": len(P), "ORIG_pass": s_["pass_A"], "SHAM_pass": s_["pass_B"],
                             "b": s_["b_Aonly"], "c": s_["c_Bonly"], "p": s_["mcnemar_exact_p"],
                             "pass_diff_ci": s_["diff_A_minus_B"],
                             "first_edit_diff_ci": (s_.get("first_edit_step_noedit_as_41") or {}).get("mean_diff_ci"),
                             "steps_fail40_diff_ci": (s_.get("steps_all_fail_at_cap") or {}).get("mean_diff_ci"),
                             "SCF_NORM_pass": sum(p[2]["passed"] for p in Pn),
                             "step_cap_ORIG": int(sum(p[1]["step_cap_stop"] for p in P)),
                             "step_cap_SHAM": int(sum(p[2]["step_cap_stop"] for p in P))}
    out["heterogeneity_exploratory"] = het
    # sham descriptives
    R = [allr[t]["SCF-SHAM"] for t in T]
    out["sham_output"] = {"n": len(R), "lines_equal_k": sum(r["scaffold_n_lines"] == SL[r["task_id"]]["k"] for r in R),
                          "real_scaffold_empty": sum(r["scaffold_real_n_lines"] == 0 for r in R),
                          "runs_with_missing_sham_files": sum(bool(r["sham_missing"]) for r in R),
                          "n_newer_than_epoch1_zero": sum(r["n_newer_than_epoch1"] == 0 for r in R),
                          "tasks_late_in_sham": [t for t in T if SL[t]["late_in_sham"]],
                          "tasks_rfix_in_sham": [t for t in T if SL[t]["rfix_in_sham"]]}
    # decision rule (pre-registered verbatim in sham_plan.md)
    a = out["scfORIG_vs_scfSHAM"]["all"]
    d, lo, hi = a["diff_A_minus_B"] if a["diff_A_minus_B"] else (None, None, None)
    out["decision_rule"] = {"n_pairs": a["n_pairs"], "diff_pp": round(100 * d, 2) if d is not None else None,
                            "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)] if d is not None else None,
                            "threshold_pp": 15.0,
                            "verdict": (None if d is None else ("Medium" if 100 * d >= 15.0 - 1e-9 else "Low"))}
    # side-channel presence on the 73 tasks (live SCF-ORIG list rank-1 is a late-cluster file; list non-empty)
    S0 = [allr[t]["SCF-ORIG"] for t in T]
    out["side_channel"] = {"n": len(S0), "orig_list_nonempty": sum(r["scaffold_n_lines"] > 0 for r in S0),
                           "rank1_is_late": sum(r["scaffold_rank1_is_late"] for r in S0),
                           "nnewer_epoch1_positive": sum(r["n_newer_than_epoch1"] > 0 for r in S0)}
    allsa = [json.loads(l) for l in open(f"{RES}/stepA_per_task.jsonl")]
    out["side_channel"]["stepA_tasks"] = len(allsa)
    out["side_channel"]["stepA_flagged_mtime_scope"] = sum(bool(x["flagged"]) for x in allsa)
    out["side_channel"]["stepA_flagged_share"] = round(out["side_channel"]["stepA_flagged_mtime_scope"] / len(allsa), 4)
    # normalisation fix: every NORM-prep run verified 0 entries newer than @1 (all files under cwd at the epoch)
    nr = [allr[t][c] for t in allr for c in ("NORM", "INF-NORM", "SCF-NORM", "SCF-SHAM") if c in allr[t] and t not in excluded]
    out["normalisation_fix_check"] = {"n_norm_prep_runs": len(nr), "verified_zero_newer": sum(r["n_newer_than_epoch1"] == 0 for r in nr)}
    sp = [json.loads(l) for l in open(f"{RES}/spend_sham.jsonl")] if os.path.exists(f"{RES}/spend_sham.jsonl") else []
    out["spend_sham_total_file"] = round(sum(r.get("cost") or 0 for r in sp), 4)
    inset = lambda r: r["run_id"] == "smoke" or capset is None or r["run_id"].split(":")[0] in capset
    out["spend_sham_capset"] = round(sum(r.get("cost") or 0 for r in sp if inset(r)), 4)
    out["spend_sham_outside_capset"] = round(sum(r.get("cost") or 0 for r in sp if not inset(r)), 4)
    out["spend_sham_total"] = out["spend_sham_total_file"] if ALL_AVAILABLE else out["spend_sham_capset"]
    sp = sp if ALL_AVAILABLE else [r for r in sp if inset(r)]
    out["spend_sham_n_calls"] = len(sp)
    bk = {}
    for r in sp:
        k = "smoke" if r["run_id"] == "smoke" else ("pilot_excluded" if r["run_id"].split(":")[0] in excluded else "SCF-SHAM")
        bk[k] = bk.get(k, 0) + (r.get("cost") or 0)
    out["spend_sham_by_kind"] = {k: round(v, 5) for k, v in bk.items()}
    tp_ = sum(r.get("prompt_tokens") or 0 for r in sp); tc_ = sum(r.get("cached_tokens") or 0 for r in sp)
    out["cache_hit_share_prompt_tokens"] = round(tc_ / tp_, 4) if tp_ else None
    # per task + buckets
    rows = []
    for t in T:
        d = allr[t]; s = sa[t]
        o_, h_ = d["SCF-ORIG"], d["SCF-SHAM"]
        rows.append({"task_id": t, "primary": t in prim, "stratum": strat[t], "n_late": s["n_late"],
                     "n_late_source": s["n_late_source"], "late_overlaps_test_patch": s["late_overlap_rtest"] >= 1,
                     "has_R_fix": bool(SL[t]["has_R_fix"]),
                     "bucket": "Higher" if grp_short_src(t) else "Low",
                     "orig_list_lines": SL[t]["k"], "rank1_is_late": o_["scaffold_rank1_is_late"],
                     "sham_has_late": bool(SL[t]["late_in_sham"]), "sham_has_rfix": bool(SL[t]["rfix_in_sham"]),
                     "pass_SCF_ORIG": int(o_["passed"]), "pass_SCF_SHAM": int(h_["passed"]),
                     "pass_SCF_NORM": int(d["SCF-NORM"]["passed"]) if "SCF-NORM" in d else "",
                     "first_edit_SCF_ORIG": o_["first_edit_step"] or 41, "first_edit_SCF_SHAM": h_["first_edit_step"] or 41,
                     "steps_SCF_ORIG": o_["steps"], "steps_SCF_SHAM": h_["steps"],
                     "stop_SCF_ORIG": o_["stop_reason"], "stop_SCF_SHAM": h_["stop_reason"]})
    out["per_task"] = rows
    for e in order["order"]:  # tasks without an analysed SCF-SHAM run: bucket from Step-A data only, outcomes blank
        t = e["task_id"]
        if t in T:
            continue
        s, d = sa[t], allr.get(t, {})
        rows.append({k: "" for k in rows[0]} | {"task_id": t, "primary": t in prim, "stratum": strat[t], "n_late": s["n_late"],
                     "n_late_source": s["n_late_source"], "late_overlaps_test_patch": s["late_overlap_rtest"] >= 1,
                     "has_R_fix": bool(SL[t]["has_R_fix"]), "bucket": "Higher" if grp_short_src(t) else "Low",
                     "orig_list_lines": SL[t]["k"],
                     "rank1_is_late": d["SCF-ORIG"]["scaffold_rank1_is_late"] if "SCF-ORIG" in d else "",
                     "sham_has_late": bool(SL[t]["late_in_sham"]), "sham_has_rfix": bool(SL[t]["rfix_in_sham"]),
                     "pass_SCF_ORIG": int(d["SCF-ORIG"]["passed"]) if "SCF-ORIG" in d else "",
                     "pass_SCF_NORM": int(d["SCF-NORM"]["passed"]) if "SCF-NORM" in d else "",
                     "stop_SCF_SHAM": "not run under the $2.00 cap"})
    with open(f"{RES}/sham_task_buckets{SUF}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    out["buckets_all73"] = {b: sum(r["bucket"] == b for r in rows) for b in ("Higher", "Low")}
    rows = [r for r in rows if r["task_id"] in T]
    out["buckets"] = {b: {"n": sum(r["bucket"] == b for r in rows),
                          "ORIG_pass": sum(r["pass_SCF_ORIG"] for r in rows if r["bucket"] == b),
                          "SHAM_pass": sum(r["pass_SCF_SHAM"] for r in rows if r["bucket"] == b)} for b in ("Higher", "Low")}
    json.dump(out, open(f"{RES}/sham_analysis{SUF}.json", "w"), indent=1)
    for key in comps:
        for s in ("primary30", "all"):
            p = out[key][s]
            print(key, s, json.dumps({k: p.get(k) for k in ("n_pairs", "pass_A", "pass_B", "b_Aonly", "c_Bonly",
                                                             "mcnemar_exact_p", "diff_A_minus_B")}))
    print("decision", out["decision_rule"]); print("sham_output", out["sham_output"]); print("spend", out["spend_sham_total"])


if __name__ == "__main__":
    main()
