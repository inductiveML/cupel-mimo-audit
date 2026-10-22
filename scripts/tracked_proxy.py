"""Proxy for the set of git-tracked regular files under a task cwd, from the phase-1 manifest only.

Phase 1 (scanner/analyze.py) used the HEAD tree (git ls-tree) as 'tracked'. The HEAD tree is not stored offline,
so we approximate it: regular files under cwd, excluding .git/ and well-known untracked artefact directories /
extensions. Agreement with the phase-1 exact tracked count (n_tracked) is measured in stepA (tracked_proxy_check).
"""
import gzip, json, re
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1

MAN = CUPEL_PHASE1 + "/results/manifests/{}.jsonl.gz"
IGN_DIRS = {".git", "node_modules", ".venv", "venv", ".tox", ".nox", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", ".hypothesis", ".eggs", ".gradle", ".next", ".nuxt", ".cache", "site-packages",
            ".parcel-cache", ".turbo", ".yarn", ".pnpm-store", ".bundle", ".m2", ".cargo", ".rustup"}
IGN_DIR_RE = re.compile(r"\.egg-info$|\.dist-info$")
IGN_EXT = re.compile(r"\.(pyc|pyo|o|so|a|class|obj)$")


def load(task_id, cwd):
    cwd = cwd.strip("/")
    files = {}
    with gzip.open(MAN.format(task_id), "rt") as f:
        for l in f:
            r = json.loads(l)
            if r["t"] != "f" or not r["p"].startswith(cwd + "/"):
                continue
            rel = r["p"][len(cwd) + 1:]
            parts = rel.split("/")
            if any(p in IGN_DIRS or IGN_DIR_RE.search(p) for p in parts[:-1]) or IGN_EXT.search(rel):
                continue
            files[rel] = {"m": r["m"], "s": r["s"]}
    return files
