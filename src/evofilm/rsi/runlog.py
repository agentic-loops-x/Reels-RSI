"""The raw material of self-improvement: what happened on every pass over a film.

<project>/.evofilm/runs.jsonl      one JSON line per finalize / render / feedback / score event
<project>/.evofilm/history/NNN/    the frame + overlay HTML, STORYBOARD.md and SCRIPT.md as they
                                    were at finalize #NNN — so a retro can diff draft → final
"""

import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from evofilm.project import HF_SECTIONS, hf_findings, is_placeholder


def state(project) -> Path:
    d = Path(project) / ".evofilm"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read(project):
    p = state(project) / "runs.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]


def append(project, rec):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}
    with (state(project) / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def snapshot(project, n):
    project = Path(project)
    dst = state(project) / "history" / f"{n:03d}"
    if dst.exists():
        shutil.rmtree(dst)
    for rel in ["STORYBOARD.md", "SCRIPT.md", *[str(p.relative_to(project)) for p in project.glob("compositions/**/*.html")
                                                if p.name != "captions.html"], *[str(p.relative_to(project)) for p in project.glob("assets/*.js")]]:
        src = project / rel
        if src.exists():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst / rel)
    return dst


def record_finalize(project, report, findings):
    n = sum(1 for r in read(project) if r.get("event") == "finalize") + 1
    snapshot(project, n)
    hf_items = [{"section": sec, "code": f["code"], "severity": f["severity"],
                 "file": Path(f.get("sourceFile") or f.get("file") or "").name, "message": f.get("message", "")[:200]}
                for sec, f in hf_findings(report)]
    return append(project, {
        "event": "finalize", "n": n,
        "hf_ok": bool(report.get("ok")),
        "hf_errors": sum(1 for i in hf_items if i["severity"] == "error") + (1 if "crash" in report else 0),
        "hf_warnings": sum(1 for i in hf_items if i["severity"] == "warning"),
        "hf_findings": hf_items,
        "rules": [asdict(f) for f in findings],
        "frames": sum(1 for f in Path(project).glob("compositions/frames/*.html") if not is_placeholder(f)),
    })


__all__ = ["read", "append", "record_finalize", "snapshot", "HF_SECTIONS"]
