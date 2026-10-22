"""Render markdown tables for the 'Informed agent' report section from results/informed_analysis.json
(no numbers typed by hand). Output: results/informed_report_tables.md"""
import json
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1

R = CUPEL_ROOT + "/results"
A = json.load(open(f"{R}/informed_analysis.json"))
L = []
COMPS = [("infORIG_vs_infNORM", "INF-ORIG vs INF-NORM (primary 1: leak value, informed)"),
         ("infORIG_vs_ORIG", "INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day)"),
         ("infNORM_vs_NORM", "INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day)"),
         ("ORIG_vs_NORM_stepB", "Step-B ORIG vs NORM (reference, uninformed)")]

L.append("### Paired pass rates\n")
L.append("| comparison (A vs B) | set | pairs | A pass | B pass | both pass | both fail | A only | B only | exact McNemar p | A−B (paired bootstrap 95% CI) |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|")
for k, lab in COMPS:
    for s in ("primary30", "all", "all_stratum_strong", "all_stratum_random"):
        p = A[k][s]
        if not p["n_pairs"]:
            continue
        d = p["diff_A_minus_B"]
        L.append(f"| {lab} | {s} | {p['n_pairs']} | {p['pass_A']} | {p['pass_B']} | {p['both_pass']} | {p['both_fail']} | "
                 f"{p['b_Aonly']} | {p['c_Bonly']} | {p['mcnemar_exact_p']} | {d[0]:+.3f} ({d[1]:+.3f} to {d[2]:+.3f}) |")

METRICS = [("steps_both_pass", "steps (both passed)"), ("steps_all_fail_at_cap", "steps (fail = 40)"),
           ("steps_eff_both_pass", "effective steps (both passed)"),
           ("prompt_tokens", "prompt tokens / run"), ("completion_tokens", "completion tokens / run"),
           ("cached_tokens", "cached prompt tokens / run"), ("cost", "cost / run ($)"),
           ("cost_both_pass", "cost / run, both passed ($)"), ("wall_s", "wall time / run (s)"),
           ("files_opened_before_first_edit", "files opened before first edit"),
           ("first_edit_step_noedit_as_41", "first-edit step (none = 41)"),
           ("opened_late_file_before_first_edit", "late-cluster file opened before first edit (share)"),
           ("final_touches_late", "final diff touches late-cluster file (share)"),
           ("mtime_targeted_before_first_edit", "time-based command before first edit (share)")]
for k, lab in COMPS[:3]:
    for s in ("primary30", "all"):
        p = A[k][s]
        L.append(f"\n**Secondary metrics — {lab}, {s}** (A = {p['A']}, B = {p['B']}; paired A−B with bootstrap 95% CI)\n")
        L.append("| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m, ml in METRICS:
            v = p.get(m)
            if not v:
                continue
            md, mm = v["mean_diff_ci"], v["median_diff_ci"]
            g = lambda x: f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.4g}"
            L.append(f"| {ml} | {v['n']} | {g(v['median_A'])} | {g(v['median_B'])} | {g(v['mean_A'])} | {g(v['mean_B'])} | "
                     f"{g(md[0])} ({g(md[1])} to {g(md[2])}) | {g(mm[0])} ({g(mm[1])} to {g(mm[2])}) |")

L.append("\n### Per-condition summary (all pairs of each comparison)\n")
L.append("| condition | set | n | pass | total cost $ | cost per solved $ | median steps (solved) | ran time cmd | … before first edit | time cmd in reply text (attempted) | `ls -l`-type only | late file opened pre-edit | final touches late | submitted | stop reasons |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
seen = set()
for k, _ in COMPS:
    for s in ("primary30", "all"):
        p = A[k][s]
        for c in (p["A"], p["B"]):
            if (c, s) in seen or f"per_cond_{c}" not in p:
                continue
            seen.add((c, s))
            q = p[f"per_cond_{c}"]
            L.append(f"| {c} | {s} | {q['n']} | {q['pass']} | {q['total_cost']} | {q['cost_per_solved']} | {q['median_steps_solved_runs']} | "
                     f"{q['mtime_targeted']} | {q['mtime_targeted_before_first_edit']} | {q['mtime_targeted_in_reply_text_attempted']} | "
                     f"{q['mtime_visible_only']} | {q['late_opened_before_first_edit']} | {q['final_touches_late']} | {q['submitted']} | {q['stop_reasons']} |")

L.append("\n### Observational: INF-ORIG runs with vs without a time-based command before the first edit\n")
L.append("| set | INF-ORIG ran time cmd pre-edit | n tasks | INF-ORIG pass | INF-NORM pass (same tasks) | Step-B ORIG pass (same tasks) |")
L.append("|---|---|---|---|---|---|")
for key, v in A["observational_INF-ORIG_time_cmd"].items():
    s, flag = key.split(":")
    L.append(f"| {s} | {flag.split('=')[1]} | {v['n']} | {v['INF-ORIG_pass']} | {v['INF-NORM_pass_same_tasks']} | {v['ORIG_pass_same_tasks']} |")

if "leak_surfaced" in A:
    L.append("\n### Post-hoc descriptive (Amendment 2): did the first executed time-based command show a late-cluster file?\n")
    L.append("| condition | runs with an executed time cmd | output names ≥ 1 late-cluster file (anywhere) | … within first 10 output lines | shown file later opened before first edit |")
    L.append("|---|---|---|---|---|")
    for c, v in A["leak_surfaced"].items():
        L.append(f"| {c} | {v['n_runs_time_cmd']} | {v['output_shows_late']} | {v['late_in_first_10_output_lines']} | {v['late_shown_then_opened_pre_edit']} |")

if "time_cmd_kinds" in A:
    L.append("\n### Kind of executed time-based command (descriptive)\n")
    L.append("| condition | runs with any | recursive/file-level `find -newer/-mtime/-mmin` | … before first edit | only `ls -t`-type (one directory level) |")
    L.append("|---|---|---|---|---|")
    for c, v in A["time_cmd_kinds"].items():
        L.append(f"| {c} | {v['runs_any_time_cmd']} | {v['runs_find_time']} | {v['runs_find_time_before_first_edit']} | {v['runs_ls_t_only']} |")

L.append("\n### Keyword audit of INF-* commands (`results/informed_cmd_audit.json`)\n")
L.append("| condition | commands | broad keyword hits | classified targeted | `ls -l`-type only | neither | runs with a hit | git-history hunting runs |")
L.append("|---|---|---|---|---|---|---|---|")
au = A["audit_INF"]
for c, v in au["summary"].items():
    L.append(f"| {c} | {au['n_commands'][c]} | {v['broad_hits']} | {v['targeted']} | {v['visible_only']} | {v['neither']} | "
             f"{v['runs_with_broad_hit']} | {au['githunt_runs'].get(c, 0)} |")

L.append(f"\n**Spend** (`results/spend_informed.jsonl`): ${A['spend_informed_total']} over {A['spend_informed_n_calls']} calls; "
         f"by kind {A['spend_informed_by_kind']}; cache-hit share of prompt tokens {A['cache_hit_share_prompt_tokens']}.")
open(f"{R}/informed_report_tables.md", "w").write("\n".join(L) + "\n")
print("\n".join(L[:30]))
