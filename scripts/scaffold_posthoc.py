"""Post-hoc, descriptive (scaffold_plan.md Amendment 1): git-history hunting and mentions of the listing, per condition,
for all six conditions on the 73 tasks. No tests. Output: results/scaffold_posthoc.json."""
import json, os, re, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
sys.path.insert(0, os.path.dirname(__file__))
from analysis_common import strip_heredocs
from informed_analyze import GITHUNT

ROOT = CUPEL_ROOT + ""; RES = f"{ROOT}/results"
MENTION = re.compile(r"recently modified|last-modified|ranked by|modification time|timestamp|mtime|(no files|empty|nothing)[^.\n]{0,60}(modif|listed|list|recent|rank)", re.I)
runs = {}
for f, conds in (("stepB_runs.jsonl", ("ORIG", "NORM")), ("informed_runs.jsonl", ("INF-ORIG", "INF-NORM")),
                 ("scaffold_runs.jsonl", ("SCF-ORIG", "SCF-NORM"))):
    for l in open(f"{RES}/{f}"):
        r = json.loads(l)
        if r["cond"] in conds:
            runs[(r["task_id"], r["cond"])] = r  # last record wins (as the analyses)
tasks = {t for t, c in runs if c == "SCF-ORIG"} & {t for t, c in runs if c == "SCF-NORM"}
out = {}
for c in ("ORIG", "NORM", "INF-ORIG", "INF-NORM", "SCF-ORIG", "SCF-NORM"):
    n = gh = gh_pre = gh_pass = nogh_pass = ment = gh_first3 = 0
    for t in sorted(tasks):
        r = runs.get((t, c))
        if not r:
            continue
        n += 1
        steps = [json.loads(l) for l in open(f"{ROOT}/runs/{t}/{c}/trajectory.jsonl")]
        ghs = [e["step"] for e in steps if e.get("cmd") and GITHUNT.search(strip_heredocs(e["cmd"]))]
        fe = r["first_edit_step"] or 41
        if ghs:
            gh += 1; gh_pass += r["passed"]
            gh_pre += ghs[0] < fe
            gh_first3 += ghs[0] <= 3
        else:
            nogh_pass += r["passed"]
        ment += any(MENTION.search(e.get("content") or "") for e in steps[:5])
    out[c] = {"n": n, "runs_githunt": gh, "githunt_before_first_edit": gh_pre, "githunt_in_first_3_steps": gh_first3,
              "pass_if_githunt": gh_pass, "pass_if_no_githunt": nogh_pass,
              "reply_mentions_listing_or_times_first5": ment}
json.dump({"note": "post hoc, descriptive only (Amendment 1); GITHUNT regex from audit_mtime_cmds.py", "by_cond": out},
          open(f"{RES}/scaffold_posthoc.json", "w"), indent=1)
for c, v in out.items():
    print(c, v)
