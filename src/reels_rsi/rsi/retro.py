"""Retro: turn one reel's history into lessons for every reel after it.

    reels retro <project>                  write .reels/retro/evidence.md and propose lessons with the
                                              retro model (config roles.retro) into ~/.reels/lessons/inbox/
    reels retro <project> --evidence-only  just the evidence — the agent directing the reel reads it and
                                              files lessons itself with `reels lessons add`

Evidence = what the checks caught on each finalize pass (and what got fixed between passes), how
each frame's code changed from first draft to final, everything the viewer said, and the judge's
notes. Fixed mistakes are the richest signal: each one cost a review round.
"""

import argparse
import difflib
import json
from pathlib import Path

from reels_rsi import agents, config, llm
from reels_rsi.rsi import lessons, lint, runlog

DIFF_BUDGET = 1600   # lines of diff in the evidence, across all files


def issue_keys(rec):
    return ({f"hyperframes/{i['section']}/{i['code']} ({i['file']})" for i in rec.get("hf_findings", [])}
            | {f"rule/{f['rule']} ({f['file']})" for f in rec.get("rules", [])})


def evidence(project):
    project = Path(project).resolve()
    runs = runlog.read(project)
    fins = [r for r in runs if r.get("event") == "finalize"]
    out = [f"# Retro evidence — {project.name}\n"]
    out.append(f"finalize passes: {len(fins)} · renders: {sum(1 for r in runs if r.get('event') == 'render')}\n")

    out.append("## Issues the checks caught, pass by pass\n")
    prev = set()
    for r in fins:
        cur = issue_keys(r)
        fixed, new = prev - cur, cur - prev
        out.append(f"### pass {r['n']} ({r['ts']}): {r.get('hf_errors', 0)} hyperframes errors, {r.get('hf_warnings', 0)} warnings, "
                   f"{len(r.get('rules', []))} rule findings")
        out += [f"- NEW {k}" for k in sorted(new)] + [f"- FIXED {k}" for k in sorted(fixed)]
        prev = cur
    if not fins:
        out.append("(no finalize passes recorded)")

    out.append("\n## The code changes that fixed them (pass → pass)\n")
    hist = sorted((runlog.state(project) / "history").glob("[0-9][0-9][0-9]"))
    fixed_at = {}
    prev = set()
    for r in fins:
        cur = issue_keys(r)
        fixed_at[r["n"]] = sorted(prev - cur)
        prev = cur
    budget = DIFF_BUDGET
    for older, newer in zip(hist, hist[1:]):
        n = int(newer.name)
        chunks = []
        for f in sorted(newer.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(newer)
            old = (older / rel).read_text("utf-8").splitlines() if (older / rel).exists() else []
            chunks += list(difflib.unified_diff(old, f.read_text("utf-8").splitlines(), f"pass{n - 1}/{rel}", f"pass{n}/{rel}", n=1, lineterm=""))
        if not chunks or budget <= 0:
            continue
        take = chunks[:min(len(chunks), 200, budget)]
        budget -= len(take)
        fixed = ", ".join(fixed_at.get(n, [])) or "nothing the checks flagged — a review/aesthetic change"
        out.append(f"### pass {n - 1} → {n} · fixed: {fixed}\n```diff\n" + "\n".join(take)
                   + ("\n… (truncated)" if len(take) < len(chunks) else "") + "\n```")
    if len(hist) < 2:
        out.append("(need ≥ 2 finalize passes)")

    out.append("\n## What the viewer said\n")
    fb = [r for r in runs if r.get("event") == "feedback"]
    out += [f"- {'APPROVED ' if r.get('approve') else ''}{('[' + r['frame'] + '] ') if r.get('frame') else ''}{r['text']}" for r in fb] or ["(nothing recorded)"]

    score_path = runlog.state(project) / "score.json"
    if score_path.exists():
        s = json.loads(score_path.read_text("utf-8"))
        out.append(f"\n## Judge ({s.get('judge_model') or 'not run'}) — composite {s.get('composite')}\n")
        for f in (s.get("judge") or {}).get("frames", []):
            low = [c for c in ("R1", "R2", "R3", "R4", "R5", "R6") if isinstance(f.get(c), (int, float)) and f[c] < 4]
            if low:
                out.append(f"- {f.get('id')}: low {', '.join(f'{c}={f[c]}' for c in low)} — {f.get('note', '')}")
        out += [f"- TOP ISSUE: {t}" for t in (s.get("judge") or {}).get("top_issues", [])]

    out.append("\n## Already known (do not propose these again)\n")
    out += [f"- lesson [{m.get('kind')}/{m.get('scope')}] {b[:140]}" for st, p, m, b in lessons.all_lessons("all")]
    out += [f"- rule {r.RULE['id']}: {r.RULE.get('lesson', '')[:140]}" for r in lint.load_rules()]
    path = runlog.state(project) / "retro" / "evidence.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", "utf-8")
    return path


def propose(project, spec, ev_path):
    from reels_rsi.project import reel_context
    reel = reel_context(project)
    prompt = agents.render_prompt("retro", evidence=ev_path.read_text("utf-8"),
                                  reel=", ".join(f"{k}={v}" for k, v in reel.items()))
    j = llm.complete_json(spec, prompt, max_tokens=4000)
    added = []
    for item in j.get("lessons", [])[:8]:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        p = lessons.add(text, item.get("kind", "doc") if item.get("kind") in lessons.KINDS else "doc",
                        item.get("scope", "all") if item.get("scope") in lessons.SCOPES else "all",
                        source=str(Path(project).resolve()), evidence=item.get("evidence", ""),
                        when=valid_when(item.get("when", "")))
        if p:
            added.append(p)
    return added


def valid_when(when):
    try:
        lessons.parse_when(when)
        return when
    except SystemExit:
        return ""                      # a model's malformed condition must not drop the lesson


def cmd_retro(argv):
    ap = argparse.ArgumentParser(prog="reels retro", description="Distil a reel's history into proposed lessons.")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--evidence-only", action="store_true")
    ap.add_argument("--model", default=None, help="provider:model (default: config roles.retro)")
    a = ap.parse_args(argv)
    ev = evidence(a.project)
    print(f"✓ evidence → {ev}")
    if a.evidence_only:
        return
    spec = a.model or config.role("retro")
    if not spec:
        print("no retro model configured — read the evidence and file lessons with `reels lessons add`")
        return
    added = propose(a.project, spec, ev)
    print(f"✓ {len(added)} lesson(s) proposed → review with `reels lessons list --state inbox`, then accept/reject")
