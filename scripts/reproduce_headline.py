"""Recompute the published headline numbers from the per-run tables in results/ alone.

Needs only numpy. Uses the same exact McNemar test and paired bootstrap (10,000 resamples, seed 1) as the study's
analysis scripts (imported from stepB_analyze.py), pairs tasks the same way (last record per task and condition wins),
and checks every recomputed value against the stored analysis JSON. Nothing is written.

usage: python scripts/reproduce_headline.py
"""
import json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cupel_paths import CUPEL_ROOT
from stepB_analyze import boot_ci, mcnemar_exact

RES = os.path.join(CUPEL_ROOT, "results")
CAP = 40


def load(fn):
    by = {}
    for line in open(os.path.join(RES, fn)):
        r = json.loads(line)
        by.setdefault(r["task_id"], {})[r["cond"]] = r  # last record wins
    return by


runs = {}
for fn in ("stepB_runs.jsonl", "informed_runs.jsonl", "scaffold_runs.jsonl", "sham_runs.jsonl"):
    for t, d in load(fn).items():
        runs.setdefault(t, {}).update(d)
stepB_order = list(load("stepB_runs.jsonl"))  # stepB_analyze.py pairs in insertion order; the later arms sort by task
primary = set(json.load(open(os.path.join(RES, "scaffold_order.json")))["primary_set"])


def pairs(A, B, S=None, order=None):
    ts = order if order is not None else sorted(runs)
    return [(t, runs[t][A], runs[t][B]) for t in ts if A in runs[t] and B in runs[t] and (S is None or t in S)]


def passes(P):
    a = np.array([p[1]["passed"] for p in P], int); z = np.array([p[2]["passed"] for p in P], int)
    b = int(((a == 1) & (z == 0)).sum()); c = int(((a == 0) & (z == 1)).sum())
    return {"n_pairs": len(P), "pass_A": int(a.sum()), "pass_B": int(z.sum()), "b": b, "c": c,
            "p": round(mcnemar_exact(b, c), 4), "diff_ci": boot_ci(a - z)}


def fe(r):
    return r["first_edit_step"] or CAP + 1


def efficiency(P):
    x = np.array([fe(p[1]) for p in P], float); y = np.array([fe(p[2]) for p in P], float)
    sx = np.array([p[1]["steps"] if p[1]["passed"] else CAP for p in P], float)
    sy = np.array([p[2]["steps"] if p[2]["passed"] else CAP for p in P], float)
    cap = lambda k: sum(p[k]["stop_reason"] == "step_cap" for p in P)
    cps = lambda k: round(sum(p[k]["cost"] for p in P) / max(1, sum(p[k]["passed"] for p in P)), 4)
    return {"first_edit_diff_ci": boot_ci(x - y), "steps_fail40_diff_ci": boot_ci(sx - sy),
            "step_cap_stops": [cap(1), cap(2)], "cost_per_solved": [cps(1), cps(2)]}


checks = []


def check(label, got, want):
    ok = got == want
    checks.append(ok)
    print(f"{'OK ' if ok else 'MISMATCH'} {label}: {got}" + ("" if ok else f"  (stored: {want})"))


def compare(label, P, stored, keyA="pass_A", keyB="pass_B", keyb="b_Aonly", keyc="c_Bonly", keyd="diff_A_minus_B"):
    g = passes(P)
    check(f"{label} pairs / passes / discordant / p / diff CI",
          [g["n_pairs"], g["pass_A"], g["pass_B"], g["b"], g["c"], g["p"], g["diff_ci"]],
          [stored["n_pairs"], stored[keyA], stored[keyB], stored[keyb], stored[keyc], stored["mcnemar_exact_p"], stored[keyd]])


J = lambda f: json.load(open(os.path.join(RES, f)))
sb, inf, scf, sham = J("stepB_analysis.json"), J("informed_analysis.json"), J("scaffold_analysis.json"), J("sham_analysis_all_available.json")

print("== Step B (uninformed): ORIG vs NORM")
for nm, S, key in (("primary 30", primary, "primary"), ("all 73", None, "all_pairs")):
    compare(f"ORIG vs NORM, {nm}", pairs("ORIG", "NORM", S, stepB_order), sb[key],
            "pass_ORIG", "pass_NORM", "b_ORIGonly", "c_NORMonly", "diff_ORIG_minus_NORM")
print("== Informed (hint): INF-ORIG vs INF-NORM")
for nm, S, key in (("primary 30", primary, "primary30"), ("all 73", None, "all")):
    compare(f"INF-ORIG vs INF-NORM, {nm}", pairs("INF-ORIG", "INF-NORM", S), inf["infORIG_vs_infNORM"][key])
print("== Scaffold (forced list): SCF-ORIG vs SCF-NORM")
for nm, S, key in (("primary 30", primary, "primary30"), ("all 73", None, "all")):
    compare(f"SCF-ORIG vs SCF-NORM, {nm}", pairs("SCF-ORIG", "SCF-NORM", S), scf["scfORIG_vs_scfNORM"][key])
print("== Sham-list control: SCF-ORIG vs SCF-SHAM (all available runs, the published analysis)")
for nm, S, key in (("primary 30", primary, "primary30"), ("all 73", None, "all")):
    compare(f"SCF-ORIG vs SCF-SHAM, {nm}", pairs("SCF-ORIG", "SCF-SHAM", S), sham["scfORIG_vs_scfSHAM"][key])
compare("SCF-SHAM vs SCF-NORM, all 73", pairs("SCF-SHAM", "SCF-NORM"), sham["scfSHAM_vs_scfNORM"]["all"])
st = sham["scfORIG_vs_scfSHAM"]["all"]
eff = efficiency(pairs("SCF-ORIG", "SCF-SHAM"))
check("SCF-ORIG − SCF-SHAM first-edit step (no edit = 41), mean diff CI", eff["first_edit_diff_ci"],
      st["first_edit_step_noedit_as_41"]["mean_diff_ci"])
check("SCF-ORIG − SCF-SHAM steps (failures at 40), mean diff CI", eff["steps_fail40_diff_ci"],
      st["steps_all_fail_at_cap"]["mean_diff_ci"])
print(f"   step-cap stops SCF-ORIG / SCF-SHAM: {eff['step_cap_stops']}  (published: 11 / 20)")
print(f"   cost per solved task SCF-ORIG / SCF-SHAM: {eff['cost_per_solved']}  (published: $0.0264 / $0.0405)")
checks.append(eff["step_cap_stops"] == [11, 20] and eff["cost_per_solved"] == [0.0264, 0.0405])
print(f"\n{sum(checks)}/{len(checks)} checks match the stored analysis")
sys.exit(0 if all(checks) else 1)
