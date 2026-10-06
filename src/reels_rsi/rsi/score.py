"""Score a reel: deterministic signals + a vision judge on the quality-bar rubric (R1–R6).

    reels score <project> [--judge provider:model] [--no-judge]
    reels compare <projectA> <projectB> [--judge …]      blind pairwise preference (3 votes, order swapped)

composite = 0.6 · judge + 0.4 · deterministic   (deterministic only when no judge is available)

The judge never sees which skill version, model or run produced a reel. Scores land in
<project>/.reels/score.json and the run log — `bench` aggregates them, `evolve` compares them.
"""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from reels_rsi import config, llm
from reels_rsi.pipeline import frame_times
from reels_rsi.rsi import runlog

CRITERIA = ("R1", "R2", "R3", "R4", "R5", "R6")
RUBRIC = """R1 Hero richness — the hero visual is detailed, fills ~half the frame, would look good as a still
R2 Mechanism shown — the narration's cause→effect is visibly happening, not just labelled
R3 Camera & life — the three samples differ by camera position/motion, not only by added elements
R4 Pacing — the build-up is spread across the frame (30% sample is not empty, 92% is not identical to 60%)
R5 Composition — depth layers, clear hierarchy, nothing colliding with the captions, nothing clipped
R6 Consistency — palette/type coherent with the rest of the reel"""
# A worked problem is a teacher at a board: a still board is right, and "camera" means guiding the eye.
R3_SOLVE = ("R3 Guiding the eye — the step being spoken is singled out (highlight, colour, pointer, zoom on the "
            "region); earlier steps dim; each sample shows a clearly different step. A static board is fine")


def reel_mode(storyboard):
    from reels_rsi.project import reel_mode as mode
    return mode(storyboard)


def rubric(mode):
    return RUBRIC.replace(RUBRIC.splitlines()[2], R3_SOLVE) if mode == "solve" else RUBRIC


def layout_for(w, h):
    """Tile size and frames per sheet so a sheet stays near 4:3 — vision models downscale any image to
    ~1.5k px, and a 9:16 reel stacked four deep shrank each frame to ~200 px ("everything is tiny")."""
    if h > w:
        return "scale=-2:640", 2          # 360×640 tiles → 1080×1280 sheet
    if h == w:
        return "scale=480:-2", 3          # 1440×1440
    return "scale=640:-2", 4              # 1920×1440


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


def group_rows(rows, per_sheet):
    """Split rows into sheets; a lone last row reads as one wide frame, so it joins the previous sheet."""
    groups = [rows[i:i + per_sheet] for i in range(0, len(rows), per_sheet)]
    if len(groups) > 1 and len(groups[-1]) == 1:
        last = groups.pop()          # pop first: `groups[-2] += groups.pop()` indexes the shortened list
        groups[-1] += last
    return groups


def sample_sheets(project, out_dir, per_sheet=None):
    """Per frame a strip of 3 samples (30/60/92 %), stacked a few frames per image → [(path, [frame ids])]."""
    project = Path(project)
    from reels_rsi.project import canvas
    w, h = map(int, canvas((project / "STORYBOARD.md").read_text("utf-8")).split("x"))
    scale, per = layout_for(w, h)
    per_sheet = per_sheet or per
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
                                "-vf", scale, str(tile)], check=True)
            else:
                from reels_rsi.project import hf
                snap = project / "snapshots"
                hf(project, ["snapshot", "--at", f"{t:.2f}"], capture=True, check=False)
                pngs = sorted(snap.glob("frame-*.png"), key=lambda p: p.stat().st_mtime)
                if not pngs:
                    continue
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pngs[-1]), "-vf", scale, str(tile)], check=True)
            tiles.append(tile)
        if len(tiles) == 3:
            strip = out_dir / f"{fid}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(t)] for t in tiles), []),
                            "-filter_complex", "hstack=inputs=3", str(strip)], check=True)
            strips.append((fid, strip))
    groups = group_rows(strips, per_sheet)
    sheets = []
    for n, group in enumerate(groups, 1):
        sheet = out_dir / f"sheet-{n}.jpg"
        if len(group) == 1:
            sheet.write_bytes(group[0][1].read_bytes())
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(s)] for _, s in group), []),
                            "-filter_complex", f"vstack=inputs={len(group)}", str(sheet)], check=True)
        sheets.append((sheet, [fid for fid, _ in group]))
    return sheets


def storyboard_digest(project):
    sb = (Path(project) / "STORYBOARD.md").read_text("utf-8")
    from reels_rsi.project import split_frames
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
        sb = (Path(project) / "STORYBOARD.md").read_text("utf-8")
        from reels_rsi.project import band_top, canvas
        w, h = canvas(sb).split("x")
        mode = reel_mode(sb)
        kind = ("a worked-problem lesson on a board (judge it as teaching: clarity of each step beats spectacle)"
                if mode == "solve" else "a narrated explainer")
        prompt = f"""You are a strict reel critic scoring {kind}, made with code (HTML/SVG/canvas).
Canvas {w}×{h} ({"portrait 9:16 — judge the layout for a phone screen" if int(h) > int(w) else "landscape"}).
Captions are burned in the band below y={band_top(sb)} (the bottom 16.67 %); that band is reserved for them,
so content stopping above it is correct, not wasted space.
Each row of each image is ONE frame of the reel: three tiles, each the full {w}×{h} canvas scaled down,
sampled at 30%, 60% and 92% of its duration (left → right).
{layout}

What each frame is meant to show and say:
{storyboard_digest(project)}

Score every frame 1–5 on each criterion (5 = excellent, 3 = acceptable, 1 = broken):
{rubric(mode)}

Return JSON: {{"frames": [{{"id": "<frame id>", "R1": n, "R2": n, "R3": n, "R4": n, "R5": n, "R6": n, "note": "<the one fix that would raise this frame most>"}}],
"top_issues": ["<the 3 most important problems across the reel, concrete>"]}}"""
        return llm.complete_json(spec, prompt, images=[s for s, _ in sheets], max_tokens=6000)


def judge_score(j):
    vals = [float(f[c]) for f in j.get("frames", []) for c in CRITERIA if isinstance(f.get(c), (int, float))]
    return round(sum(vals) / len(vals) / 5 * 100, 1) if vals else None


def ensure_records(project):
    """Reels made before Reels-RSI (or by hand) have no run log yet — measure them once."""
    runs = runlog.read(project)
    if not any(r.get("event") == "finalize" for r in runs) and (project / "index.html").exists():
        from reels_rsi.project import hf_check
        from reels_rsi.rsi import lint
        runlog.record_finalize(project, hf_check(project), lint.lint_project(project))
    video = project / "renders" / "video.mp4"
    if not any(r.get("event") == "render" for r in runs) and video.exists():
        from reels_rsi.project import probe_duration
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


def compare(a, b, spec, votes=4, detail=False):
    """Blind pairwise: which of two reels on the same topic is better? Each vote sees both reels'
    sample sheets; the order alternates, and `votes` is rounded up to an even number so each reel is
    shown first exactly as often as second. Vision judges prefer the reel shown SECOND far more often
    than chance (in our reliability study sonnet picked the second-shown reel in 81 % of votes), so an
    odd vote count silently favours whichever reel takes the extra second slot. The judge is never told
    which version is which. Returns {"A": wins, "B": wins} (+ "why": [...] and "first": [...] with
    detail=True — `first[i]` is the side shown first on vote i)."""
    votes += votes % 2
    wins, why, first = {"A": 0, "B": 0}, [], []
    with tempfile.TemporaryDirectory() as tmp:
        sheets = {"A": sample_sheets(a, Path(tmp) / "a"), "B": sample_sheets(b, Path(tmp) / "b")}
        digest = {k: storyboard_digest(p) for k, p in (("A", a), ("B", b))}
        for v in range(votes):
            x, y = ("A", "B") if v % 2 == 0 else ("B", "A")
            ix, iy = [s for s, _ in sheets[x]], [s for s, _ in sheets[y]]
            prompt = f"""Two narrated explainer reels on the same topic, made independently. You see stills only.
Reel X = images 1–{len(ix)}; reel Y = images {len(ix) + 1}–{len(ix) + len(iy)}. In each image every row is one
frame of the reel, sampled at 30%, 60% and 92% of its duration (left → right). Captions sit in the bottom band.

Reel X — what each frame shows and says:
{digest[x]}

Reel Y — what each frame shows and says:
{digest[y]}

Which reel is better overall for a viewer who wants to understand the topic? Weigh:
{RUBRIC}
Judge the reels, not their length or number of frames.
Return JSON: {{"winner": "X" or "Y", "why": "one concrete sentence"}}"""
            j = llm.complete_json(spec, prompt, images=ix + iy)
            pick = x if str(j.get("winner", "")).strip().upper().startswith("X") else y
            wins[pick] += 1
            why.append(f"{'A' if pick == 'A' else 'B'}: {j.get('why', '')}")
            first.append(x)
    return {**wins, "why": why, "first": first} if detail else wins


def side_by_side(a, b, out):
    """One image for a human: reel A's frames (left) next to reel B's (right), for the evolve report."""
    def height(img):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height",
                            "-of", "csv=p=0", str(img)], capture_output=True, text=True)
        return int(r.stdout.strip() or 0)
    with tempfile.TemporaryDirectory() as tmp:
        cols = []
        for k, proj in (("a", a), ("b", b)):
            sheets = sample_sheets(proj, Path(tmp) / k, per_sheet=99)
            if not sheets:
                return None
            cols.append(sheets[0][0])
        h = max(height(c) for c in cols)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(cols[0]), "-i", str(cols[1]), "-filter_complex",
                        f"[0:v]pad=iw+40:{h}:0:0:white[l];[1:v]pad=iw:{h}:0:0:white[r];[l][r]hstack=inputs=2,"
                        "scale='min(2400,iw)':-2", "-q:v", "4", str(out)], check=False, capture_output=True)
    return out if Path(out).exists() else None


def cmd_score(argv):
    ap = argparse.ArgumentParser(prog="reels score", description="Score a finalized/rendered reel.")
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
    ap = argparse.ArgumentParser(prog="reels compare", description="Blind pairwise comparison of two versions of a reel.")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--judge", default=None)
    ap.add_argument("--votes", type=int, default=3)
    a = ap.parse_args(argv)
    spec = a.judge or config.role("judge")
    w = compare(a.a, a.b, spec, a.votes, detail=True)
    print(f"A ({a.a}) {w['A']} · B ({a.b}) {w['B']} → {'A' if w['A'] > w['B'] else 'B'} wins ({spec})")
    for line in w["why"]:
        print("  " + line)
