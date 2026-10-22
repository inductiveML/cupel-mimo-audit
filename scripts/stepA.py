"""Step A: offline strength of the mtime_scope signal (no agent, no Docker).

Inputs (read-only): <phase-1>/results/{tier_a.jsonl, manifests/, mtime_precision.json}, data/code.parquet,
plus our own results/mtime_precision_ext.json (extended anchoring) and optionally results/stepB_runs.jsonl (R_agent).
Outputs: results/stepA_metrics.json, results/stepA_per_task.jsonl, results/stepA_table.md

Ranking with ties is scored analytically: E[#relevant in top k] under uniformly random tie-breaking, and
P(hit@k) via the hypergeometric probability for the partially-included tie group.
"""
import json, math, os, random, re, sys
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
from math import comb
import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
import tracked_proxy as tpx

P1 = CUPEL_PHASE1 + ""
OUT = CUPEL_ROOT + "/results"
KS = (1, 3, 5, 10)
BOOT = 2000
SEED = 20261019

TEST_RE = re.compile(r"(^|/)(tests?|testing|spec|specs|__tests__|testdata|fixtures?|usercase-test[^/]*)/|(^|/)test_[^/]*\.py$|_test\.py$|_test\.go$|\.(test|spec)\.[cm]?[jt]sx?$|Test[s]?\.java$|_spec\.rb$|(^|/)conftest\.py$", re.I)
DOC_RE = re.compile(r"(^|/)docs?/|\.(md|rst|txt|adoc)$|(^|/)(CHANGELOG|CHANGES|HISTORY|NEWS|AUTHORS|LICENSE)[^/]*$", re.I)
CODE_EXT = re.compile(r"\.(py|pyx|go|js|jsx|ts|tsx|mjs|cjs|java|kt|rb|php|rs|c|cc|cpp|h|hpp|cs|scala|swift|vue|svelte|lua|ex|exs|clj)$")
STOP = set("the a an and or of to in is it be for on with as by that this from at are was not but if then else when "
           "can should would will use used using get set have has had we you i our your they them there their its into "
           "file files code test tests issue bug error fix make new add also like just which what how why one two any all "
           "some more only than other such may might need want does doesn don isn".split())


# ------------------------------------------------------------------ ranking with ties
def scored_metrics(scores, rel, ks=KS):
    """scores: dict path->sortable score (higher = ranked earlier); rel: set of relevant paths (subset of scores).
    Returns expected precision@k, recall@k and P(hit@k) under uniformly random tie-breaking."""
    groups = {}
    for p, s in scores.items():
        groups.setdefault(s, [0, 0])
        groups[s][0] += 1
        groups[s][1] += p in rel
    order = sorted(groups.items(), key=lambda x: x[0], reverse=True)
    N, R = len(scores), len(rel)
    out = {}
    for k in ks:
        kk = min(k, N)
        taken, erel, miss_all = 0, 0.0, 1.0
        for _, (g, r) in order:
            if taken >= kk:
                break
            j = min(g, kk - taken)
            erel += j * r / g
            # P(no relevant among j drawn from group of g with r relevant)
            miss_all *= comb(g - r, j) / comb(g, j) if g - r >= j else 0.0
            taken += j
        out[f"p@{k}"] = erel / kk if kk else 0.0
        out[f"r@{k}"] = erel / R if R else None
        out[f"hit@{k}"] = 1.0 - miss_all
    return out


def tokens(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    return [t for t in re.split(r"[^A-Za-z0-9]+", s.lower()) if len(t) >= 3 and t not in STOP and not t.isdigit()]


def bm25_scores(paths, query, k1=1.2, b=0.75):
    docs = {p: tokens(p) + tokens(os.path.basename(p)) for p in paths}  # basename tokens double-weighted
    N = len(docs)
    avg = sum(len(d) for d in docs.values()) / max(1, N)
    df = {}
    for d in docs.values():
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    q = set(tokens(query))
    sc = {}
    for p, d in docs.items():
        tf = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for t in q:
            if t in tf:
                idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
        sc[p] = round(s, 9)
    return sc


# ------------------------------------------------------------------ reference sets
def tp_files(tp):
    fs = set(re.findall(r"^diff --git a/(\S+) b/", tp, re.M))
    return {f for f in fs if not f.startswith("mimo_") and f != "test_commands.json"}


def test_stem(p):
    b = os.path.basename(p)
    b = re.sub(r"\.(test|spec)(?=\.[A-Za-z0-9]+$)", "", b)
    stem, ext = os.path.splitext(b)
    stem = re.sub(r"^test_|_test$|_spec$|Tests?$|^Test(?=[A-Z])", "", stem)
    return stem.lower(), ext.lower()


def src_proxy(cands, rtest_all):
    """R_src_proxy: candidate non-test, non-doc code files whose stem equals the stem of a test_patch file after
    stripping test affixes (test_foo.py->foo.py, foo_test.go->foo.go, Foo.test.ts->Foo.ts, FooTest.java->Foo.java).
    For Go the match must be in the same directory (package); for other languages any directory."""
    out = set()
    stems = {}
    for t in rtest_all:
        s, e = test_stem(t)
        if s and s not in ("__init__", "conftest", "index", "utils", "util", "helpers", "main", "common"):
            stems.setdefault(s, []).append(t)
    for p in cands:
        if TEST_RE.search(p) or DOC_RE.search(p) or not CODE_EXT.search(p):
            continue
        s, e = os.path.splitext(os.path.basename(p))[0].lower(), os.path.splitext(p)[1].lower()
        for t in stems.get(s, []):
            if e == ".go":
                if os.path.dirname(t) == os.path.dirname(p):
                    out.add(p)
            else:
                out.add(p)
    return out


def load_rfix():
    out = {}
    srcs = [f"{P1}/results/mtime_precision.json", f"{OUT}/mtime_precision_ext.json"]
    for s in srcs:
        if not os.path.exists(s):
            continue
        for t in json.load(open(s)).get("tasks", []):
            if t.get("status") == "ok" and t.get("fix_files_existing_at_base") is not None:
                out[t["task_id"]] = {"files": set(t["fix_files_existing_at_base"]), "src": os.path.basename(s),
                                     "anchor": t.get("anchor")}
    return out


def load_ragent():
    p = f"{OUT}/stepB_runs.jsonl"
    out = {}
    if not os.path.exists(p):
        return out
    for l in open(p):
        r = json.loads(l)
        if r.get("passed") and r.get("final_diff_files"):
            out.setdefault(r["task_id"], set()).update(r["final_diff_files"])
    return out


# ------------------------------------------------------------------ main
def main():
    rows = [json.loads(l) for l in open(f"{P1}/results/tier_a.jsonl")]
    tasks = {}
    for r in pq.read_table(f"{P1}/data/code.parquet").to_pylist():
        ij = json.loads(r["extra_info"]["instance_json"])
        tasks[ij["instance_id"]] = ij
    rfix, ragent = load_rfix(), load_ragent()
    per = []
    for r in rows:
        tid = r["task_id"]
        mt = (r.get("evidence") or {}).get("mtime") or {}
        flagged = any(f["type"] == "mtime_scope" for f in r.get("findings", []))
        ent = {"task_id": tid, "flagged": flagged, "n_tracked": r.get("n_tracked"), "lang": r.get("lang"),
               "n_late": mt.get("n_late"), "n_late_source": len(mt.get("late_source", [])),
               "late_gap_s": mt.get("late_gap_s"), "compressed_bytes": (r.get("stream") or {}).get("compressed_bytes")}
        if not r.get("n_tracked"):
            ent["excluded"] = "no_tracked_files_phase1"; per.append(ent); continue
        c = tpx.load(tid, r["cwd"])
        late = set(mt.get("late_files", []))
        ent["n_cand"] = len(c)
        ent["proxy_ratio"] = round(len(c) / r["n_tracked"], 4)
        ent["late_missing_from_proxy"] = len(late - set(c))
        ent["proxy_ok"] = 0.95 <= ent["proxy_ratio"] <= 1.05 and ent["late_missing_from_proxy"] == 0
        ij = tasks[tid]
        rtest_all = tp_files(ij["test_patch"])
        refs = {"R_test": rtest_all & set(c), "R_src_proxy": src_proxy(c, rtest_all)}
        if tid in rfix:
            refs["R_fix"] = rfix[tid]["files"] & set(c)
            ent["R_fix_anchor"] = rfix[tid]["anchor"]
        if tid in ragent:
            refs["R_agent"] = ragent[tid] & set(c)
        ent["ref_sizes"] = {k: len(v) for k, v in refs.items()}
        ent["n_rtest_new_files"] = len(rtest_all - set(c))
        rnd = random.Random(f"{SEED}:{tid}")
        mtime = {p: v["m"] for p, v in c.items()}
        lex = bm25_scores(list(c), ij["problem_statement"])
        rankers = {
            "mtime": mtime,
            "random": {p: 0 for p in c},
            "size_desc": {p: v["s"] for p, v in c.items()},
            "size_asc": {p: -v["s"] for p, v in c.items()},
            "lexical_bm25": lex,
            "mtime_then_lexical": {p: (mtime[p], lex[p]) for p in c},
        }
        ent["metrics"] = {}
        for rn, sc in rankers.items():
            ent["metrics"][rn] = {}
            for refn, rs in refs.items():
                if rs:
                    ent["metrics"][rn][refn] = {k: (round(v, 6) if v is not None else None)
                                                for k, v in scored_metrics(sc, rs).items()}
        # late-cluster stats used by step B selection
        ent["late_src_in_rtest"] = len(set(mt.get("late_source", [])) & rtest_all)
        ent["late_overlap_rtest"] = len(late & refs["R_test"])
        per.append(ent)
    with open(f"{OUT}/stepA_per_task.jsonl", "w") as f:
        for e in per:
            f.write(json.dumps(e) + "\n")

    # ---------------- aggregate with bootstrap CIs
    rng = np.random.default_rng(SEED)

    def agg(sel):
        res = {}
        for rn in ("mtime", "random", "size_desc", "size_asc", "lexical_bm25", "mtime_then_lexical"):
            res[rn] = {}
            for refn in ("R_test", "R_src_proxy", "R_fix", "R_agent"):
                vals = [e["metrics"][rn][refn] for e in sel if "metrics" in e and refn in e["metrics"][rn]]
                if not vals:
                    continue
                d = {"n_tasks": len(vals)}
                for m in [f"{x}@{k}" for x in ("p", "r", "hit") for k in KS]:
                    arr = np.array([v[m] for v in vals if v[m] is not None], float)
                    if not len(arr):
                        continue
                    bs = arr[rng.integers(0, len(arr), (BOOT, len(arr)))].mean(1)
                    d[m] = [round(float(arr.mean()), 4), round(float(np.percentile(bs, 2.5)), 4),
                            round(float(np.percentile(bs, 97.5)), 4)]
                res[rn][refn] = d
        return res

    flagged = [e for e in per if e["flagged"] and "metrics" in e]
    out = {
        "note": "values are [mean, boot95_lo, boot95_hi] over tasks; expected metrics under random tie-breaking; "
                "candidates = tracked-file proxy (scripts/tracked_proxy.py); references restricted to files existing at base",
        "bootstrap_resamples": BOOT, "seed": SEED,
        "tracked_proxy_check": {
            "n_tasks_with_tracked": sum(1 for e in per if "n_cand" in e),
            "proxy_ok": sum(1 for e in per if e.get("proxy_ok")),
            "proxy_exact_count": sum(1 for e in per if e.get("n_cand") == e.get("n_tracked")),
            "flagged_total": sum(1 for e in per if e["flagged"]),
            "flagged_proxy_ok": sum(1 for e in flagged if e["proxy_ok"])},
        "flagged_proxy_ok": agg([e for e in flagged if e["proxy_ok"]]),
        "flagged_all": agg(flagged),
        "unflagged_proxy_ok": agg([e for e in per if not e["flagged"] and e.get("proxy_ok")]),
    }
    json.dump(out, open(f"{OUT}/stepA_metrics.json", "w"), indent=1)

    # ---------------- markdown table
    L = []
    for grp in ("flagged_proxy_ok", "flagged_all", "unflagged_proxy_ok"):
        for refn in ("R_test", "R_src_proxy", "R_fix", "R_agent"):
            rows_ = [(rn, out[grp][rn][refn]) for rn in out[grp] if refn in out[grp][rn]]
            if not rows_:
                continue
            L.append(f"\n**{grp} / {refn}** (n = {rows_[0][1]['n_tasks']} tasks)\n")
            L.append("| ranker | hit@1 | hit@5 | hit@10 | P@1 | P@5 | R@5 | R@10 |")
            L.append("|---|---|---|---|---|---|---|---|")
            for rn, d in rows_:
                f = lambda m: (f"{d[m][0]:.2f} ({d[m][1]:.2f}-{d[m][2]:.2f})" if m in d else "-")
                L.append(f"| {rn} | {f('hit@1')} | {f('hit@5')} | {f('hit@10')} | {f('p@1')} | {f('p@5')} | {f('r@5')} | {f('r@10')} |")
    open(f"{OUT}/stepA_table.md", "w").write("\n".join(L) + "\n")
    print(json.dumps(out["tracked_proxy_check"]))


if __name__ == "__main__":
    main()
