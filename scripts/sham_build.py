"""Build the SCF-SHAM lists offline, before any agent call (results/sham_plan.md). No Docker, no agent.

Per task (the 73 tasks of results/scaffold_order.json):
  k        = number of lines of that task's live SCF-ORIG list (results/scaffold_runs.jsonl, scaffold_n_lines);
  cands    = the candidate set the ORIG rule (ANCHOR_EXCL) draws from: regular files under cwd minus .git and the
             Step-A artefact exclusions = tracked_proxy.load(task, cwd) on the phase-1 manifest;
  pool     = sorted(cands - ORIG list); if len(pool) < k, the ORIG-list files are added back (documented per task);
  sham     = random.Random(SEED_BASE + task_number).sample(pool, k), in sampled order;
  line i   = '<timestamp of SCF-ORIG line i>  <sham path i>' (ORIG timestamps reused verbatim, newest first,
             so the column format and mtime values are identical to the ORIG list; only the paths differ).
Records per task: k, pool size, whether ORIG files were added back, and which late-cluster / upstream-fix (R_fix)
files landed in the sham list. Output: results/sham_lists.json"""
import hashlib, json, os, random, re, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
sys.path.insert(0, os.path.dirname(__file__))
import tracked_proxy as tpx
from stepA import load_rfix

ROOT = CUPEL_ROOT + ""
RES = f"{ROOT}/results"
P1 = CUPEL_PHASE1 + ""
SEED_BASE = 20261022000000  # seed for task format-code-task-NNNNNN = SEED_BASE + NNNNNN
LINE_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)  (.+)$")


def main():
    order = json.load(open(f"{RES}/scaffold_order.json"))["order"]
    ta = {json.loads(l)["task_id"]: json.loads(l) for l in open(f"{P1}/results/tier_a.jsonl")}
    rfix = load_rfix()
    scf = {}
    for l in open(f"{RES}/scaffold_runs.jsonl"):
        r = json.loads(l)
        if r["cond"] == "SCF-ORIG":
            scf[r["task_id"]] = r  # last record wins (as the analyses)
    per = []
    for e in order:
        tid = e["task_id"]; r = ta[tid]
        orig_out = open(f"{ROOT}/runs/{tid}/SCF-ORIG/scaffold_output.txt").read()
        lines = [LINE_RE.match(x) for x in orig_out.splitlines() if x.strip()]
        assert all(lines), tid
        ts = [m.group(1) for m in lines]; olist = [m.group(2) for m in lines]
        k = scf[tid]["scaffold_n_lines"]
        assert k == len(ts) and olist == scf[tid]["scaffold_list"], tid
        cands = set(tpx.load(tid, r["cwd"]))
        pool = sorted(cands - set(olist))
        added_back = len(pool) < k
        if added_back:
            pool = sorted(cands)
        seed = SEED_BASE + int(tid[-6:])
        sham = random.Random(seed).sample(pool, k)
        late = set(r["evidence"]["mtime"].get("late_files", []))
        fix = rfix[tid]["files"] if tid in rfix else set()
        out = "".join(f"{t}  {p}\n" for t, p in zip(ts, sham))
        per.append({"i": e["i"], "task_id": tid, "primary": e["primary"], "stratum": e["stratum"], "seed": seed,
                    "k": k, "n_candidates": len(cands), "pool_size": len(pool), "orig_files_added_back": added_back,
                    "n_orig_list_not_in_candidates": len(set(olist) - cands),
                    "sham_list": sham, "orig_list": olist, "sham_output": out,
                    "n_late": len(late), "late_in_sham": sorted(set(sham) & late),
                    "has_R_fix": bool(fix), "rfix_in_sham": sorted(set(sham) & fix),
                    "late_in_orig": len(set(olist) & late)})
    blob = json.dumps(per, sort_keys=True).encode()
    res = {"seed_base": SEED_BASE, "seed_rule": "random.Random(SEED_BASE + int(task_id[-6:])).sample(sorted(pool), k)",
           "n_tasks": len(per), "sha256_of_per_task": hashlib.sha256(blob).hexdigest(),
           "summary": {"k_total": sum(p["k"] for p in per),
                       "k_hist": {str(k): sum(p["k"] == k for p in per) for k in sorted({p["k"] for p in per})},
                       "tasks_orig_added_back": sum(p["orig_files_added_back"] for p in per),
                       "tasks_with_late_in_sham": sum(bool(p["late_in_sham"]) for p in per),
                       "tasks_with_rfix_in_sham": sum(bool(p["rfix_in_sham"]) for p in per),
                       "tasks_with_R_fix": sum(p["has_R_fix"] for p in per),
                       "min_pool": min(p["pool_size"] for p in per)},
           "per_task": per}
    json.dump(res, open(f"{RES}/sham_lists.json", "w"), indent=1)
    print(json.dumps(res["summary"]), res["sha256_of_per_task"])
    for p in per:
        if p["late_in_sham"] or p["rfix_in_sham"] or p["orig_files_added_back"] or p["n_orig_list_not_in_candidates"]:
            print(p["i"], p["task_id"], "k", p["k"], "pool", p["pool_size"], "late", p["late_in_sham"],
                  "rfix", p["rfix_in_sham"], "addback", p["orig_files_added_back"],
                  "orig_not_in_cands", p["n_orig_list_not_in_candidates"])


if __name__ == "__main__":
    main()
