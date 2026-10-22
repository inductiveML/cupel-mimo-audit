# Cupel: MiMo-V2.6 RL environment audit, artefacts

This repository holds the reports, pre-registrations, analysis scripts and derived result tables behind
Cupel's audit of Xiaomi's MiMo-V2.6 RL coding environments
([`XiaomiMiMo/MiMo-V2.6-RL-oss`](https://huggingface.co/datasets/XiaomiMiMo/MiMo-V2.6-RL-oss), code split,
images `docker.io/xiaomimimo/mimo-v2.6-rl-oss:*`).

**Published write-up: <https://inductive.ml/cupel/mimo>**

Cupel is the RL-environment auditing arm of [Inductive ML](https://inductive.ml).

## Findings in one paragraph

Xiaomi's fix for the git-history leak holds: 0 of 300 sampled tasks had a recoverable commit later than the task's
base (95% CI 0–1.26%). A second leak, through file modification times, is still present in 85.3% of tasks
(256 of 300): the files the reference fix changed are newer than the rest of the checkout. Against a matched
sham-list control, an agent shown the mtime ranking made its first edit about 3 steps sooner but solved no more
tasks (51 vs 51 of 73; 95% upper bound +12.3 pp). Severity: Low. The fix is to normalise timestamps when building
the images, e.g. `find <repo> -xdev -exec touch -h -d @0 {} +`.

## Contents

| Path | What it is |
|---|---|
| `PHASE1_REPORT.md` | Phase 1: static scan of 300 tasks (git-history fix verification, other leak classes, scanner recall on 115 planted leaks). |
| `MTIME_REPORT.md` | The mtime side channel: offline signal strength (Step A) and the four paired agent arms (uninformed, informed, scaffold, sham-list control), with methods, caveats and spend. |
| `results/stepB_plan.md` | Pre-registration of the uninformed paired A/B (Step B), with Amendments 1–4. |
| `results/informed_plan.md` | Pre-registration of the informed-agent arm, with Amendments 1–2. |
| `results/scaffold_plan.md` | Pre-registration of the scaffold (forced-compliance) arm, including the verbatim ranking command, with Amendment 1. |
| `results/sham_plan.md` | Pre-registration of the sham-list control, with Amendment 1 (budget) and the analyst's note on it. |
| `results/*_runs.jsonl` | One record per agent run (task, condition, pass/fail, steps, first-edit step, files opened, final-diff files, tokens, cost, stop reason, grader summary). `stepB_` = ORIG/NORM, `informed_` = INF-ORIG/INF-NORM, `scaffold_` = SCF-ORIG/SCF-NORM, `sham_` = SCF-SHAM. |
| `results/*_analysis.json` | Full outputs of the analysis scripts (all comparisons, secondary metrics, per-task tables). `sham_analysis_all_available.json` is the published (all-73) sham analysis; `sham_analysis.json` is the first-66 analysis under the original $2.00 cap. |
| `results/sham_task_buckets*.csv` | Per-task outcomes for SCF-ORIG vs SCF-SHAM with severity buckets and strata. |
| `results/stepA_metrics.json`, `stepA_per_task.jsonl`, `stepA_table.md` | Step A: offline ranking metrics (mtime vs BM25, size, random) and per-task late-cluster statistics. |
| `results/mtime_precision_ext.json` | Extended upstream anchoring (late-mtime set vs the upstream fix's file set). |
| `results/stepB_selection.json`, `stepB_primary_prebug_set.json`, `*_order.json`, `*_state.json`, `sham_capset.json` | Task selection, pre-registered order and condition coins, per-task run state, and the first-66 ($2.00 cap) task set. |
| `results/sham_lists.json` | The fixed sham lists (sha256 recorded in `sham_plan.md`). |
| `results/scaffold_offline_check.json` | Offline check of the scaffold ranking rule. |
| `results/*cmd_audit.json`, `scaffold_posthoc.json` | Keyword audits of agent commands and the post-hoc git-history-hunting counts. |
| `results/report_tables.md`, `informed_report_tables.md`, `power.json` | Rendered tables and the power analysis. |
| `scripts/reproduce_headline.py` | Recomputes the headline paired results from the included `*_runs.jsonl` files and checks them against the stored analysis JSON. |
| `scripts/stepB_analyze.py`, `informed_analyze.py`, `scaffold_analyze.py`, `scaffold_posthoc.py`, `sham_analyze.py`, `audit_mtime_cmds.py` | The analysis scripts that produced the `*_analysis.json` files. |
| `scripts/stepA.py`, `tracked_proxy.py`, `sham_build.py` | Step A offline ranking and the sham-list construction. |
| `scripts/report_tables.py`, `informed_report_tables.py`, `power.py` | Render tables / compute power from the analysis JSON. |
| `scripts/analysis_common.py`, `cupel_paths.py` | The command classifier and helpers the analysis scripts import (verbatim from the study's orchestrator), and the data-path settings. |

The analysis scripts are the study's own code. For publication the only changes are that the data paths are
configurable (`CUPEL_ROOT`, `CUPEL_PHASE1`, see `scripts/cupel_paths.py`) and the classifier helpers are imported
from `scripts/analysis_common.py` instead of the unpublished orchestrator. Analysis logic is unchanged.

## Re-running the analysis

Python 3.10+ with `numpy`.

```sh
pip install numpy
python scripts/reproduce_headline.py         # recomputes the headline results from results/*_runs.jsonl
python scripts/report_tables.py              # regenerates results/report_tables.md from the analysis JSON
python scripts/informed_report_tables.py     # regenerates results/informed_report_tables.md
python scripts/power.py                      # regenerates the power analysis in results/power.json
```

`reproduce_headline.py` recomputes, for every arm, the pass counts, discordant pairs, exact McNemar p and paired
bootstrap 95% CI (10,000 resamples, seed 1) on the pre-registered primary 30 and on all 73 pairs, plus the
sham-arm efficiency numbers (first-edit step, steps with failures at 40, step-cap stops, cost per solved task),
and checks each one against the stored analysis. It prints `12/12 checks match` on this repository. The
report-table scripts reproduce their markdown byte for byte. `power.py` regenerates `power.json` except for two
values that were added to it separately (primary-30 power when all, or 90%, of discordant pairs favour ORIG;
the first is the 0.73 quoted in `MTIME_REPORT.md` §3.2).

The scripts overwrite their outputs in `results/`; use `git diff` to compare.

A full re-analysis from scratch (`*_analyze.py`, `audit_mtime_cmds.py`, `stepA.py`, `sham_build.py`) also needs
inputs that are not in this repository: the per-run agent trajectories (`runs/<task>/<cond>/trajectory.jsonl`,
which contain complete container output) and the phase-1 scan outputs (`tier_a.jsonl`, per-task file manifests),
which come from the private scanner. Point `CUPEL_ROOT` / `CUPEL_PHASE1` at them if you have them.

## Not included

- The Cupel scanner (static image analysis, leak detectors, planting harness) and its raw outputs. The audit
  tooling is private.
- The agent loop, container orchestration and model client used for the agent runs, the spend logs, and the raw
  trajectories.
- Process logs and operator notes. Process ids and host details were removed from the reports and plans;
  no number was changed.

## Contact

Aditya Veer Parmar, Cupel / Inductive ML: aditya@inductive.ml
