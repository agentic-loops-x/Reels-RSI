"""Score a film: deterministic signals + a vision judge on the quality-bar rubric (R1–R6).

    takeloop score <project> [--judge provider:model] [--no-judge]
    takeloop compare <projectA> <projectB> [--judge …]      blind pairwise preference (3 votes, order swapped)

composite = 0.6 · judge + 0.4 · deterministic   (deterministic only when no judge is available)

The judge never sees which skill version, model or run produced a film. Scores land in
<project>/.takeloop/score.json and the run log — `bench` aggregates them, `evolve` compares them.
"""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from takeloop import config, llm
from takeloop.pipeline import frame_times
from takeloop.rsi import runlog

CRITERIA = ("R1", "R2", "R3", "R4", "R5", "R6")
RUBRIC = """R1 Hero richness — the hero visual is detailed, fills ~half the frame, would look good as a still
R2 Mechanism shown — the narration's cause→effect is visibly happening, not just labelled
R3 Camera & life — the three samples differ by camera position/motion, not only by added elements
R4 Pacing — the build-up is spread across the frame (30% sample is not empty, 92% is not identical to 60%)
R5 Composition — depth layers, clear hierarchy, nothing colliding with the captions, nothing clipped
R6 Consistency — palette/type coherent with the rest of the film"""


def target_seconds(storyboard):
    m = re.search(r"^duration:\s*([\d.]+)", storyboard, re.M)
    return float(m.group(1)) if m else None


def deterministic(project):
    project = Path(project)
    runs = runlog.read(project)
    fin = next((r for r in reversed(runs) if r.get("event") == "finalize"), None)
    ren = next((r for r in reversed(runs) if r.get("event") == "render"), None)
    sb = (project / "STORYBOARD.md").read_text("utf-8") if (project / "STORYBOARD.md").exists() else ""
    m = {"rendered": bool(ren and ren.get("ok")), "duration_s": (ren or {}).get("duration_s"),
         "target_s": target_seconds(sb), "frames": (fin or {}).get("frames", 0),
         "finalize_passes": sum(1 for r in runs if r.get("event") == "finalize"),
         "hf_errors": (fin or {}).get("hf_errors", 0), "hf_warnings": (fin or {}).get("hf_warnings", 0),
         "rule_errors": sum(1 for f in (fin or {}).get("rules", []) if f["severity"] == "error"),
         "rule_warnings": sum(1 for f in (fin or {}).get("rules", []) if f["severity"] == "warning")}
    if not fin:
        return m, 0.0
    s = 100.0
    s -= min(45, 15 * m["hf_errors"]) + min(15, 3 * m["hf_warnings"])
    s -= min(30, 10 * m["rule_errors"]) + min(10, 2 * m["rule_warnings"])
    if not m["rendered"]:
        s -= 40
    if m["duration_s"] and m["target_s"]:
        m["duration_err"] = round(abs(m["duration_s"] - m["target_s"]) / m["target_s"], 3)
        s -= 10 if m["duration_err"] > 0.15 else 0
    if m["duration_s"] and m["frames"]:
        m["avg_shot_s"] = round(m["duration_s"] / m["frames"], 2)
        s -= 5 if not 2.5 <= m["avg_shot_s"] <= 10 else 0
    return m, max(0.0, s)


def sample_sheets(project, out_dir, per_sheet=4):
    """Per frame a strip of 3 samples (30/60/92 %), stacked 4 frames per image → [(path, [frame ids])]."""
    project = Path(project)
    hosts = frame_times.hosts((project / "index.html").read_text("utf-8"))
    video = project / "renders" / "video.mp4"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    strips = []
    for fid, start, dur in hosts:
        tiles = []
        for k, f in enumerate((0.3, 0.6, 0.92)):
            t = start + dur * f
            tile = out_dir / f"{fid}-{k}.jpg"
            if video.exists():
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                                "-vf", "scale=640:-2", str(tile)], check=True)
            else:
                from takeloop.project import hf
                snap = project / "snapshots"
                hf(project, ["snapshot", "--at", f"{t:.2f}"], capture=True, check=False)
                pngs = sorted(snap.glob("frame-*.png"), key=lambda p: p.stat().st_mtime)
                if not pngs:
                    continue
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pngs[-1]), "-vf", "scale=640:-2", str(tile)], check=True)
            tiles.append(tile)
        if len(tiles) == 3:
            strip = out_dir / f"{fid}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(t)] for t in tiles), []),
                            "-filter_complex", "hstack=inputs=3", str(strip)], check=True)
            strips.append((fid, strip))
    sheets = []
    for i in range(0, len(strips), per_sheet):
        group = strips[i:i + per_sheet]
        sheet = out_dir / f"sheet-{i // per_sheet + 1}.jpg"
        if len(group) == 1:
            sheet.write_bytes(group[0][1].read_bytes())
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(s)] for _, s in group), []),
                            "-filter_complex", f"vstack=inputs={len(group)}", str(sheet)], check=True)
        sheets.append((sheet, [fid for fid, _ in group]))
    return sheets


def storyboard_digest(project):
    sb = (Path(project) / "STORYBOARD.md").read_text("utf-8")
    from takeloop.project import split_frames
    rows = []
    for num, fid, block in split_frames(sb):
        scene = re.search(r"^-\s+scene:\s*(.+)$", block, re.M)
        vo = re.search(r"^-\s+voiceover:\s*(.+)$", block, re.M)
        rows.append(f"- {fid}: {(scene.group(1) if scene else '')[:160]} | says: {(vo.group(1) if vo else '')[:160]}")
    return "\n".join(rows)


def judge(project, spec):
    with tempfile.TemporaryDirectory() as tmp:
        sheets = sample_sheets(project, tmp)
        if not sheets:
            raise llm.LLMError("no frames to judge (finalize first)")
        layout = "\n".join(f"- image {i + 1}: rows top→bottom = {', '.join(ids)}" for i, (_, ids) in enumerate(sheets))
        prompt = f"""You are a strict film critic scoring a narrated explainer video made with code (HTML/SVG/canvas).
Each row of each image is ONE frame of the film, sampled at 30%, 60% and 92% of its duration (left → right).
{layout}

What each frame is meant to show and say:
{storyboard_digest(project)}

Score every frame 1–5 on each criterion (5 = excellent, 3 = acceptable, 1 = broken):
{RUBRIC}

Return JSON: {{"frames": [{{"id": "<frame id>", "R1": n, "R2": n, "R3": n, "R4": n, "R5": n, "R6": n, "note": "<the one fix that would raise this frame most>"}}],
"top_issues": ["<the 3 most important problems across the film, concrete>"]}}"""
        return llm.complete_json(spec, prompt, images=[s for s, _ in sheets], max_tokens=6000)


def judge_score(j):
    vals = [float(f[c]) for f in j.get("frames", []) for c in CRITERIA if isinstance(f.get(c), (int, float))]
    return round(sum(vals) / len(vals) / 5 * 100, 1) if vals else None


def ensure_records(project):
    """Films made before TakeLoop (or by hand) have no run log yet — measure them once."""
    runs = runlog.read(project)
    if not any(r.get("event") == "finalize" for r in runs) and (project / "index.html").exists():
        from takeloop.project import hf_check
        from takeloop.rsi import lint
        runlog.record_finalize(project, hf_check(project), lint.lint_project(project))
    video = project / "renders" / "video.mp4"
    if not any(r.get("event") == "render" for r in runs) and video.exists():
        from takeloop.project import probe_duration
        runlog.append(project, {"event": "render", "ok": True, "duration_s": probe_duration(video), "imported": True})


def score(project, spec=None, use_judge=True):
    project = Path(project).resolve()
    ensure_records(project)
    det, det_s = deterministic(project)
    res = {"deterministic": det, "det_score": round(det_s, 1), "judge": None, "judge_score": None, "judge_model": None}
    spec = spec or (config.role("judge") if use_judge else None)
    if use_judge and spec and (project / "index.html").exists():
        try:
            j = judge(project, spec)
            res.update(judge=j, judge_score=judge_score(j), judge_model=spec)
        except (llm.LLMError, subprocess.CalledProcessError, ValueError) as e:
            res["judge_error"] = str(e)[:500]
    res["composite"] = round(0.6 * res["judge_score"] + 0.4 * det_s, 1) if res["judge_score"] is not None else round(det_s, 1)
    (runlog.state(project) / "score.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
    runlog.append(project, {"event": "score", "composite": res["composite"], "det_score": res["det_score"],
                            "judge_score": res["judge_score"], "judge_model": res["judge_model"]})
    return res


def print_score(res):
    d = res["deterministic"]
    print(f"deterministic {res['det_score']}/100 · rendered={d['rendered']} · hyperframes {d['hf_errors']}E/{d['hf_warnings']}W"
          f" · rules {d['rule_errors']}E/{d['rule_warnings']}W · frames {d['frames']} · passes {d['finalize_passes']}"
          + (f" · {d['duration_s']}s vs {d['target_s']}s" if d.get("duration_s") else ""))
    if res.get("judge"):
        print(f"judge ({res['judge_model']}) {res['judge_score']}/100")
        for f in res["judge"].get("frames", []):
            print(f"  {f.get('id', '?'):18} " + " ".join(f"{c}={f.get(c, '-')}" for c in CRITERIA) + f"  · {f.get('note', '')[:90]}")
        for t in res["judge"].get("top_issues", []):
            print(f"  ! {t}")
    elif res.get("judge_error"):
        print(f"judge failed: {res['judge_error']}")
    print(f"composite {res['composite']}/100")


def compare(a, b, spec, votes=3):
    """Blind pairwise: which film is better? Order alternates between votes; returns wins per side."""
    wins = {"A": 0, "B": 0}
    with tempfile.TemporaryDirectory() as tmp:
        sa = sample_sheets(a, Path(tmp) / "a", per_sheet=99)
        sb = sample_sheets(b, Path(tmp) / "b", per_sheet=99)
        for v in range(votes):
            first, second = (("A", sa), ("B", sb)) if v % 2 == 0 else (("B", sb), ("A", sa))
            prompt = ("Two versions of the same narrated explainer film, each shown as one image whose rows are its frames "
                      "(30/60/92% samples left→right). Image 1 is film X, image 2 is film Y. Which is the better film overall — "
                      "richer visuals, clearer mechanism, livelier camera, better pacing and composition?\n"
                      f"{RUBRIC}\nReturn JSON: {{\"winner\": \"X\" or \"Y\", \"why\": \"one sentence\"}}")
            j = llm.complete_json(spec, prompt, images=[first[1][0][0], second[1][0][0]])
            pick = first[0] if str(j.get("winner", "")).upper().startswith("X") else second[0]
            wins[pick] += 1
    return wins


def cmd_score(argv):
    ap = argparse.ArgumentParser(prog="takeloop score", description="Score a finalized/rendered film.")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--judge", default=None, help="provider:model (default: config roles.judge or auto-detect)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = score(a.project, a.judge, not a.no_judge)
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else "", end="")
    if not a.json:
        print_score(res)


def cmd_compare(argv):
    ap = argparse.ArgumentParser(prog="takeloop compare", description="Blind pairwise comparison of two versions of a film.")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--judge", default=None)
    ap.add_argument("--votes", type=int, default=3)
    a = ap.parse_args(argv)
    spec = a.judge or config.role("judge")
    w = compare(a.a, a.b, spec, a.votes)
    print(f"A ({a.a}) {w['A']} · B ({a.b}) {w['B']} → {'A' if w['A'] > w['B'] else 'B'} wins ({spec})")
