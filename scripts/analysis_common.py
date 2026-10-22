"""Analysis helpers used by the published analysis scripts.

Verbatim copies of the command classifier (MT_TARGETED, MT_VISIBLE, HEREDOC, strip_heredocs, classify), the
files-opened heuristic (files_opened) and the late-cluster lookup (late_files) from the study's Step-B orchestrator.
The orchestrator itself (containers, agent loop, model client) is not published; nothing here runs an agent.
late_files() reads the phase-1 scanner output tier_a.jsonl, which is not included in this repository.
"""
import json, re

from cupel_paths import CUPEL_PHASE1


MT_TARGETED = re.compile(
    r"\bls\b[^|;&\n]*\s-[A-Za-z]*t|--sort[= ]time|\bls\b[^|;&\n]*--time|(?:^|[|;&(`]\s*|xargs\s+(?:-\S+\s+)*)stat\s|"
    r"\bfind\b[^|;&\n]*-(newer\w*|mtime|mmin|ctime|cmin|amin|atime|printf[^|;&\n]*%[TtCcAa@])|"
    r"git\s+ls-files[^|;&\n]*--debug|getmtime|getctime|st_mtime|st_ctime|os\.stat\(|\.stat\(\)|os\.lstat\(|"
    r"\btree\b[^|;&\n]*\s-[A-Za-z]*D|--full-time|--time-style|\bdate\s+-r\b", re.M)  # case-sensitive (Go os.Stat)

MT_VISIBLE = re.compile(r"\bls\b[^|;&\n]*\s-[A-Za-z]*l|\bfind\b[^|;&\n]*\s-ls\b|\bll\b")

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)

def strip_heredocs(c):
    """Drop heredoc bodies (file contents being written) so code inside them is not classified as a command."""
    return HEREDOC.sub("<<HEREDOC", c)

def late_files(tid):
    for l in open(f"{CUPEL_PHASE1}/results/tier_a.jsonl"):
        r = json.loads(l)
        if r["task_id"] == tid:
            return r["evidence"]["mtime"].get("late_files", []), r["cwd"]
    return [], None

def files_opened(cmds, cands, cwd):
    seen = []
    for c in cmds:
        for tok in re.split(r"[\s'\"=,:;|&<>()]+", c):
            t = tok
            if t.startswith(cwd + "/"):
                t = t[len(cwd) + 1:]
            t = t[2:] if t.startswith("./") else t
            if t in cands and t not in seen:
                seen.append(t)
    return seen

def classify(cmds):
    cmds = [strip_heredocs(c) for c in cmds]
    tg = [c for c in cmds if MT_TARGETED.search(c)]
    vis = [c for c in cmds if not MT_TARGETED.search(c) and MT_VISIBLE.search(c)]
    return {"mtime_targeted": bool(tg), "mtime_visible": bool(vis), "n_mtime_targeted_cmds": len(tg),
            "n_mtime_visible_cmds": len(vis), "mtime_targeted_cmds": [c[:300] for c in tg[:10]]}
