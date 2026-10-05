"""Project lifecycle: new → packets → finalize → render, plus hf / concat / analyze.

These are the deterministic steps. No model is involved here — any agent (or a human) runs them.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from evofilm import __version__, paths
from evofilm.pipeline import frame_times


def run(cmd, cwd=None, check=True, capture=False):
    return subprocess.run([str(c) for c in cmd], cwd=cwd, check=check, text=True,
                          capture_output=capture)


def node(script, *args, cwd=None, capture=False):
    return run(["node", paths.VENDOR / script, *args], cwd=cwd, capture=capture)


def hf_version(project) -> str:
    try:
        scripts = json.loads((Path(project) / "package.json").read_text("utf-8")).get("scripts", {})
        m = re.search(r"hyperframes@([0-9][^ \"]*)", json.dumps(scripts))
        if m:
            return m.group(1)
    except (OSError, ValueError):
        pass
    return paths.HF_VERIFIED


def hf(project, args, capture=False, check=True):
    """Run the HyperFrames CLI at the version the project pins (reproducible renders)."""
    return run(["npx", "-y", f"hyperframes@{hf_version(project)}", *args], cwd=project, capture=capture, check=check)


# ── new ──────────────────────────────────────────────────────────────────────
def preset_dir(name):
    if (paths.PRESETS / name / "FRAME.md").exists():
        return paths.PRESETS
    for root in (Path.home() / ".claude/skills", Path.home() / ".agents/skills"):
        d = root / "hyperframes-creative" / "frame-presets"
        if (d / name).exists():
            return d
    ours = ", ".join(sorted(p.name for p in paths.PRESETS.iterdir() if p.is_dir()))
    raise SystemExit(f"✗ unknown preset '{name}'. EvoFilm presets: {ours}. Official HyperFrames presets "
                     f"need `npx hyperframes skills update hyperframes-creative` first.")


def cmd_new(argv):
    ap = argparse.ArgumentParser(prog="evofilm new", description="Scaffold a film project.")
    ap.add_argument("dir")
    ap.add_argument("--preset", default="deepspace")
    ap.add_argument("--title", default="")
    ap.add_argument("--desc", default="")
    a = ap.parse_args(argv)
    target = Path(a.dir)
    if (target / "hyperframes.json").exists():
        sys.exit(f"✗ {target} already is a project")
    pdir = preset_dir(a.preset)
    if not (paths.fonts() / "NotoSansSC-VF.ttf").exists():
        print("⚠ fonts not installed yet — run `evofilm setup` before finalize")
    base = ["--non-interactive", "--example=blank", "--skill=faceless-explainer"]
    if run(["npx", "-y", "hyperframes@latest", "init", target, *base], check=False, capture=True).returncode:
        shutil.rmtree(target, ignore_errors=True)
        run(["npx", "-y", f"hyperframes@{paths.HF_VERIFIED}", "init", target, *base], capture=True)
    target = target.resolve()
    (target / "capture/extracted").mkdir(parents=True, exist_ok=True)
    (target / "assets/music").mkdir(parents=True, exist_ok=True)
    (target / "capture/extracted/tokens.json").write_text(
        json.dumps({"title": a.title, "description": a.desc, "colors": [], "fonts": []}, ensure_ascii=False), "utf-8")
    vt = target / "capture/extracted/visible-text.txt"
    if not vt.exists():
        vt.write_text(f"{a.title}\n{a.desc}\n", "utf-8")
    node("build-frame.mjs", "--preset", a.preset, "--preset-dir", pdir, "--hyperframes", target)
    state = target / ".evofilm"
    state.mkdir(exist_ok=True)
    (state / "project.json").write_text(json.dumps({
        "evofilm": __version__, "preset": a.preset, "title": a.title,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2), "utf-8")
    print(f"✓ project ready: {target} · preset {a.preset} · hyperframes@{hf_version(target)}")


# ── packets: one self-contained brief per frame for parallel frame workers ───
def split_frames(storyboard):
    heads = list(re.finditer(r"^## Frame\s+([^\n]+)$", storyboard, re.M))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(storyboard)
        block = storyboard[m.start():end].strip()
        src = re.search(r"^-\s+src:\s*(\S+)", block, re.M)
        num = re.match(r"(\d+)", m.group(1).strip())
        yield (int(num.group(1)) if num else i + 1), (Path(src.group(1)).stem if src else None), block


def canvas(storyboard):
    m = re.search(r"^format:\s*(\S+)", storyboard, re.M)
    fmt = (m.group(1) if m else "1920x1080").lower()
    return {"9:16": "1080x1920", "1:1": "1080x1080", "16:9": "1920x1080"}.get(fmt, fmt if "x" in fmt else "1920x1080")


def band_top(storyboard):
    """Top of the caption band — HyperFrames reserves the bottom 16.67 % of the canvas."""
    h = int(canvas(storyboard).split("x")[1])
    return h - round(h * 0.1667)


def cmd_packets(argv):
    ap = argparse.ArgumentParser(prog="evofilm packets", description="Write per-frame worker packets.")
    ap.add_argument("--project", default=".")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    sb = (project / "STORYBOARD.md").read_text("utf-8")
    direction = re.search(r"^## Video direction\n(.*?)(?=^## Frame)", sb, re.M | re.S)
    meta = json.loads((project / "audio_meta.json").read_text("utf-8")) if (project / "audio_meta.json").exists() else {}
    words = {v["frame"]: v.get("words", []) for v in meta.get("voices", [])}
    out = project / ".evofilm" / "packets"
    out.mkdir(parents=True, exist_ok=True)
    skill = paths.skill_dir()
    from evofilm.rsi import lessons
    digest = lessons.digest(scope="frame")
    (out / "_role.md").write_text(f"""# Role: frame worker (EvoFilm)

You build exactly one HyperFrames frame: `compositions/frames/<frame_id>.html` in {project}.
Read, in order:
1. {skill}/references/frame-worker.md — non-negotiables, shot skeleton, verified patterns
2. {skill}/references/quality-bar.md — the rubric your frame is scored on
3. {project}/frame.md — the design system (palette, type, motion grammar)
4. the recipe your packet's `route:` points to ({skill}/references/styles.md · history.md · solve.md · techniques.md)
5. your packet `<frame_id>.md` in this folder

Canvas {canvas(sb)} · captions enabled: keep text out of the caption band (y > {band_top(sb)} on this canvas)
· if the storyboard plans an overlay, keep out of its band too.
Cue every reveal to the spoken word times in your packet. Write only your frame file, then run
`evofilm lint --project {project} --frame <frame_id>` and fix everything it reports.
Reply with one line describing the hero visual.
{digest}""", "utf-8")
    n = 0
    for num, fid, block in split_frames(sb):
        if not fid:
            continue
        timing = " ".join(f'{w["text"]}@{w["start"]:.2f}' for w in words.get(num, []))
        (out / f"{fid}.md").write_text(
            f"# Frame packet: {fid}\n\n- Project: {project}\n- Canvas: {canvas(sb)}\n"
            f"- Design tokens: {project / 'frame.md'}\n\n"
            + (f"## Video direction (film-wide)\n\n{direction.group(1).strip()}\n\n" if direction else "")
            + f"## Your storyboard block\n\n{block}\n\n"
            + (f"## Spoken words (seconds from frame start)\n\n{timing}\n" if timing else ""), "utf-8")
        n += 1
    print(f"✓ packets: {n} frames → {out}")


# ── finalize ─────────────────────────────────────────────────────────────────
def step(name):
    print(f"── {name}", flush=True)


def cmd_finalize(argv):
    ap = argparse.ArgumentParser(prog="evofilm finalize",
                                 description="fonts → captions → music → sfx → assemble → overlays → transitions → lint → check → srt → snapshots")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--no-snapshot", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    from evofilm.pipeline import captions_cjk, fonts, music, overlays, sfx, srt
    from evofilm.rsi import lint, runlog

    step("fonts"); fonts.main(["--project", str(project)])
    step("captions"); captions_cjk.main(["--project", str(project)])
    step("music")
    meta = json.loads((project / "audio_meta.json").read_text("utf-8"))
    if (meta.get("bgm") or {}).get("path") == "assets/bgm/bed.wav":
        music.main(["--project", str(project)])
    else:
        print("  (user track or none — unchanged)")
    step("sfx"); sfx.main(["cues", "--project", str(project)])
    step("assemble")
    r = node("assemble-index.mjs", "--storyboard", "./STORYBOARD.md", "--hyperframes", ".", cwd=project, capture=True)
    print("\n".join(l for l in r.stdout.splitlines() if re.search(r"total duration|anomal|skipped|frames|voice|bgm|captions|sfx", l)))
    index = project / "index.html"
    s = index.read_text("utf-8")
    if 'id="el-captions"' in s and 'data-track-kind="captions"' not in s:   # assembler omits the captions track kind
        index.write_text(re.sub(r'(\n(\s*)id="el-captions")', r'\1\n\2data-track-kind="captions"', s, count=1), "utf-8")
    step("overlays"); overlays.main(["--project", str(project)])
    step("transitions")
    tr = node("transitions.mjs", "inject", "--storyboard", "./STORYBOARD.md", "--hyperframes", ".", cwd=project, capture=True)
    print("\n".join(tr.stdout.strip().splitlines()[-1:]))
    node("transitions.mjs", "verify", "--storyboard", "./STORYBOARD.md", "--index", "./index.html", cwd=project)

    step("check (hyperframes lint · runtime · layout · contrast)")
    report = hf_check(project)
    print_check(report)
    step("lint (evofilm rules)")
    findings = lint.lint_project(project)
    lint.print_findings(findings)
    step("subtitles"); srt.main(["--project", str(project)])
    if not a.no_snapshot:
        step("snapshots")
        shutil.rmtree(project / "snapshots", ignore_errors=True)
        times = ",".join(f"{t:.2f}" for t in frame_times.sample_times(project))
        sr = hf(project, ["snapshot", "--at", times], capture=True, check=False)
        print("\n".join([l for l in (sr.stdout + sr.stderr).splitlines() if re.search(r"contact-sheet|frame-", l)][-3:]))
        print(f"   review: {project}/snapshots/contact-sheet.jpg (3 samples per frame: 30% · 60% · 92%)")
    rec = runlog.record_finalize(project, report, findings)
    print(f"✓ finalize #{rec['n']}: hyperframes {rec['hf_errors']} error(s) / {rec['hf_warnings']} warning(s) · "
          f"evofilm rules {len(findings)} finding(s)")


HF_SECTIONS = ("lint", "runtime", "layout", "motion", "contrast")


def hf_check(project) -> dict:
    """`hyperframes check --json` (lint + runtime + layout + contrast in one browser pass)."""
    r = hf(project, ["check", "--json"], capture=True, check=False)
    try:
        return json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        return {"ok": False, "crash": (r.stdout + r.stderr)[-2000:]}


def hf_findings(report):
    for sec in HF_SECTIONS:
        for f in (report.get(sec) or {}).get("findings", []):
            if f.get("severity") in ("error", "warning"):
                yield sec, f


def print_check(report):
    if "crash" in report:
        print("✗ hyperframes check crashed:\n" + report["crash"])
        return
    for sec, f in hf_findings(report):
        mark = "✗" if f["severity"] == "error" else "⚠"
        where = Path(f.get("sourceFile") or f.get("file") or "").name
        at = f" @{f['time']:.2f}s" if f.get("time") else ""
        print(f"  {mark} {sec}/{f['code']} {where}{at}: {f.get('message', '')[:140]}")
    print("  check " + ("passed" if report.get("ok") else "FAILED"))


# ── render ───────────────────────────────────────────────────────────────────
def cmd_render(argv):
    ap = argparse.ArgumentParser(prog="evofilm render")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--quality", default="high", choices=["draft", "standard", "high"])
    ap.add_argument("--output", default="renders/video.mp4")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    t0 = time.time()
    r = hf(project, ["render", "--skill=faceless-explainer", "--quality", a.quality, "--output", a.output],
           capture=True, check=False)
    print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if re.search(r"◇|MB|rendered in|rror", l)))
    out = project / a.output
    from evofilm.rsi import runlog
    if not out.exists():
        runlog.append(project, {"event": "render", "ok": False, "seconds": round(time.time() - t0, 1)})
        sys.exit("✗ render produced no file")
    dur = probe_duration(out)
    runlog.append(project, {"event": "render", "ok": True, "seconds": round(time.time() - t0, 1),
                            "duration_s": dur, "quality": a.quality, "bytes": out.stat().st_size})
    vol = run(["ffmpeg", "-hide_banner", "-i", out, "-af", "volumedetect", "-vn", "-f", "null", "-"],
              capture=True, check=False).stderr
    print("  " + " · ".join(re.findall(r"(?:mean|max)_volume: [-\d.]+ dB", vol)))
    print(f"✓ {out} · {dur:.1f}s · {out.stat().st_size / 1e6:.1f} MB")


def probe_duration(path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture=True)
    return round(float(r.stdout.strip()), 2)


# ── concat (chapters) ────────────────────────────────────────────────────────
def shift_srt(text, offset, start_idx):
    def shift(m):
        h, mi, s, ms = map(int, m.groups())
        t = int(round((h * 3600 + mi * 60 + s + ms / 1000 + offset) * 1000))
        h, r = divmod(t, 3600000); mi, r = divmod(r, 60000); s, ms = divmod(r, 1000)
        return f"{h:02d}:{mi:02d}:{s:02d},{ms:03d}"
    out, idx = [], start_idx
    for b in text.strip().split("\n\n"):
        lines = b.split("\n")
        if len(lines) < 2:
            continue
        stamp = re.sub(r"(\d+):(\d+):(\d+),(\d+)", shift, lines[1])
        out.append(f"{idx}\n{stamp}\n" + "\n".join(lines[2:]) + "\n")
        idx += 1
    return "\n".join(out), idx


def cmd_concat(argv):
    ap = argparse.ArgumentParser(prog="evofilm concat", description="Join rendered chapter projects into one film.")
    ap.add_argument("output")
    ap.add_argument("chapters", nargs="+")
    a = ap.parse_args(argv)
    out = Path(a.output).resolve()
    srt_parts, offset, idx = [], 0.0, 1
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for d in a.chapters:
            v = Path(d).resolve() / "renders" / "video.mp4"
            if not v.exists():
                sys.exit(f"✗ missing {v}")
            lst.write(f"file '{v}'\n")
            sub = Path(d) / "renders" / "subtitles.srt"
            if sub.exists():
                text, idx = shift_srt(sub.read_text("utf-8"), offset, idx)
                srt_parts.append(text)
            offset += probe_duration(v)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, "-c:v", "libx264", "-crf", "18",
         "-preset", "medium", "-c:a", "aac", "-b:a", "192k", out])
    Path(lst.name).unlink()
    if srt_parts:
        out.with_suffix(".srt").write_text("\n".join(srt_parts), "utf-8")
    print(f"✓ {out} ({offset:.1f}s)")


# ── analyze a reference video ────────────────────────────────────────────────
def cmd_analyze(argv):
    ap = argparse.ArgumentParser(prog="evofilm analyze",
                                 description="Study a reference video: cuts, pacing, contact sheet. Match its style, never its content.")
    ap.add_argument("video")
    ap.add_argument("out", nargs="?", default="reference-analysis")
    ap.add_argument("--threshold", type=float, default=0.3)
    a = ap.parse_args(argv)
    out = Path(a.out)
    shutil.rmtree(out / "frames", ignore_errors=True)
    (out / "frames").mkdir(parents=True)
    dur = probe_duration(a.video)
    info = run(["ffmpeg", "-v", "info", "-i", a.video, "-vf", f"select='gt(scene,{a.threshold})',showinfo",
                "-vsync", "vfr", "-f", "null", "-"], capture=True, check=False).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", info)]
    (out / "shots.txt").write_text("\n".join(f"{c:.2f}" for c in cuts), "utf-8")
    soft = len(cuts) < max(3, dur / 20)   # crossfades/pushes hide cuts → sample evenly
    if soft:
        stepv = max(1.5, dur / 36)
        mids = [round(stepv / 2 + i * stepv, 2) for i in range(int(dur // stepv))]
    else:
        b = [0.0] + cuts + [dur]
        mids = [(b[i] + b[i + 1]) / 2 for i in range(len(b) - 1)]
    mids = mids[::max(1, len(mids) // 48)][:48]
    for i, t in enumerate(mids, 1):
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1", "-vf", "scale=480:-2",
             out / "frames" / f"{i:03d}_{t:.2f}s.jpg"])
    rows = (len(mids) + 5) // 6
    run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", f"{out}/frames/*.jpg", "-vf",
         f"tile=6x{rows}:padding=6:color=black", "-frames:v", "1", out / "contact.jpg"])
    loud = re.search(r"mean_volume: [-\d.]+ dB", run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "volumedetect",
                                                     "-vn", "-f", "null", "-"], capture=True, check=False).stderr)
    stats = (f"duration: {dur:.1f}s\nhard cuts detected: {len(cuts)}\navg shot length: {dur / (len(cuts) + 1):.2f}s\n"
             f"cuts per minute: {len(cuts) / dur * 60:.1f}\n{loud.group(0) if loud else 'no audio'}\n")
    if soft:
        stats += "note: few hard cuts — likely soft transitions; contact sheet sampled evenly, judge pacing from it\n"
    (out / "stats.txt").write_text(stats, "utf-8")
    print(stats + f"✓ {out}/contact.jpg ({len(mids)} samples)")


def cmd_hf(argv):
    ap = argparse.ArgumentParser(prog="evofilm hf", description="Run the project-pinned HyperFrames CLI.")
    ap.add_argument("--project", default=".")
    a, rest = ap.parse_known_args(argv)
    sys.exit(hf(Path(a.project).resolve(), rest, check=False).returncode)
