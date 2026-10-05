"""setup · doctor · install · make — getting from zero to a film."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from evofilm import __version__, agents, config, paths

FONTS = {
    "NotoSerifSC-VF.ttf": "notoserifsc/NotoSerifSC%5Bwght%5D.ttf",
    "NotoSansSC-VF.ttf": "notosanssc/NotoSansSC%5Bwght%5D.ttf",
    "InstrumentSerif-Regular.ttf": "instrumentserif/InstrumentSerif-Regular.ttf",
    "InstrumentSerif-Italic.ttf": "instrumentserif/InstrumentSerif-Italic.ttf",
    "Archivo-VF.ttf": "archivo/Archivo%5Bwdth,wght%5D.ttf",
}
FONT_BASE = "https://github.com/google/fonts/raw/main/ofl/"
SKILL_TARGETS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "agents": Path.home() / ".agents" / "skills",   # shared location read by several agent CLIs
}


def version_of(cmd, args=("--version",)):
    if not shutil.which(cmd):
        return None
    r = subprocess.run([cmd, *args], capture_output=True, text=True)
    return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else "?"


def cmd_setup(argv):
    ap = argparse.ArgumentParser(prog="evofilm setup", description="One-time setup: fonts, SFX library, HyperFrames CLI.")
    ap.add_argument("--fonts-from", default=None, help="copy font files from a local folder instead of downloading")
    a = ap.parse_args(argv)
    missing = [c for c in ("node", "npx", "ffmpeg", "ffprobe") if not shutil.which(c)]
    if missing:
        sys.exit(f"✗ missing: {', '.join(missing)} — macOS: brew install node ffmpeg · Ubuntu: apt install nodejs npm ffmpeg")
    node_major = int(re.search(r"v(\d+)", version_of("node")).group(1))
    if node_major < 20:
        print(f"⚠ node {node_major} — HyperFrames wants Node 22+")
    fdir = paths.fonts()
    fdir.mkdir(parents=True, exist_ok=True)
    for name, rel in FONTS.items():
        dst = fdir / name
        if dst.exists():
            continue
        if a.fonts_from and (Path(a.fonts_from) / name).exists():
            shutil.copyfile(Path(a.fonts_from) / name, dst)
            print(f"  font {name} (copied)")
            continue
        print(f"  font {name} (downloading, OFL) …", flush=True)
        with urllib.request.urlopen(FONT_BASE + rel, timeout=300) as r:
            dst.write_bytes(r.read())
    from evofilm.pipeline import sfx
    if not (paths.sfx_lib() / "whoosh.wav").exists():
        sfx.cmd_library()
    print(f"  hyperframes@{paths.HF_VERIFIED} (prefetch) …", flush=True)
    subprocess.run(["npx", "-y", f"hyperframes@{paths.HF_VERIFIED}", "--version"], capture_output=True)
    print(f"✓ evofilm {__version__} ready · home {paths.home()}\n  next: `evofilm install` (adds the skill to your agents), then ask your agent "
          f"\"/evofilm 做一个讲…的视频\" — or run `evofilm make \"…\"`")


def cmd_doctor(argv):
    from evofilm import llm
    from evofilm.rsi import lessons, lint
    ok = lambda b: "✓" if b else "✗"
    print(f"evofilm {__version__} · python {sys.version.split()[0]} · skill {paths.skill_dir()}")
    for c in ("node", "ffmpeg", "npx"):
        v = version_of(c, ("-version",) if c == "ffmpeg" else ("--version",))
        print(f"  {ok(v)} {c:8} {v or 'missing'}")
    fonts = [n for n in FONTS if (paths.fonts() / n).exists()]
    print(f"  {ok(len(fonts) == len(FONTS))} fonts    {len(fonts)}/{len(FONTS)} in {paths.fonts()}")
    print(f"  {ok((paths.sfx_lib() / 'whoosh.wav').exists())} sfx      {paths.sfx_lib()}")
    for name, root in SKILL_TARGETS.items():
        t = root / "evofilm"
        if t.exists() or t.is_symlink():
            print(f"  ✓ skill    installed for {name}: {t}")
    print("agents (harnesses that can direct a film):")
    for h in ("claude", "codex", "gemini", "opencode"):
        print(f"  {ok(shutil.which(h))} {h}")
    h, m = config.harness()
    print(f"models: harness={h} model={m}")
    for r in ("judge", "retro"):
        spec = config.role(r)
        good, why = llm.available(spec) if spec else (False, "none configured/detected")
        note = "  (login not checked — if calls fail, run `claude` once and /login)" if good and spec.startswith("claude-cli:") else ""
        print(f"  {ok(good)} {r:6} {spec or '-'}{'' if good else '  (' + why + ')'}{note}")
    print(f"self-improvement: {len(lint.load_rules())} rules · lessons "
          + " · ".join(f"{s} {len(lessons.all_lessons(s))}" for s in ("inbox", "accepted", "rejected")))


def cmd_install(argv):
    ap = argparse.ArgumentParser(prog="evofilm install", description="Install the EvoFilm skill into your agent(s).")
    ap.add_argument("--agent", default="auto", choices=["auto", "all", *SKILL_TARGETS])
    ap.add_argument("--copy", action="store_true", help="copy instead of symlink (symlinks follow upgrades)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    src = paths.skill_dir()
    if a.agent == "auto":
        names = [n for n, root in SKILL_TARGETS.items() if root.parent.exists()] or ["agents"]
    elif a.agent == "all":
        names = list(SKILL_TARGETS)
    else:
        names = [a.agent]
    for n in names:
        dst = SKILL_TARGETS[n] / "evofilm"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink():
            dst.unlink()
        elif dst.exists():
            if not a.force:
                print(f"  ⚠ {dst} exists (not a symlink) — skipped; --force to replace")
                continue
            shutil.rmtree(dst)
        if a.copy:
            shutil.copytree(src, dst)
        else:
            dst.symlink_to(src, target_is_directory=True)
        print(f"  ✓ {n}: {dst} → {src}")
    print("✓ done — in Claude Code: /evofilm 做一个讲…的视频 · in other agents: \"use the evofilm skill to make a video about …\"")


def cmd_make(argv):
    ap = argparse.ArgumentParser(prog="evofilm make", description="One sentence in, a rendered film out (headless agent).")
    ap.add_argument("topic")
    ap.add_argument("--dir", default=None, help="project directory (default videos/<slug>)")
    ap.add_argument("--length", type=int, default=60)
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16", "1:1"])
    ap.add_argument("--style", default="your choice")
    ap.add_argument("--quality", default="high", choices=["draft", "standard", "high"])
    ap.add_argument("--harness", default=None, help="claude | codex | gemini | opencode")
    ap.add_argument("--model", default=None, help="passed to the harness (e.g. opus, sonnet, gpt-5.1, deepseek/deepseek-chat)")
    ap.add_argument("--yes", action="store_true", help="skip the permission confirmation")
    a = ap.parse_args(argv)
    h, m = config.harness()
    harness, model = a.harness or h, a.model or m
    slug = re.sub(r"[^a-z0-9]+", "-", a.topic.lower()).strip("-")[:40] or f"film-{os.getpid()}"
    proj = Path(a.dir or f"videos/{slug}").resolve()
    if not a.yes:
        if not sys.stdin.isatty():
            sys.exit("✗ headless make runs an agent with full tool permissions in this folder — pass --yes")
        if input(f"{harness} ({model}) will work in {Path.cwd()} with full tool permissions. Continue? [y/N] ").lower() != "y":
            return
    prompt = agents.render_prompt("make", skill=paths.skill_dir(), topic=a.topic, length=a.length, aspect=a.aspect,
                                  style=a.style, dir=proj, quality=a.quality)
    print(f"▶ {harness} ({model}) is directing: {a.topic}\n  project: {proj}", flush=True)
    proj.parent.mkdir(parents=True, exist_ok=True)
    res = agents.run(harness, model, prompt, cwd=Path.cwd(), log_path=proj.parent / f"{proj.name}.make.log")
    print(res["tail"][-1200:])
    video = proj / "renders" / "video.mp4"
    print((f"✓ {video}" if video.exists() else "✗ no video produced — see the log")
          + f" · {res['seconds'] / 60:.1f} min" + (f" · ${res['cost_usd']:.2f}" if res.get("cost_usd") else ""))
