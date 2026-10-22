"""Render markdown tables for MTIME_REPORT.md from results/*.json (no numbers typed by hand)."""
import json
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1

R = CUPEL_ROOT + "/results"
A = json.load(open(f"{R}/stepA_metrics.json"))
B = json.load(open(f"{R}/stepB_analysis.json"))
L = []
f = lambda v: f"{v[0]:.2f} ({v[1]:.2f}–{v[2]:.2f})"

L.append("### Step A: ranking metrics (mean over tasks, bootstrap 95% CI)\n")
for grp, title in (("flagged_proxy_ok", "Flagged tasks, tracked proxy OK (main)"),
                   ("flagged_all", "All flagged tasks (sensitivity: includes tasks where the proxy disagrees with phase 1)"),
                   ("unflagged_proxy_ok", "Unflagged tasks (contrast)")):
    for ref in ("R_fix", "R_test", "R_src_proxy", "R_agent"):
        rows = [(rn, A[grp][rn][ref]) for rn in A[grp] if ref in A[grp][rn]]
        if not rows:
            continue
        L.append(f"\n**{title} — {ref}** (n = {rows[0][1]['n_tasks']} tasks)\n")
        L.append("| ranker | hit@1 | hit@3 | hit@5 | hit@10 | P@1 | P@3 | P@5 | P@10 | R@1 | R@3 | R@5 | R@10 |")
        L.append("|---|" + "---|" * 12)
        for rn, d in rows:
            L.append(f"| {rn} | " + " | ".join(f(d[m]) if m in d else "–" for m in
                     [f"{x}@{k}" for x in ("hit", "p", "r") for k in (1, 3, 5, 10)]) + " |")

L.append("\n### Step B: paired pass rates\n")
L.append("| set | pairs | ORIG pass | NORM pass | both pass | both fail | b (ORIG only) | c (NORM only) | exact McNemar p | ORIG−NORM (paired bootstrap 95% CI) |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for k in ("primary", "prereg_as_run", "all_pairs", "primary_stratum_strong", "primary_stratum_random",
          "all_stratum_strong", "all_stratum_random"):
    p = B[k]
    if not p["n_pairs"]:
        continue
    d = p["diff_ORIG_minus_NORM"]
    L.append(f"| {p['label']} | {p['n_pairs']} | {p['pass_ORIG']} | {p['pass_NORM']} | {p['both_pass']} | {p['both_fail']} | "
             f"{p['b_ORIGonly']} | {p['c_NORMonly']} | {p['mcnemar_exact_p']} | {d[0]:+.3f} ({d[1]:+.3f} to {d[2]:+.3f}) |")

for k in ("primary", "all_pairs"):
    p = B[k]
    L.append(f"\n**Secondary metrics — {p['label']}** (medians; paired difference ORIG−NORM: mean and median with bootstrap 95% CI)\n")
    L.append("| metric | n | median ORIG | median NORM | mean ORIG | mean NORM | mean diff (CI) | median diff (CI) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for m in ("steps_both_pass", "steps_eff_both_pass", "steps_all_fail_at_cap", "steps_eff_all_fail_at_cap",
              "prompt_tokens", "completion_tokens", "cost", "wall_s", "files_opened_before_first_edit",
              "first_edit_step_noedit_as_41", "opened_late_file_before_first_edit", "final_touches_late"):
        x = p.get(m)
        if not x:
            continue
        md = x["mean_diff_ci"]; me = x["median_diff_ci"]
        fmt = (lambda v: f"{v:.4f}") if m == "cost" else (lambda v: f"{v:.2f}" if abs(v) < 1000 else f"{v:,.0f}")
        L.append(f"| {m} | {x['n']} | {fmt(x['median_ORIG'])} | {fmt(x['median_NORM'])} | {fmt(x['mean_ORIG'])} | {fmt(x['mean_NORM'])} | {fmt(md[0])} ({fmt(md[1])} to {fmt(md[2])}) | "
                 f"{fmt(me[0])} ({fmt(me[1])} to {fmt(me[2])}) |")
    L.append("\n| condition | runs | mtime_targeted (any) | mtime_targeted before first edit | mtime_visible only | submitted | stop reasons |")
    L.append("|---|---|---|---|---|---|---|")
    for c in ("ORIG", "NORM"):
        r = p[f"rate_{c}"]
        L.append(f"| {c} | {r['n']} | {r['mtime_targeted']} | {r['mtime_targeted_before_first_edit']} | {r['mtime_visible']} | "
                 f"{r['submitted']} | {r['stop_reasons']} |")

L.append("\n**Observational (all pairs): ORIG runs with vs without an mtime-targeted command**\n")
L.append("| group | pairs | ORIG pass | NORM pass (same tasks) |")
L.append("|---|---|---|---|")
for g, v in B["observational_ORIG_mtime_targeted"].items():
    L.append(f"| {g} | {v['n']} | {v['ORIG_pass']} | {v['NORM_pass_same_tasks']} |")

L.append("\n**Per pair**\n")
L.append("| task | stratum | primary | ORIG | NORM | steps O/N | cost O/N | mtime-targeted O/N | final diff touches late file O/N |")
L.append("|---|---|---|---|---|---|---|---|---|")
prim = set(B["primary_set"])
for x in B["per_pair"]:
    L.append(f"| {x['task_id'][-6:]} | {x['stratum']} | {'yes' if x['task_id'] in prim else 'no'} | {'pass' if x['ORIG'] else 'fail'} | "
             f"{'pass' if x['NORM'] else 'fail'} | {x['steps'][0]}/{x['steps'][1]} | {x['cost'][0]:.4f}/{x['cost'][1]:.4f} | "
             f"{int(x['mt_targeted'][0])}/{int(x['mt_targeted'][1])} | {int(x['late_touched'][0])}/{int(x['late_touched'][1])} |")
open(f"{R}/report_tables.md", "w").write("\n".join(L) + "\n")
print("wrote", f"{R}/report_tables.md", len(L), "lines")
