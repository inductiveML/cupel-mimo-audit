# Step B pre-registration (written 2026-10-19, before any agent run)

## Question
Does the C2 `mtime_scope` leak (a late mtime cluster of tracked files in the base checkout) help a cheap LLM agent
solve MiMo tasks? Paired A/B: same task, same image, same agent; only file timestamps differ.

## Task selection (`scripts/stepB_select.py`, output `results/stepB_selection.json`, seed 1019)
- Pool: tasks flagged `mtime_scope` in phase-1 `tier_a.jsonl` (256), whose tracked-file proxy agrees with phase-1
  `n_tracked` within 5% and contains every phase-1 late file (218), and whose compressed image is <= 1.2 GB
  (83; disk/time constraint, documented exclusion: 135 larger images).
- Strong stratum (37): >= 1 late source file, late cluster <= 10 files, and late cluster overlaps R_test (>= 1 file)
  or the task has an anchored upstream fix (R_fix, at selection time).
- Random stratum (46): the rest of the pool.
- Seeded order within each stratum; tasks are taken in that order, interleaved strong, strong, random, ...
  Target: **20 strong + 10 random = 30 validated tasks** (final n set after the pilot so total spend stays < $4.50 and
  wall time ~12 h; a smaller n will be reported as such). Tasks that fail validation are skipped (logged with reason)
  and the next task in the same stratum's order is used.

## Grader and pass criterion
- `test_patch` ships `mimo_test_command.sh` (and sometimes a base64 build-env tarball), so the grader is: after the
  agent finishes, write `test_patch` to `/tmp` (outside the repo), `git apply` it in `cwd` (fallback `patch -p1`),
  then run `test_command` with timeout `verifier_timeout_sec` (1800 s for all tasks).
- **Pass iff test_patch applies and `test_command` exits 0.** (The script uses `set -e`/pipefail or OR-ed rc.)
- The final state is graded whether or not the agent submitted (same rule in both conditions).
- Containers: `--network none --memory 2g --cpus 1.5`, entrypoint overridden with `sleep infinity`, named `mtime_*`.

## Validation (before agent runs, per task)
Fresh container, NO changes, in both ORIG and NORM: grader must FAIL. Exclude (and log) if: test_patch does not
apply; base passes in ORIG; base passes in NORM (normalization alone changes the grade); base grader exceeds 900 s or
times out (wall-time budget); base grader output shows network errors (we run offline and do not enable network).
No gold patch exists, so there is **no gold-pass check**: some tasks may be unsolvable in this environment, which
only adds concordant fail/fail pairs (reduces power, does not bias the paired difference).

## Conditions (fresh container per run from the same image)
- ORIG: `find <cwd> -xdev -exec true {} +` (no-op of the same shape), then `find <cwd> -xdev -newermt @1 | wc -l` (recorded).
- NORM: `find <cwd> -xdev -exec touch -h -d @0 {} +` (all files, dirs, symlinks, including `.git`), then the
  same verification must return 0 or the run aborts. `cwd` is the working directory. Files outside `cwd`
  (site-packages copies, caches) are not touched (documented limitation).
- Condition order within a task: seeded coin (seed 4242); tasks in the seeded order above. One container at a time.

## Agent (`scripts/agent.py`)
- Model `deepseek/deepseek-v4.1-flash-1017` via OpenRouter, provider pinned to `deepseek` (first-party, automatic
  prompt caching), `allow_fallbacks: false`, temperature 0, seed 7, max_tokens 8192 per response (default reasoning).
- mini-swe-agent-style: one bash block per reply; each command is `docker exec -w <cwd> <c> timeout 120 bash -lc` (login shell, as the shipped graders use `bash -lc`; images set only PATH);
  output merged stdout+stderr, truncated to 6,000 chars (head 3,000 + tail 3,000); no state between commands.
- Step cap 40 model calls; per-run cost cap $0.15; run ends on a reply whose only command is `echo SUBMIT`.
- System prompt and task prompt are fixed (see `scripts/agent.py`, constants SYSTEM and TASK); task prompt =
  cwd + problem statement + "Make the minimal source change to resolve the issue. Do not modify tests. When you are
  done, finish by running `echo SUBMIT` as your only command." No mention of timestamps.
- Budget: stop launching new runs at $4.50 summed `usage.cost` (results/spend.jsonl), stop everything at $5.00.

## Recorded per run (`results/stepB_runs.jsonl`, trajectories in `runs/<task>/<cond>/`)
pass/fail; steps; prompt/completion/cached tokens; cost; wall time; mtime-revealing commands (regex classes
`mtime_targeted` and `mtime_visible`, see `scripts/stepB.py`); first edit step (host-side `git diff --name-only` +
new untracked files named in the command, after every step, not counted as agent steps); files opened before the
first edit (command tokens that resolve to candidate files - heuristic); final diff files; overlap with late cluster.

## Pilot
2 tasks x 2 conditions (first two strong tasks in order). If the protocol is unchanged after the pilot, the pilot
pairs are included in the main analysis; if anything is changed, they are excluded and reported separately.

## Analysis plan
- Primary: paired pass-rate difference ORIG - NORM; exact McNemar test on discordant pairs (b = ORIG pass/NORM fail,
  c = ORIG fail/NORM pass), two-sided; paired bootstrap 95% CI over tasks (10,000 resamples, seed 1).
- Secondary: steps (both-pass pairs; and all pairs with failures counted at the cap 40), tokens, cost, files opened
  before first edit, first-edit step; medians and paired bootstrap CIs of the mean/median paired difference.
  Rate of mtime-targeted / mtime-visible commands per condition.
- Subgroups: strong vs random strata (descriptive); ORIG runs with vs without an mtime-targeted command
  (observational, not causal).
- Power: with ~30 pairs, exact McNemar needs a lopsided split of discordant pairs (e.g. 9:1 of 10, 8:0 of 8) for
  p < 0.05; effects below ~25-30 percentage points are unlikely to be detected. A non-significant result will be
  reported as inconclusive, not as "no effect".

## Amendment 1 (after pilot v1, before the main run; 2026-10-19T19:50Z)
Pilot v1 (tasks 002739, 002808) showed: (a) the model sometimes emits its native tool-call markup
(`<｜｜DSML｜｜ ... parameter name="command" ...>CMD</...parameter>`) instead of a ```bash block (5/40 replies on
002739 counted as format errors); (b) the regex `\bstat\b` misfired on Python code (`stat, pv, ... = adfuller(...)`);
(c) on 002739 neither condition edited any file in 40 steps (pure exploration until the cap).
Changes, identical in both conditions:
1. A reply with no ```bash block but with DSML `parameter name="command"` markup is parsed as that command.
2. `stat` counts as mtime-targeted only in command position (start, after `| ; & ( \``, or after `xargs`);
   Python `os.stat(`, `.stat()`, `getmtime`, `st_mtime` remain; the loose `sort ... time` rule was dropped.
   (Classification is re-computed from saved trajectories at analysis time, so it is the same for all runs.)
3. System prompt adds one sentence: "You can run at most 40 commands in total, so do not spend them all on exploration."
Pilot v1 records are moved to `results/pilot_v1/` and excluded from the main analysis. Per the pre-registered rule,
the pilot tasks are not dropped from the seeded order: they are re-run from scratch under the amended protocol
(the agent is stateless, so this does not leak anything into the runs).
Pilot v1 measurements: ~$0.02 and ~3.2 min per 40-step run (prompt caching ~95% of prompt tokens);
base grader 3 s (002739) and ~4-5 min (002808).

## Amendment 2 (during the main run, 2026-10-19T21:50Z): network-error heuristic bug
The validation rule "exclude if base grader output shows network errors" used a case-insensitive regex in which
`ENOTFOUND` matched `ServiceNotFound` (Home Assistant exception). Task 001495 was therefore wrongly excluded as
"grader_needs_network" although its base output is an ordinary test failure; the main loop then took the next strong
task in order. Correction (decided before seeing any agent result on 001495): the regex is made case-sensitive and
the generic `ConnectionError` token dropped. After the main loop, every exclusion is re-checked against saved
validation logs with the fixed regex; wrongly excluded tasks are run under the same protocol. The **primary analysis
uses the set the corrected rule would have selected** (first 20 valid strong + first 10 valid random in seeded order):
a wrongly-excluded task replaces the last task of its stratum that was taken only because of the bug. The run set
including both is reported as a sensitivity analysis.

## Amendment 3 (2026-10-19T23:50Z, during the main run): extension sample
Decided AFTER an interim look at 26 pairs (18 vs 17 passes, no mtime-targeted commands), so it is labelled as
such. Spend (~$0.93) and time allow more pairs. After the pre-registered 30 tasks (and the Amendment-2 re-run), the
loop continues through the rest of the same pool in the same seeded orders and interleaving, until the pool is
exhausted, my spend reaches $4.50, or 2026-10-20T07:30Z (wall-time cap), whichever is first. Same protocol.
Reporting: the **primary** result stays the pre-registered 30-task set; "all pairs" (primary + extension) is a
secondary analysis. Optional stopping is not used: the extension's stopping rule is fixed here and does not depend
on results.

## Amendment 4 (2026-10-20T00:50Z): classifier false positive
`os\.stat\(` under re.I matched Go source `os.Stat(` written via a heredoc (002673 ORIG). The mtime classifier is
now case-sensitive and heredoc bodies are stripped before matching. Classification is recomputed from saved
trajectories for every run at analysis time, so all runs use the same final rule. Pass/fail is unaffected.
