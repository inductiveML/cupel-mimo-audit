# PHASE 1 REPORT: Xiaomi MiMo fix verification and scanner calibration

**Date:** 2026-10-19 (run on a 4 CPU / 7 GB RAM VPS)
**Scope:** Tier A (static) only. No Tier B or Tier C runs, no `docker pull`, nothing pushed or published, no outreach.
**Detector:** `tierA-1.0`, combined hash `d128e438d3232ba1` (`results/detector_hash.txt`, per-file sha256 in `results/detector_files.sha256`). All 300 sample results come from this version. A noise-filter update, `tierA-1.1` (hash `fdb2939d6164ba36`, `results/detector_hash_v1.1.txt`), was applied after the run (see §6). It was regression-tested with recall and on the one affected task, but it was **not** used for the headline numbers.
**Goal:** check whether Xiaomi fixed the unreachable-git-object leak that Vals reported, find any residual or new leak classes, and calibrate the scanner's recall with planted leaks.

Every number below comes from files in `results/` or from a cited source. Inferences are labelled as such.

---

## 1. Headline

| Question | Answer (stratified random sample, n = 300 of 2,602) |
|---|---|
| Does the fix survive in git (Vals' class, C1 FIX-PRESENT)? | **0 / 300 tasks.** 95% Wilson CI **0 – 1.26%** (rule-of-three upper bound 1.0%). No unreachable objects, no commits outside HEAD's history, no reflogs, stash, pseudo-refs or remote refs in any primary repo. **Xiaomi's git fix holds on the current images.** |
| Vals' figure, for contrast | 1,795 / 2,698 (66.5%) "fix commit survives as unreachable objects" ([Vals, 2026-10-07](https://www.vals.ai/blogs/mimo-reward-hacking)), measured on the images that existed before the re-push. |
| Residual leak: modification-time scope trail (C2 `mtime_scope`) | **256 / 300 = 85.3%** (95% CI 80.9 – 88.9%). The base checkout has a separate, later cluster of tracked files (median gap 424 s), and that cluster contains ≥ 1 source file. In **213 / 300 = 71.0%** (65.6 – 75.8%) the cluster also contains files touched by the task's `test_patch` (or their directories). |
| Is that mtime cluster really the reference-patch scope? | Upstream spot-check (public GitHub, read-only): in **every task where the upstream fix could be anchored (13 of 60 attempted), the late-mtime set equalled the upstream fix's file set exactly (precision = recall = 1.0)** (`results/mtime_precision.json`). Most sampled HEADs could not be anchored with anonymous API access; see §4.3. |
| Scanner recall on planted leaks | **115 / 115 (100%)** across **23 leak types** × 5 bases each, using all 20 clean bases. 0 detections on the unplanted bases (`results/recall.json`). |

**Bottom line:** the git-object leak that Vals headlined is gone from the current images. The secondary leak Vals also showed ("`find -newermt` reveals the full set of files modified by the reference solution") is **still present in about 85% of tasks**. Wherever we could anchor it upstream, it gives the exact set of files the reference fix changes. Per spec §5 that is I2 (scope reveal, not the solution) ∧ R4 (ordinary tool use, `find -newermt`) → **Low**, possibly Medium if Tier B shows that scope plus the issue text materially raises solve rate. That needs Tier C to decide.

---

## 2. Dataset, revision and image pins

| Item | Value |
|---|---|
| HF dataset | `XiaomiMiMo/MiMo-V2.6-RL-oss`, revision **`971cab2ab421fd88db29770db0d0e52014b63615`** (2026-10-18T12:41:01Z), same as the spec 08 §6 pin |
| `code.parquet` | 2,602 rows, sha256 `3a531075…b8b3ba9` |
| Drift vs Vals | HF commit `6b9046cc42d8` (2026-10-18): "code: drop 96 excluded tasks (2698 -> 2602 rows); no content changes to kept rows". Verified locally against revision `639865fd3374` (2,698 rows): 96 IDs removed, 0 kept rows changed. The dropped IDs are in `data/dropped_96.json`; their Docker tags no longer exist. |
| Images | `docker.io/xiaomimimo/mimo-v2.6-rl-oss:format-code-task-NNNNNN`, one per task. Each is a single flattened gzip layer. All 2,602 tags have `last_pushed` = 2026-10-16 (Hub API), 9 days after Vals' post. |
| Digests scanned | All 300 image digests are recorded per task in `results/tier_a.jsonl` (`image_digest`, `layers`). 0 of 300 differed from the tag listing captured at the start of the run (no drift during the scan). |
| Git pack dates inside the images | From tar headers of the primary repo packs: 296 × 2026-10-10, 3 × 2026-10-13, 1 × 2026-10-09 (`results/pack_dates_from_manifest.json`). All are after Vals' post. This is consistent with Xiaomi re-packing or garbage-collecting the repos and re-pushing, but that is an inference: no Xiaomi statement was found. |
| Gold patch | **Not shipped** (`reward_model.ground_truth` is empty for all rows). Only `test_patch` is provided. 475 / 2,602 tasks (51 / 300 in the sample) use Xiaomi-authored tests (`usercase-test-*`); the rest use upstream test diffs. |

---

## 3. Method

### 3.1 Acquisition: no `docker pull`, nothing stored
- Layer digests come from the Hub web API (`/v2/repositories/…/tags/<tag>/images`), so the anonymous registry manifest limit is never touched. The token claims show `pull_limit 100 / 21600 s`; the response header showed `ratelimit-limit: 100;w=3600`. Blob GETs do not count toward the limit.
- Each layer is streamed through `curl | pigz -dc | python tarfile`. Every tar member is recorded (path, size, mtime, mode, git-blob sha1 for files ≤ 64 MB) to `results/manifests/<task>.jsonl.gz`. Only Tier A evidence is extracted: every `.git` dir, VCS caches, `.pytest_cache`, `.pyc` and small files under the task cwd, and backup, patch or credential-named files. Everything is deleted after analysis, except 20 clean workdirs kept for recall.
- Sample: seeded random order, stratified by language (from `test_patch` extensions: python / go / js-ts / other) × image-size tertile (12 strata), interleaved proportionally. The first 300 were scanned, so any prefix is itself a stratified random sample (`results/sample_order.json`). Per-stratum counts are in `results/summary.json`.

### 3.2 Match rule (pinned before counting)
The full rule is in `MATCH_RULE.md`. Briefly: there is no gold patch, so **C1 FIX-PRESENT** means a recoverable commit (from any object store in the image, including packs without an `.idx`, alternates, submodules and secondary clones) that is *later* than HEAD (a descendant of HEAD, or newer committer time) and changes ≥ 1 non-test, non-doc path. It is labelled *strong* if that commit also contains an exact post-`test_patch` blob or covers the late-mtime source set. Partial matches (orphan blobs or trees, test-only commits, staged index entries) are counted separately and are never counted as fix-present.

### 3.3 Tier A checks run on every task
- **Git:** the full object inventory via `cat-file --batch-all-objects`; direct pack-header and idx parsing (object counts, packs missing their idx, which are re-indexed by the scanner); `fsck --unreachable --no-reflogs`; all refs (heads, tags, remotes, notes, replace, stash, other); pseudo-refs (ORIG_HEAD, FETCH_HEAD, …); reflogs; worktrees; submodule git dirs; secondary repos containing HEAD; index-vs-HEAD (staged) comparison; post-`test_patch` blob presence.
- **Filesystem:** mtime clustering of the tracked files; directory mtimes of the test locations; stale `.pyc` detection from header source size and mtime vs the current source (handles both the 3.3–3.6 and the PEP 552 header layouts); editor-backup and patch residue; copies of project files elsewhere on disk (site-packages, Go module cache, `build/lib`, bundled tools) that differ from HEAD; blobs from later commits found on disk; post-`test_patch` (hidden-test) files found on disk; hidden test names in `.pytest_cache`; worktree vs HEAD.
- **Grader and sandbox (static only):** `mimo_test_command.sh` is **not present in any of the 300 images**, so it is injected at grading time and the grader logic is not statically auditable from the image. 89 / 300 tasks have a `conftest.py` in the agent-writable repo (only a C3 *surface*; confirming it needs Tier B). Credential files and `docker.sock` are searched for. Network egress is a runtime harness property and **cannot** be judged from the image (not claimed either way).

---

## 4. Results (n = 300, detector tierA-1.0)

### 4.1 Per finding type: raw, and after triage (§6)

| Category / type | Raw tasks | After triage | Rate after triage (95% Wilson) | Notes |
|---|---|---|---|---|
| **C1 fix_present** (any route) | **0** | **0** | 0% (0 – 1.26%) | Also 0 tasks with any fsck-unreachable object, any non-HEAD commit, reflogs, stash, pseudo-refs, remote or other refs, or packs without idx |
| C1 git_without_head | 1 | 1 | 0.3% | Task 000474: HEAD → `refs/heads/master`, which does not exist (no loose or packed refs). Re-scanned with v1.1, which derives the base from the index tree: 2 commits, both base history, **no later commit**. A broken ref, not a leak (`results/recheck_000474_v1.1.json`) |
| **C2 mtime_scope** | **256** | **256** | **85.3% (80.9 – 88.9%)** | Test-correlated: 213 (71.0%, 65.6 – 75.8%). Late source files per task: 1 file in 88 tasks, 2 in 47, 3 in 32, 4 in 20, 5 in 16, ≥ 6 in 53 (max 30, capped list) |
| C6 mtime_test_dir_hint | 12 | 12 | 4.0% (2.3 – 6.9%) | No late source cluster, but the directories where hidden tests are added have later mtimes (reveals test location) |
| C2 project_copy_differs | 24 | 5 | 1.7% | After triage: npm/cli task with a different npm bundled in `/opt/node-20` (001135); poetry task with poetry installed in site-packages (002412); scipy build env (002607); pre-commit stale `build/lib` (002308, 1 file differs: `constants.py`); 000039 (Go toolchain's vendored `x/sys` vs the project's vendored copy), which I judge **coincidental** on manual review. Copy versions not inspected; these are Tier B or manual candidates |
| C2 stale_pyc | 1 | 1 | 0.3% | **001372 (bigframes):** `__pycache__` for `third_party/bigframes_vendored/pandas/core/{frame,series}.py`, `io/gbq.py`, `version.py` was compiled from source of a **different size** (e.g. frame.py 260,858 B in the pyc vs 260,051 B on disk), and those files are in the task's late-mtime set. **Strongest new candidate:** the bytecode may hold the other (possibly post-fix) version. Needs decompile and Tier B |
| C2 worktree_dirty | 5 | 1 | 0.3% | The 4 dropped are eol conversion (verified on 002621: `*.bat text eol=crlf`). The remaining one is `vendor/…/meeting.ics`, almost certainly the same eol effect |
| C1p index_staged | 6 | 0 | 0% | All were non-ASCII paths mis-parsed by v1.0 (quoted `ls-files` output); fixed in v1.1 (`-z`) |
| C6 hidden_test_file_on_disk | 3 | 0 | 0% | All were empty `__init__.py` (or < 32 B) matching unrelated empty files |
| C2 backup_residue | 1 | 0 | 0% | A conda recipe patch touching a generic root `setup.py` |
| C4 credential_files | 1 | 1 | 0.3% | `/testbed/.pypirc` (111 B) in task 000582 (boxsdk). Content and tracked status not inspected; likely an upstream fixture. Info only |
| QA extract_incomplete | 1 | 1 | – | Task 001299 (gitea): a *testdata* repo inside the project ships an `.idx` without its `.pack`. This is upstream test data, not our extraction (the primary repo is complete) |

Raw per-task results: `results/tier_a.jsonl`. Triaged results: `results/tier_a_triaged.jsonl`. Counts: `results/summary.json` and `results/triage_summary.json`.

### 4.2 By stratum (mtime_scope / n)
python 107/134 · go 65/78 · js/ts 60/63 · remaining languages 24/25 (c/c++ 3/3, java 3/3, php 2/2, ruby 2/3, unclassified 14/14). Synthetic-test tasks (`/workspace/repo`, `usercase-test-*`): 49/51. Upstream-test tasks: 207/249. **fix_present = 0 in every one of the 12 strata.** Full table: `results/summary.json → per_stratum`.

### 4.3 Upstream precision check of mtime_scope
`scanner/mtime_precision.py` used the anonymous GitHub API (read-only; 60 requests/h). For mtime-flagged tasks taken in a seeded random order: find the non-fork repo containing HEAD → find either (a) an upstream commit whose parent is exactly HEAD, or (b) a PR whose `base.sha` is exactly HEAD → compare its file list with the late-mtime set. Only files that exist at base are compared, since files the fix adds have no mtime to leak.
- Results (`results/mtime_precision.json`): **60 tasks attempted. 13 anchored (11 by a commit whose parent is HEAD, 2 by a PR whose base is HEAD). 13/13 exact matches, mean precision 1.0, mean recall 1.0.** Of the rest, 16 had a HEAD that GitHub commit search could not find (the search index excludes many repos and mirrors), and 31 had no exact HEAD anchor (e.g. a squash-merge whose parent is not the task base). These are reported as unmapped, not counted as failures.
- Two earlier versions of this check were discarded and are kept in `results/dev/`: v0 mapped HEADs to random forks; v1 required parent == HEAD only.
- Caveat: an anchored subset may be biased toward simple, single-commit fixes.

### 4.4 Comparison with Vals' 1,795 (go-gate)
Under the original framing of the task (replicate Vals' count), the go-gate (within ~10% of 1,795) **does not apply**. The task was later reframed as fix verification, and the expected and observed C1 count on current images is ~0. Root cause of the gap, with evidence:
1. **Images were rebuilt after Vals' post.** All tags were re-pushed on 2026-10-16, and repo packs are dated 2026-10-09 to 2026-10-13.
2. **The dataset was revised.** 96 tasks were dropped on 2026-10-18 (2,698 → 2,602).
3. **The scanner is not blind to the class.** Recall on planted unreachable, packed-unreachable, branch, tag, remote, stash, reflog, ORIG_HEAD, pack-without-idx and secondary-clone leaks is 100% (§5).

Per spec §6 this is the documented "image drift / revision pin" root cause, together with recall at the target. The pre-fix images are no longer tagged, so Vals' 1,795 cannot be reproduced from public artifacts. The spec's ≥ 95% precision gate was not run: there are 0 C1 candidates to check, and the C2 mtime precision is covered by §4.3.

---

## 5. Recall calibration (planted leaks)

20 clean bases were kept from the final run: 7 python, 5 go, 5 js/ts, 3 other; 0 C1 findings at v1.0. A synthetic "fix" (a small appended function) was added to a deterministic tracked source file. Each type was planted into 5 bases (round-robin over all 20), the scanner was re-run, and a hit was counted only if the expected finding fired **and pointed to the planted object or file**, and the same check was **negative on the unplanted base**.

| Leak type | Recall (detected / planted) |
|---|---|
| unreachable commit (loose) | 5/5 |
| unreachable, packed (Vals' scenario: objects in a pack, no ref) | 5/5 |
| leftover branch | 5/5 |
| tag | 5/5 |
| remote-tracking ref | 5/5 |
| stash | 5/5 |
| reflog-only | 5/5 |
| pseudo-ref ORIG_HEAD | 5/5 |
| packfile only, `.idx` missing (git ignores it; needs direct pack parsing) | 5/5 |
| secondary bare clone elsewhere on disk | 5/5 |
| orphan blob only (partial class) | 5/5 |
| staged in index | 5/5 |
| mtime cluster on the fixed file | 5/5 |
| `__pycache__` compiled from fixed code | 5/5 |
| editor backup `.orig` | 5/5 |
| editor backup `~` | 5/5 |
| patch residue (`/tmp/reference.patch`) | 5/5 |
| Go module cache copy with fixed file | 5/5 |
| site-packages build copy with fixed file | 5/5 |
| in-repo `build/lib` copy with fixed file | 5/5 |
| future blob on disk (fixed file copied elsewhere) | 5/5 |
| hidden test file on disk | 5/5 |
| hidden test names in `.pytest_cache` | 5/5 |
| **Total** | **115/115 (100%)** |

`results/recall.json` (tierA-1.0) holds every trial. A v1.1 regression pass (2 bases per type) detected **46/46** (`results/recall_v1.1.json`).
**Caveat:** the plants were written by the same author as the detectors, so 100% shows the detectors implement their spec. It does not show coverage of unknown techniques. Spec §6 still requires independent seeding (another person or model) and Tier C discovery runs before claiming coverage.

---

## 6. Problems found and how they were handled

| Problem | Effect | Fix |
|---|---|---|
| Dev run (v0.3, 32 tasks): files > 64 MB were hashed but **never written**, so large `.pack` files were missing | 8/32 dev tasks had no analysable git ("HEAD unresolvable") | Streamed extraction of any wanted file regardless of size. Dev results discarded (`results/dev/`). The final run used the fixed code, and a QA check (idx without pack) was added |
| py3.6 `.pyc` header parsed as the PEP 552 layout | false stale_pyc | Handled per magic-number range |
| Noise classes in v1.0 (eol-converted files, quoted non-ASCII index paths, empty-file blob matches, coincidental path tails, generic `setup.py` patches) | 33 raw findings in 300 tasks | Post-hoc triage rules T1–T5 (`scanner/triage.py`), written after manual review and applied to v1.0 results. Raw and triaged counts are both reported. Also implemented in the analyzer as **v1.1**, together with a HEAD-unresolvable fallback (base from the index tree) |
| Recall cross-product (23 × 20) was too slow (~6–7 h; fsck on a 23k-commit / 1.6 GB pack) | – | 5 bases per type in round-robin |
| GitHub precision check: fork mapping and over-strict anchor | wrong / empty results | Fixed and re-run; earlier logs kept in `results/dev/` |
| Hub tag listing caps anonymous pagination | – | Name-prefix queries (≤ 100 tags each) |
| Pack mtime in one task's evidence (from the extracted file) did not match the tar header | cosmetic | Pack dates are reported from tar manifests |

---

## 7. Disk and time used

| Item | Value |
|---|---|
| Final run wall clock | 11,399 s (3.17 h) for 300 tasks, 3 workers. Part of it overlapped with the recall run, which competed for CPU |
| Data streamed | 665.1 GB compressed → 1,801 GB of file content hashed (ratio ≈ 2.7) |
| Throughput | 21.6 MB/s compressed per worker (median 132.5 s per task), ≈ 58 MB/s aggregate. Bound by gzip decompression (`pigz -dc` ≈ 47 MB/s per stream when uncontended). Single-blob network fetch was measured at ≈ 265 MB/s |
| Disk | Lowest free space on `/` logged during the final run was 52 GB (60 GB at start; floor is 10 GB). Persistent footprint: `results/` 1.5 GB (mostly per-task manifests), `work/keep` 3.4 GB (20 recall bases), `data/` 26 MB |
| Docker | 0 images pulled, 0 containers run |
| Full-census extrapolation (not run) | 2,602 tasks × 5.76 TB → about 27 h at the measured ≈ 58 MB/s aggregate (inference from the measured rate) |

---

## 8. MiMo follow-ups that also need Tier B (optional, small; as planned on 2026-10-19)
- Confirm the bigframes stale-`.pyc` candidate: decompile, diff against base, apply, grade.
- For the 13 anchored mtime tasks: measure whether giving the scope plus the issue text changes solve rate (Tier C), so the mtime severity is set from measurement rather than assumed.

---

## 9. Deliverables index
Not published in this repository: `DISK_PLAN.md`, `MATCH_RULE.md` (summarised in §3.2), the private `scanner/` (stream.py, analyze.py [v1.1; v1.0 copy at `results/dev/analyze_v1.0.py`], run.py, plant.py, triage.py, summarize.py, mtime_precision.py, registry.py, tasks.py), `results/tier_a.jsonl` (300 rows, v1.0), `results/tier_a_triaged.jsonl`, `results/summary.json`, `results/triage_summary.json`, `results/recall.json`, `results/recall_v1.1.json`, `results/mtime_precision.json`, `results/manifests/` (per-task file manifests with mtimes and hashes), `results/sample_order.json`, `results/dev/` (discarded dev artefacts). The scanner and its raw outputs are private and are not part of this repository.
