"""Where the analysis scripts look for data.

CUPEL_ROOT   : the folder holding results/ (and, for the full re-analysis, runs/<task>/<cond>/trajectory.jsonl).
               Defaults to the root of this repository.
CUPEL_PHASE1 : the phase-1 scan outputs (results/tier_a.jsonl, results/manifests/, results/mtime_precision.json,
               data/code.parquet). Not included in this repository.
"""
import os

CUPEL_ROOT = os.environ.get("CUPEL_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUPEL_PHASE1 = os.environ.get("CUPEL_PHASE1", os.path.join(CUPEL_ROOT, "phase1"))
