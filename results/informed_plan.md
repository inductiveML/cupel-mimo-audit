# Informed-agent pre-registration (written 2026-10-20 ~07:00Z, before any agent call of this experiment)

## Question
Step B showed that an agent *not told* about the C2 `mtime_scope` leak never used it and was not measurably helped
(ORIG 50/73 vs NORM 47/73; primary 21/30 vs 20/30, McNemar p = 1.0). Here: **does the leak help an agent that is
told to look at recent modification times?** This is a stand-in for an RL policy that has learned `ls -t`.

## The only change to the agent
One line appended (after a newline) to the Step-B system prompt (`scripts/agent.py` SYSTEM), verbatim:

    Tip: files that were modified recently relative to the rest of the repository often indicate where a change belongs, so early on it can help to run `ls -lt` or `find . -newer <some file>` to see them.

Everything else is identical to Step B: task prompt, model `deepseek/deepseek-v4.1-flash-1017`, provider pinned to
`deepseek` with `allow_fallbacks: false`, temperature 0, seed 7, max_tokens 8192, step cap 40, per-run cost cap
$0.15, `docker exec … timeout 120 bash -lc` in `cwd`, output truncation 6,000 chars (head 3,000 + tail 3,000),
DSML parsing (Step-B Amendment 1), bare `echo SUBMIT` stop rule, host-side first-edit detection, same images
(`xiaomimimo/mimo-v2.6-rl-oss:<task>`), same container flags (`--network none --memory 2g --cpus 1.5`, entrypoint
`sleep infinity`, names `mtime_*`), same grader (`git apply` test_patch from `/tmp`, run `test_command`, pass iff
applies and exit 0). Validation results from Step B are reused (no re-validation).

Implementation: new files only. `scripts/agent_informed.py` (parameterised copy of `agent.py`: system prompt,
model, provider, spend file and caps are arguments; loop logic unchanged), `scripts/orclient_informed.py` (copy of
`orclient.py` writing to `results/spend_informed.jsonl`), `scripts/stepB_informed.py` (orchestrator; imports
`prep`, `grade`, `classify`, `files_opened`, `load_tasks`, `late_files` unchanged from `scripts/stepB.py`),
`scripts/informed_analyze.py`. No existing file in `results/` or `runs/<task>/{validate,ORIG,NORM}` is modified.

## Conditions (fresh container per run, one container at a time)
- **INF-ORIG**: hint + original timestamps; prep = `find <cwd> -xdev -exec true {} +` (no-op, as ORIG), then
  `find <cwd> -xdev -newermt @1 | wc -l` recorded.
- **INF-NORM**: hint + `find <cwd> -xdev -exec touch -h -d @0 {} +`, then the same verification must return 0
  or the run aborts (as NORM). Control for "the hint itself just makes the agent more focused".

## Tasks and order (`scripts/informed_order.py` → `results/informed_order.json`)
Exactly the 73 tasks that have both ORIG and NORM runs in `results/stepB_runs.jsonl`. Order = the Step B
processing order (insertion order of `results/stepB_state.json`, i.e. the interleaved strong, strong, random schedule
as actually run): the 30 tasks of the pre-registered primary set (`stepB_analysis.json` "primary_set") first, then
the remaining 43. Condition order within a task: a new seeded coin, **seed 20261020** (`random.Random(20261020)`,
one draw per task in that order; < 0.5 → INF-ORIG first). 37/73 tasks start with INF-ORIG.

Order (last 6 digits of `format-code-task-…`; P = primary, E = extension; first condition):
1 002739 P NORM · 2 002808 P NORM · 3 000877 P NORM · 4 001692 P ORIG · 5 000498 P ORIG · 6 001285 P NORM ·
7 002661 P ORIG · 8 002197 P ORIG · 9 002935 P ORIG · 10 001883 P ORIG · 11 002797 P ORIG · 12 000459 P ORIG ·
13 000162 P ORIG · 14 001495 P NORM · 15 000520 P ORIG · 16 002199 P ORIG · 17 000414 P ORIG · 18 001566 P NORM ·
19 002098 P NORM · 20 001743 P ORIG · 21 001197 P ORIG · 22 003043 P NORM · 23 000230 P NORM · 24 001424 P ORIG ·
25 002820 P NORM · 26 001547 P NORM · 27 001872 P NORM · 28 000409 P NORM · 29 002768 P NORM · 30 000613 P NORM ·
31 002649 E ORIG · 32 001420 E NORM · 33 002256 E ORIG · 34 002201 E NORM · 35 002673 E NORM · 36 001642 E ORIG ·
37 001486 E NORM · 38 002285 E ORIG · 39 002220 E NORM · 40 000691 E NORM · 41 001685 E ORIG · 42 002860 E ORIG ·
43 001804 E ORIG · 44 000377 E ORIG · 45 002051 E ORIG · 46 002659 E NORM · 47 000501 E ORIG · 48 001699 E NORM ·
49 000510 E ORIG · 50 000290 E NORM · 51 001686 E NORM · 52 002109 E NORM · 53 002598 E NORM · 54 000342 E ORIG ·
55 001905 E ORIG · 56 002919 E NORM · 57 001409 E ORIG · 58 000531 E ORIG · 59 002599 E ORIG · 60 002443 E ORIG ·
61 002974 E ORIG · 62 002933 E ORIG · 63 002322 E NORM · 64 001214 E NORM · 65 001568 E ORIG · 66 000670 E NORM ·
67 002461 E NORM · 68 003017 E NORM · 69 000828 E NORM · 70 002833 E ORIG · 71 002798 E ORIG · 72 002335 E NORM ·
73 001935 E NORM

## Smoke test and pilot
1. One tiny call ("Reply with OK", max_tokens 16) through `orclient_informed.chat`, logged in `spend_informed.jsonl`
   as run_id `smoke`.
2. Pilot pair = task 1 (002739), both conditions, full protocol. If the protocol is unchanged after the pilot, the
   pilot pair is part of the main data. If anything changes, the pilot is moved to `results/informed_pilot_v1/`,
   excluded, the change recorded as a dated amendment, and task 002739 re-run from scratch.

## Outcomes and analysis (`scripts/informed_analyze.py` → `results/informed_analysis.json`)
Pass = grader pass as above. Statistics exactly as `stepB_analyze.py`: exact two-sided McNemar on discordant pairs;
paired bootstrap 95% CI over tasks (10,000 resamples, seed 1) for the pass-rate difference and secondary metrics.

**Primary comparisons** (each reported on the pre-registered 30-task primary set, and separately on all 73):
1. **INF-ORIG vs INF-NORM** (paired, same task, same day): the leak's value to an informed agent.
2. **INF-ORIG vs Step-B ORIG** (paired by task): the value of knowing the trick. Caveat to report: ORIG runs are from
   2026-10-19/20 and temperature 0 is not deterministic (15/73 old ORIG/NORM pairs were discordant with no causal
   mechanism), so this comparison mixes the hint effect with day-to-day / run-to-run noise.

**Secondary:** INF-NORM vs Step-B NORM (paired by task); strata (strong/random) descriptively.

**Secondary metrics**, per condition and paired (same three comparisons), medians/means and paired bootstrap CIs:
steps to solve (both-pass pairs; and all pairs with failures counted at the cap 40); effective steps (first
`echo SUBMIT` in any form), prompt/completion/cached tokens and cost per run, plus cost per solved task (total cost /
passes, descriptive); files opened before the first edit; first-edit step (no edit = 41); a late-cluster file opened
before the first edit; final diff touches a late-cluster file; wall time.

**Compliance / mechanism:** time-based commands are classified with the unchanged Step-B `classify` regexes
(`MT_TARGETED`, `MT_VISIBLE`, heredoc bodies stripped, recomputed from saved trajectories) plus the broad keyword
audit of `audit_mtime_cmds.py` (same regexes, applied to INF-* trajectories, output `results/informed_cmd_audit.json`).
Reported per condition: compliance rate = runs with ≥ 1 `mtime_targeted` command, and with one before the first
edit; step of the first such command. **Observational** (not causal): INF-ORIG pass rate among runs that did vs did
not run a time-based command before the first edit (with the INF-NORM pass rate on the same tasks alongside).

**Interpretation rule (fixed now):** a positive INF-ORIG − INF-NORM difference whose CI excludes 0 is evidence the
leak helps an informed agent; a non-significant result is reported as inconclusive for effects below the detectable
size (Step-B power: ~+23 pp needed at n = 30, ~+15 pp at n = 73 with similar discordance), not as "no effect".
The severity verdict (Low vs Medium) is discussed with both the point estimates and the CIs.

## Stopping rules and budget
- Spend: summed `usage.cost` in the NEW `results/spend_informed.jsonl` only (old `spend.jsonl` not counted and not
  appended to; key-level totals never used). **Cap $4.00.**
- A new task (pair) is started only if spend < **$3.55** (leaves room for one pair at ~$0.02–0.05 per run, up to
  the $0.15 per-run cap). The second run of a pair is started only if spend < **$3.70**. Inside a run, every step
  checks spend; at ≥ **$4.00** the run stops (`global_spend_hard_cap`) and the loop ends. Incomplete pairs are
  excluded from paired analyses and reported.
- Disk: before every pull and every container start and at every agent step, free disk on `/` must be ≥ **20 GB**,
  else all Docker work stops (`dock.pull` additionally refuses below 25 GB, as before).
- Wall time: no new task after 2026-10-21T06:00Z.
- One container at a time; each task image removed by exact tag after its task finishes.
- The run is resumable from `results/informed_state.json` (finished conditions are not re-run).

## Optional stronger-model arm (only if budget clearly remains)
Run only if all 73 main pairs are complete and spend ≤ **$2.90** at that point. Then, in a dated amendment before
any call to the new model: pick one mid-tier, cheap OpenRouter model with a first-party provider and prompt caching,
justify it (price, capability), measure one pilot pair (task 1) and record per-run cost; pre-register the task subset
as the primary 30 in the same order, then the extension, and run pairs (INF-ORIG/INF-NORM, same hint, same seeds,
same coin) while spend + 2 × (1.5 × measured pilot per-run cost) < $3.70. Outputs go to
`runs/<task>/INF-ORIG@<model-slug>/`, `INF-NORM@<model-slug>/`, records in `informed_runs.jsonl` with a `model` field.
Reported as exploratory (no pre-registered primary test unless ≥ 30 pairs complete).

## Amendments

### Amendment 1 (2026-10-20T07:25Z, after the pilot and 3 tasks; protocol unchanged, one descriptive metric added)
- Pilot (002739): both conditions ran under the pre-registered protocol. INF-ORIG degenerated into repeated DSML
  markup from step 16 (19 format errors). The same failure mode occurred in Step B (3 ORIG runs with >= 10 format
  errors, max 23; DSML replies were 62-63% of Step-B steps), so nothing was changed and the pilot pair is included
  in the main data, as pre-registered.
- Observation: replies sometimes contain a time-based command that is **not executed**: e.g. 002808 INF-ORIG step 1
  had a ```bash `ls` ``` block *and* a DSML `ls -lt | head`; the unchanged parser (bash block first, DSML only if
  no bash block) ran `ls`; in degenerate replies with several DSML commands, none is executed (format error).
  The harness is kept exactly as in Step B for comparability. **Added (descriptive only, no test):** per condition,
  runs whose reply *text* (with heredoc bodies stripped) matches `MT_TARGETED` anywhere ("attempted"), next to runs
  that *executed* such a command (the pre-registered compliance measure, unchanged).

### Amendment 2 (2026-10-20T15:40Z, during the extension, after an interim look at the primary 30; descriptive only)
Added one **post hoc, descriptive** mechanism metric (no test, no effect on any pre-registered outcome or stopping
rule): for each INF run with an executed time-based command, whether the output of the *first* such command names a
late-cluster file (relative path in the output, or basename as a token when the file is top-level or its directory is
named in the command; heuristic), and whether that file was then opened before the first edit. INF-NORM is the
control (no time signal there). Rationale: compliance alone does not show the agent actually *saw* the leak.
Addendum (2026-10-20T16:45Z, same post-hoc metric, decided after seeing that the "anywhere" variant fires about as often
in INF-NORM as in INF-ORIG, i.e. it detects "listed", not "ranked first"): also report whether a late-cluster file is
named within the first 10 non-empty output lines of that first time-based command. Descriptive only.
