# Scaffold-arm pre-registration (written 2026-10-20 ~20:10Z, before any agent call of this experiment)

## Question
Section 7 (informed agent) found INF-ORIG 50/73 vs INF-NORM 45/73, but only 27/73 INF-ORIG runs ran a time-based
command before the first edit, mostly a top-level `ls -lt`. That measured the cheap agent's *compliance* with a hint,
not the value of the leak. Here compliance is removed: **the harness itself** runs a fixed mtime-ranking command
inside the container before the first model call and shows its output to the agent. Question: **does the mtime leak
raise the solve rate when the agent is guaranteed to see the ranked late cluster?** (forced-compliance upper bound for
this model and scaffold).

## The only change versus the uninformed Step-B agent
- No hint line (system prompt = Step-B `scripts/agent.py` SYSTEM, unchanged; task prompt = Step-B TASK, unchanged).
- After the condition's timestamp prep (and its verification), the harness runs `scaffold_cmd.SCAFFOLD_CMD` once via
  `dock.ex(cname, cmd, cwd, timeout=120)` (= `docker exec -w <cwd> … timeout -s KILL 120 bash -lc <cmd>`, stdout+stderr
  merged, exactly how agent commands run), then appends to the end of the first user message, after one blank line:

      Files in the repository ranked by last-modified time (most recent first):
      <output>
      {literal command output, nothing substituted; passed through the same truncate() as agent observations}</output>

  The command output is saved to `runs/<task>/SCF-*/scaffold_output.txt` with its return code; the full first user
  message is in the saved trajectory metadata (`scaffold.json`). This harness command is not an agent step, does not
  count toward the 40-step cap, and is not included in the classified agent commands.
- Everything else is identical to the informed/Step-B runs: model `deepseek/deepseek-v4.1-flash-1017`, provider pinned
  `deepseek` with `allow_fallbacks: false`, temperature 0, seed 7, max_tokens 8192, step cap 40, per-run cost cap $0.15,
  CMD timeout 120 s, output truncation 6,000 chars (head 3,000 + tail 3,000), bash-block-then-DSML parsing (Step-B
  Amendment 1), bare `echo SUBMIT` stop rule, host-side first-edit detection, images `xiaomimimo/mimo-v2.6-rl-oss:<task>`,
  container flags `--network none --memory 2g --cpus 1.5`, entrypoint `sleep infinity`, names `mtime_*`, grader
  (`git apply` test_patch from `/tmp`, run `test_command`, pass iff the patch applies and exit 0). Step-B validation
  results are reused (no re-validation).

## The fixed command (rule ANCHOR_EXCL) — `scripts/scaffold_cmd.py`
- Candidates: regular files under cwd, pruning `.git` and the Step-A tracked-proxy artefact directories
  (`node_modules`, `.venv`, `venv`, `__pycache__`, `site-packages`, `.tox`, `.nox`, `.cache`, `.pytest_cache`,
  `.mypy_cache`, `.ruff_cache`, `.hypothesis`, `.eggs`, `.gradle`, `.next`, `.nuxt`, `.parcel-cache`, `.turbo`, `.yarn`,
  `.pnpm-store`, `.bundle`, `.m2`, `.cargo`, `.rustup`, `*.egg-info`, `*.dist-info`) and files `*.pyc *.pyo *.o *.so *.a
  *.class *.obj` — i.e. exactly the candidate set Step A ranked (`scripts/tracked_proxy.py`).
- Anchor: the most common whole-second mtime among the candidates (ties → earliest), i.e. the bulk checkout cluster.
  Listed: candidates whose whole-second mtime is **strictly greater** than the anchor (the `find -newer <anchor>` idea,
  done with an awk filter so that bulk files with a later sub-second part in the anchor second are not listed),
  sorted newest first (ties by path, `LC_ALL=C`), **at most 30 lines**, each `YYYY-MM-DD HH:MM:SS  <path>`.
- Verbatim command:

```
find . -type d \( -name '.bundle' -o -name '.cache' -o -name '.cargo' -o -name '.eggs' -o -name '.git' -o -name '.gradle' -o -name '.hypothesis' -o -name '.m2' -o -name '.mypy_cache' -o -name '.next' -o -name '.nox' -o -name '.nuxt' -o -name '.parcel-cache' -o -name '.pnpm-store' -o -name '.pytest_cache' -o -name '.ruff_cache' -o -name '.rustup' -o -name '.tox' -o -name '.turbo' -o -name '.venv' -o -name '.yarn' -o -name '__pycache__' -o -name 'node_modules' -o -name 'site-packages' -o -name 'venv' -o -name '*.egg-info' -o -name '*.dist-info' \) -prune -o -type f ! \( -name '*.pyc' -o -name '*.pyo' -o -name '*.o' -o -name '*.so' -o -name '*.a' -o -name '*.class' -o -name '*.obj' \) -printf '%T@\t%TY-%Tm-%Td %TH:%TM:%TS\t%P\n' 2>/dev/null | awk -F'\t' '{s=int($1); c[s]++; L[NR]=$0; S[NR]=s} END {m=""; for (k in c) if (m=="" || c[k]>c[m] || (c[k]==c[m] && k+0<m+0)) m=k; for (i=1;i<=NR;i++) if (S[i]>m+0) print L[i]}' | LC_ALL=C sort -t"$(printf '\t')" -k1,1nr -k3,3 | head -n 30 | awk -F'\t' '{sub(/\.[0-9]+$/, "", $2); print $2 "  " $3}'
```

### Why this rule (offline check, `scripts/scaffold_offline_check.py` → `results/scaffold_offline_check.json`)
Computed on the phase-1 manifests of the 73 tasks (whole-second mtimes; ties scored analytically under random
tie-breaking as in Step A). Reference "late" = phase-1 late cluster; "R_fix" = anchored upstream-fix files (17 of the
73 tasks are anchored).

| rule | candidates | late hit@1 (73) | late hit@3 | R_fix hit@1 (17) | R_fix hit@3 |
|---|---|---|---|---|---|
| TOP30_ALL (spec-literal: all files except .git, top 30) | all | 0.904 | 0.918 | 0.941 | 1.00 |
| ANCHOR_ALL (same, newer than bulk anchor) | all | 0.904 | 0.918 | 0.941 | 1.00 |
| TOP30_EXCL | Step-A set | 0.986 | 1.00 | 0.941 | 1.00 |
| **ANCHOR_EXCL (chosen)** | Step-A set | **0.986** | **1.00** | **0.941** | **1.00** |

- Step A (tracked proxy, mtime ranker) on the same 17 anchored tasks: R_fix hit@1 0.941; Step A overall (75 tasks)
  0.92. **The chosen rule surfaces an upstream-fix file at rank 1 at the Step-A rate** (check recorded).
- Primary 30: ANCHOR_EXCL late hit@1 1.00; R_fix hit@1 0.929 (7 anchored).
- Without the artefact exclusions, 6/73 tasks (1 primary) have `node_modules`/`.venv` files installed *after* the late
  cluster that push it out of the top 30 entirely; that is why the Step-A exclusions are part of the rule (decision:
  the spec says "pick the rule from Step A's offline method so it reproduces the offline signal").
- The anchor (mode second of the candidates) equals the phase-1 `bulk_max_mtime` in 69/73 tasks (the other 4 are one
  second earlier; then some bulk files of the following second appear below the late cluster). The anchored list is
  ≤ 30 lines in 67/73 tasks, never empty under ORIG offline; the late cluster makes up on average 87% of the shown lines.
  Remaining lines are typically build outputs or generated files newer than the checkout.
- One task (#44, 000377) has a non-late tracked file (`wordcloud/_version.py`) newer than the late file (rank 2).
- Rank-1 is identical for the anchored and top-30 rules; the anchor only removes the bulk tail (and makes NORM empty).

### What NORM shows
Under SCF-NORM every file under cwd has mtime 0 (verified as in NORM). All candidates then share the anchor second 0, so
**no file is strictly newer: the output is empty**, and the agent sees the header followed by an empty `<output>`
block. This is shown literally; nothing is substituted. (Recorded per run: `scaffold_n_lines`.)

### In-container check before any agent call
Before the smoke call, the command is run once in a fresh ORIG and a fresh NORM container of task 1 (002739) and the
output is compared with the offline expectation (ORIG: the two late files first; NORM: empty). Recorded in
`results/scaffold_container_check.json`. If the command fails there, it is fixed before any agent call and this plan
is amended.

## Conditions (fresh container per run, one container at a time)
- **SCF-ORIG**: Step-B ORIG prep (`find <cwd> -xdev -exec true {} +`, no-op), `find <cwd> -xdev -newermt @1 | wc -l`
  recorded, then the scaffold command, then the agent.
- **SCF-NORM**: Step-B NORM prep (`find <cwd> -xdev -exec touch -h -d @0 {} +`), verification must return 0 newer
  entries or the run aborts, then the identical scaffold command and header, then the agent.

## Tasks and order (`scripts/scaffold_order.py` → `results/scaffold_order.json`)
Exactly the 73 tasks and order of `results/informed_order.json` (Step-B processing order, primary 30 first).
Condition order: a new seeded coin, **seed 20261021** (`random.Random(20261021)`, one draw per task in order; < 0.5 →
SCF-ORIG first). 46/73 tasks start with SCF-ORIG.

1 002739 P NORM · 2 002808 P ORIG · 3 000877 P NORM · 4 001692 P ORIG · 5 000498 P ORIG · 6 001285 P ORIG ·
7 002661 P NORM · 8 002197 P ORIG · 9 002935 P ORIG · 10 001883 P NORM · 11 002797 P ORIG · 12 000459 P NORM ·
13 000162 P NORM · 14 001495 P ORIG · 15 000520 P ORIG · 16 002199 P ORIG · 17 000414 P ORIG · 18 001566 P NORM ·
19 002098 P ORIG · 20 001743 P ORIG · 21 001197 P ORIG · 22 003043 P NORM · 23 000230 P NORM · 24 001424 P ORIG ·
25 002820 P ORIG · 26 001547 P NORM · 27 001872 P ORIG · 28 000409 P NORM · 29 002768 P ORIG · 30 000613 P NORM ·
31 002649 E ORIG · 32 001420 E NORM · 33 002256 E ORIG · 34 002201 E ORIG · 35 002673 E ORIG · 36 001642 E NORM ·
37 001486 E ORIG · 38 002285 E ORIG · 39 002220 E ORIG · 40 000691 E ORIG · 41 001685 E NORM · 42 002860 E ORIG ·
43 001804 E ORIG · 44 000377 E ORIG · 45 002051 E ORIG · 46 002659 E NORM · 47 000501 E ORIG · 48 001699 E NORM ·
49 000510 E NORM · 50 000290 E ORIG · 51 001686 E ORIG · 52 002109 E ORIG · 53 002598 E ORIG · 54 000342 E NORM ·
55 001905 E NORM · 56 002919 E ORIG · 57 001409 E ORIG · 58 000531 E NORM · 59 002599 E NORM · 60 002443 E ORIG ·
61 002974 E ORIG · 62 002933 E ORIG · 63 002322 E NORM · 64 001214 E ORIG · 65 001568 E NORM · 66 000670 E ORIG ·
67 002461 E NORM · 68 003017 E ORIG · 69 000828 E ORIG · 70 002833 E ORIG · 71 002798 E ORIG · 72 002335 E NORM ·
73 001935 E NORM

## Implementation (new files only)
`scripts/scaffold_cmd.py` (command + header), `scripts/orclient_scaffold.py` (copy of `orclient_informed.py` writing to
`results/spend_scaffold.jsonl`), `scripts/agent_scaffold.py` (copy of the informed loop: Step-B SYSTEM, no hint, takes
the scaffold block and appends it to the first user message; loop logic unchanged), `scripts/stepB_scaffold.py`
(orchestrator, imports unchanged `prep`, `grade`, `classify`, `files_opened`, `load_tasks`, `late_files` from
`scripts/stepB.py`), `scripts/scaffold_analyze.py`, `scripts/scaffold_order.py`, `scripts/status_tick_scaffold.py`.
Outputs: `results/scaffold_runs.jsonl`, `scaffold_state.json`, `scaffold_log.txt`, `scaffold_analysis.json`,
`scaffold_cmd_audit.json`, `spend_scaffold.jsonl`, `pid_scaffold_*.txt`; `runs/<task>/SCF-ORIG/`, `runs/<task>/SCF-NORM/`.
No existing file in `results/` or any existing `runs/<task>/*` directory is modified.

## Smoke test and pilot
1. One tiny call ("Reply with OK", max_tokens 16) through `orclient_scaffold.chat`, run_id `smoke`.
2. Pilot pair = task 1 (002739), both conditions, full protocol. If the protocol is unchanged after the pilot, the pilot
   pair is part of the main data. If anything changes, the pilot is moved to `results/scaffold_pilot_v1/` (and the run
   dirs to `runs/002739/SCF-*_pilot_v1`), excluded, the change recorded as a dated amendment, and 002739 re-run.

## Analysis (`scripts/scaffold_analyze.py` → `results/scaffold_analysis.json`)
Statistics exactly as `stepB_analyze.py` / `informed_analyze.py`: exact two-sided McNemar on discordant pairs; paired
bootstrap 95% CI over tasks (10,000 resamples, seed 1) for the pass-rate difference and secondary metrics.

**Primary:** **SCF-ORIG vs SCF-NORM**, paired by task, on the pre-registered primary 30 and on all 73, separately.

**Secondary** (same statistics, primary 30 and all 73): SCF-ORIG vs INF-ORIG; SCF-ORIG vs Step-B ORIG; SCF-NORM vs
Step-B NORM; (descriptive) SCF-NORM vs INF-NORM. Cross-day comparisons are labelled as such (temperature 0 is not
deterministic at this provider: 15/73 Step-B pairs discordant without mechanism).

**Secondary metrics** per condition and paired: steps to solve (both-pass pairs; all pairs with failures at 40), effective
steps, prompt/completion/cached tokens, cost per run and cost per solved task; first-edit step (no edit = 41); files
opened before the first edit; late-cluster file opened before the first edit / touched by the final diff; **first
edited file(s)** (the `git_state_changed` files at the first-edit step) **includes a file from the scaffold list**, and
**final diff includes a file from the scaffold list** — for SCF-ORIG against its own list; for SCF-NORM (whose list is
empty) against the same task's SCF-ORIG list (labelled "would-have-been list"); the same two metrics for the Step-B /
INF runs against the task's SCF-ORIG list, descriptively. Also: live rank-1 of the SCF-ORIG output is a late-cluster
file (expected ≈ 0.986 from the offline check), number of lines shown per condition, and time-based commands run by
the agent itself (unchanged `classify` regexes + keyword audit → `results/scaffold_cmd_audit.json`).

**Decision rule (pre-registered verbatim):** if SCF-ORIG minus SCF-NORM on all 73 is >= +15 pp, the recommended
severity becomes Medium with that number; otherwise Low stands without the "cheap model's habits" caveat (state the
CI upper bound). Report honestly either way.
(Operationalisation: "SCF-ORIG minus SCF-NORM" = the paired point estimate of the pass-rate difference over the
complete pairs of the 73; if fewer than 73 pairs complete, the rule is applied to the complete pairs and the shortfall
is stated.)

## Stopping rules and budget
- Spend: summed per-call `usage.cost` in `results/spend_scaffold.jsonl` only (other spend files are not counted or
  appended to; key-level totals never used). **Cap $4.00.** A new task is started only if spend < **$3.55**; the
  second run of a pair only if spend < **$3.70**; inside a run, every step checks spend and stops at ≥ **$4.00**
  (`global_spend_hard_cap`). Incomplete pairs are excluded from paired analyses and reported.
- Disk: before every pull, container start and agent step, free disk on `/` must be ≥ **20 GB**, else all Docker work
  stops (`dock.pull` additionally refuses below 25 GB).
- Wall time: no new task after 2026-10-22T06:00Z.
- One container at a time; each task image removed by exact tag after its task finishes.
- Resumable from `results/scaffold_state.json` (finished conditions are not re-run).

## Amendments

### Amendment 1 (2026-10-21T04:57Z, after all 146 runs; descriptive only, no effect on any pre-registered outcome)
- Pilot: the pilot pair (002739) ran under the protocol unchanged, so it is included as pre-registered (no exclusion).
- Interim look (disclosed): at 2026-10-20T23:25Z the analysis script was run on 24 complete pairs as a pipeline test.
  Nothing was changed after it: protocol, stopping rules and analysis are as pre-registered, and the run went to the end of the schedule.
- Added after seeing the final data, because SCF-NORM passed less often than Step-B NORM: `scripts/scaffold_posthoc.py`
  → `results/scaffold_posthoc.json`. Per condition, it counts runs with git-history hunting (the `GITHUNT` regex of
  `audit_mtime_cmds.py`), whether that came before the first edit, and pass rates with vs without it. It also counts
  replies in the first 5 steps that mention the listing or times. These counts are descriptive only and carry no test.
- Hygiene record `scripts/scaffold_hygiene.py` → `results/scaffold_hygiene.json`.
