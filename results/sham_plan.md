# Cupel sham-list control (SCF-SHAM): pre-registration

Written 2026-10-21 ~07:04Z, **before any agent call of this experiment**. The sham lists were built offline (no Docker,
no agent) by `scripts/sham_build.py` → `results/sham_lists.json`
(sha256 of the file `526a2ef6013818c6ca5d850fea7df88e1a28d59b88d47509fe8e36f6cd2ec772`; sha256 of the per-task
content `70ce43fd9172d36c8fed76ccb67186d5a157216f0f3a6fb10559b6ce9363fcae`). They are fixed now and will not change.

## Question
Section 8 (scaffold arm): SCF-ORIG 51/73 vs SCF-NORM 42/73 (+12.3 pp, p = 0.12; primary 30: 22 vs 13, p = 0.035).
SCF-ORIG matched Step-B ORIG (50) and INF-ORIG (50); the gap came from SCF-NORM falling below Step-B NORM (47).
SCF-NORM showed the header "ranked by last-modified time" followed by an **empty** list, which may itself hurt
(SCF-NORM agents hunted git history most often, 29/73). That is a control confound.
**SCF-SHAM** replaces the empty list with a non-empty but uninformative list of the same length. Question: is the
ORIG-list benefit still there when the control also sees a plausible-looking list?

## Design: one new condition, SCF-SHAM
Identical to SCF (`scripts/stepB_scaffold.py`, `agent_scaffold.py`) in everything except the content of the list:
same 73 tasks in the same order (`results/scaffold_order.json`, primary 30 first), images
`xiaomimimo/mimo-v2.6-rl-oss:<task>`, container flags (`--network none --memory 2g --cpus 1.5`, `sleep infinity`,
names `mtime_*`), grader (`git apply` test_patch from `/tmp`, `test_command`, pass iff applied and exit 0), reuse of
Step-B validation (no re-validation), Step-B SYSTEM and TASK prompts, no hint line, model
`deepseek/deepseek-v4.1-flash-1017`, provider pinned `deepseek` with `allow_fallbacks: false`, temperature 0, seed 7,
max_tokens 8192, step cap 40, per-run cost cap $0.15, command timeout 120 s, truncation 6,000 chars, bash-then-DSML
parsing, bare `echo SUBMIT` stop, host-side first-edit detection, and the **same header text**
(`Files in the repository ranked by last-modified time (most recent first):`) and block shape
(`scaffold_cmd.block`: header, `<output>`, list, `</output>`), appended after one blank line to the first user message.

### Timestamps: NORM
Step-B NORM prep (`find <cwd> -xdev -exec touch -h -d @0 {} +`) and verification (`find <cwd> -xdev -newermt @1 | wc -l`
must be 0, else the run aborts), unchanged (`stepB.prep`).

### Harness steps after prep (not agent steps, not classified)
1. The unchanged ANCHOR_EXCL scaffold command (`scaffold_cmd.SCAFFOLD_CMD`) is run and its output recorded
   (`scaffold_real_output`, expected empty as in SCF-NORM). It is **not** shown.
2. A harness existence check: `test -f` for each sham path in the container (recorded as `sham_missing`). The list is
   shown as pre-fixed regardless; missing files are reported.
3. The sham block `scaffold_cmd.block(truncate(sham_output))` is appended to the first user message.

### Sham construction (fixed; `scripts/sham_build.py`)
- **k** = the number of lines of that task's live SCF-ORIG list (`scaffold_n_lines` in `results/scaffold_runs.jsonl`;
  the existing SCF-ORIG run, not re-run).
- **Candidate set** = the set the ORIG rule draws from: regular files under cwd, minus `.git` and the Step-A artefact
  exclusions (`tracked_proxy.load(task, cwd)` on the phase-1 manifest — the same set `scaffold_offline_check.py` used
  to reproduce the live ORIG lists).
- **Pool** = sorted(candidates − the task's SCF-ORIG list). If the pool had fewer than k files, the ORIG-list files
  would be added back; this never happens (minimum pool size 10 ≥ k in every task; `tasks_orig_added_back` = 0).
- **Draw**: `random.Random(20261022000000 + NNNNNN).sample(pool, k)` for task `format-code-task-NNNNNN`
  (seed per task recorded in `sham_lists.json`), uniform without replacement, kept in sampled order.
- **Format**: line i = `<timestamp string of SCF-ORIG line i>  <sham path i>`. The ORIG timestamps are reused verbatim
  (same column format `YYYY-MM-DD HH:MM:SS  path`, same plausible values, newest first). Only the paths differ.
  (Under NORM the real files have epoch mtimes; an agent that runs `ls -l` on a sham file would see 1970. Same for
  SCF-NORM. Recorded as a caveat; the harness does not change real timestamps, since that would break NORM.)
- **Per task recorded**: k, pool size, seed, the sham list, and which late-cluster files and upstream-fix (`R_fix`)
  files landed in the sham list.
- **Summary of the fixed lists** (`sham_lists.json` `summary`): 73 tasks, 531 lines total; k histogram
  1:5, 2:16, 3:9, 4:16, 5:5, 6:1, 7:4, 8:3, 10:2, 11:1, 14:1, 19:1, 21:1, 26:1, 29:1, 30:6.
  **Late-cluster files in a sham list: 0 tasks.** **R_fix files in a sham list: 1 task** (#4, 001692:
  `tests/kerastuner/engine/tuner_workflows_test.py`, an upstream-fix test file not in the ORIG list; of 17 anchored
  tasks). ORIG files added back: 0 tasks.

## Run protocol
- Order: the 73 tasks in `scaffold_order.json` order; one SCF-SHAM run per task; fresh container per run; one
  container at a time; each image removed by exact tag after the task's run.
- **Container check before the smoke call** (task 1, 002739, no agent): NORM prep, the real scaffold command (expect
  empty), sham existence check (expect 0 missing), block text. → `results/sham_container_check.json`.
- **Smoke**: one tiny call ("Reply with OK", max_tokens 16), run_id `smoke`, via `scripts/orclient_sham.py`.
- **Pilot**: task 1 (002739) full protocol. If the protocol is unchanged, the pilot is part of the main data. If anything
  changes, the pilot is moved to `results/sham_pilot_v1/` and `runs/<task>/SCF-SHAM_pilot_v1/`, excluded, the change is
  recorded as a dated amendment, and 002739 re-run.
- Main loop in the background, resumable from `results/sham_state.json`.

## Stopping rules and budget
- Spend: summed per-call `usage.cost` in `results/spend_sham.jsonl` only (no other spend file read or appended to;
  key-level totals never used). **Cap $2.00.** A new run is launched only if spend < **$1.85**; inside a run each step
  checks spend and stops at ≥ **$2.00** (`global_spend_hard_cap`).
- Disk: free disk on `/` ≥ **20 GB** before every pull, container start and agent step, else all Docker work stops
  (`dock.pull` additionally refuses below 25 GB).
- Wall time: no new run after 2026-10-22T12:00Z.
- If fewer than 73 runs complete, the paired analyses use the complete pairs and the shortfall is stated.

## Analysis (`scripts/sham_analyze.py` → `results/sham_analysis.json`)
Statistics as in §8: exact two-sided McNemar on discordant pairs, paired bootstrap 95% CI over tasks (10,000 resamples,
seed 1; `stepB_analyze.boot_ci`, `informed_analyze.summarize` imported unchanged).

**Primary:** **SCF-ORIG vs SCF-SHAM**, paired by task, on the pre-registered primary 30 and on all 73. SCF-ORIG = the
existing runs in `results/scaffold_runs.jsonl` (not re-run). SCF-ORIG ran a day earlier (2026-10-20/21); temperature 0
is not deterministic at this provider, so this is a cross-day pairing (stated in the report).

**Secondary:** SCF-SHAM vs SCF-NORM and SCF-SHAM vs Step-B NORM (does any non-empty list remove the empty-list
penalty?), same statistics, primary 30 and all 73. Descriptive: SCF-SHAM vs SCF-ORIG/INF-ORIG/Step-B ORIG pass counts.

**Efficiency, per condition and paired (SCF-ORIG − SCF-SHAM; also SCF-SHAM − SCF-NORM):** first-edit step (no edit = 41);
steps to solve (both-pass pairs; all pairs with failures counted at 40); step-cap stops (count per condition);
cost per run and cost per solved task; files opened before the first edit; git-history commands (runs with ≥ 1
`GITHUNT` match, `informed_analyze.GITHUNT`, heredocs stripped; paired indicator difference). Also: first edited file /
final diff in the task's SCF-ORIG list (and, for SCF-SHAM, in its own sham list: did the sham mislead?).

**Heterogeneity (exploratory, labelled as such):** pass difference and first-edit-step difference SCF-ORIG − SCF-SHAM
- by stratum (strong / random);
- by the "short source-containing late cluster" group: 1–10 late files with ≥ 1 late source file (`stepA_per_task.jsonl`
  `n_late`, `n_late_source`) vs the rest. Note fixed now: 70 of the 73 tasks fall into this group (the Step-B pool was
  already restricted to small clusters), so this split is expected to be uninformative and the strata split is the
  informative one;
- by late-cluster size bin (1–2, 3–4, 5–10, > 10 files).
The per-task gradient = the per-task ORIG−SHAM pass and first-edit differences by these groups.
(Disclosure: §8 already showed the SCF-ORIG − SCF-NORM difference concentrated in the strong stratum; these splits are
therefore not blind to that earlier result.)

**Decision rule (pre-registered verbatim):** if SCF-ORIG minus SCF-SHAM on all 73 is >= +15 pp, correctness severity
becomes Medium with that number; otherwise correctness stays Low and the reported finding is the efficiency gain
(with its numbers) plus the per-task gradient. State the CI upper bound either way.
(Operationalisation: the paired point estimate of the pass-rate difference over complete pairs; ≥ 15.0 pp → Medium.)

**Severity buckets** (`results/sham_task_buckets.csv`): Higher = 1–10 late files with ≥ 1 late source file; Low = rest.
Per task with the inputs (n_late, n_late_source, stratum) and the observed per-task outcomes.

## Implementation (new files only)
`scripts/sham_build.py`, `scripts/orclient_sham.py` (copy of `orclient_scaffold.py` → `results/spend_sham.jsonl`),
`scripts/agent_sham.py` (imports `agent_scaffold.run_agent` logic with the sham spend thresholds/client),
`scripts/stepB_sham.py` (orchestrator), `scripts/sham_analyze.py`, `scripts/status_tick_sham.py`.
Outputs: `results/sham_*`, `results/spend_sham.jsonl`, process-id files, `runs/<task>/SCF-SHAM/`.
No existing file in `results/` or existing `runs/<task>/*` directory is modified.

## Amendments
(none yet)

## Amendment 1 (budget only), 2026-10-21 ~10:35Z, by the study lead
The study lead raised the cap from $2.00 to $3.20 (stop new runs at $3.05, hard stop $3.20) so all 73 tasks finish. Reason: the cost per run (~$0.036) is higher than planned. The decision was made from spend and task counts only; no SCF-SHAM vs SCF-ORIG comparison was looked at. Design, tasks, order, and analysis are unchanged. The running loop had loaded the old constants, so when it stopped at $1.85 it was relaunched (resumable) with the new caps. **Do not start the analysis until all 73 tasks are done or the $3.05 stop is hit by the relaunched loop.**

## Note by the analyst (2026-10-21T11:10Z) on the preceding "Amendment 1"
The analyst did not write the "Amendment 1 (budget only)" above; it was appended from outside the analysis session at 10:33Z, together with the corresponding cap change in the agent loop and the relaunch. The change could not be verified at that time as coming from the study lead, so it was **not adopted** for the analysis at first: the pre-registered stopping rule ($1.85 new-run stop and $2.00 hard stop, `results/spend_sham.jsonl`) defined the analysed set, the runs completed by the first loop (snapshot `results/sham_capset.json`), and later runs were to be reported only as a separately labelled sensitivity check. The design and the analysis are otherwise unchanged.

*Publication note (2026-10-22):* the study lead subsequently confirmed Amendment 1, so the all-73 analysis (`sham_analyze.py --all-available`) is primary in `MTIME_REPORT.md` §9; the first-66 analysis is reported alongside. Process ids and operator tooling details were removed from this file for publication; nothing else in the plan was changed.
