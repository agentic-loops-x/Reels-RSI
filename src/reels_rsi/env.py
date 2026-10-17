"""setup · doctor · install · make — getting from zero to a reel."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from reels_rsi import __version__, agents, config, paths

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
    ap = argparse.ArgumentParser(prog="reels setup", description="One-time setup: fonts, SFX library, HyperFrames CLI.")
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
    from reels_rsi.pipeline import sfx
    if not (paths.sfx_lib() / "whoosh.wav").exists():
        sfx.cmd_library()
    print(f"  hyperframes@{paths.HF_VERIFIED} (prefetch) …", flush=True)
    subprocess.run(["npx", "-y", f"hyperframes@{paths.HF_VERIFIED}", "--version"], capture_output=True)
    print(f"✓ reels {__version__} ready · home {paths.home()}\n  next: `reels install` (adds the skill to your agents), then ask your agent "
          f"\"/reels 做一个讲…的视频\" — or run `reels make \"…\"`")


def cmd_doctor(argv):
    from reels_rsi import llm
    from reels_rsi.rsi import lessons, lint
    ok = lambda b: "✓" if b else "✗"
    print(f"reels {__version__} · python {sys.version.split()[0]} · skill {paths.skill_dir()}")
    for c in ("node", "ffmpeg", "npx"):
        v = version_of(c, ("-version",) if c == "ffmpeg" else ("--version",))
        print(f"  {ok(v)} {c:8} {v or 'missing'}")
    pop = shutil.which("pdftotext") and shutil.which("pdfimages") and shutil.which("pdftoppm")
    print(f"  {ok(pop)} poppler  {'pdftotext · pdfimages · pdftoppm' if pop else 'missing — `reels paper` (PDF / arXiv → reel) needs it: brew install poppler'}")
    fonts = [n for n in FONTS if (paths.fonts() / n).exists()]
    print(f"  {ok(len(fonts) == len(FONTS))} fonts    {len(fonts)}/{len(FONTS)} in {paths.fonts()}")
    print(f"  {ok((paths.sfx_lib() / 'whoosh.wav').exists())} sfx      {paths.sfx_lib()}")
    for name, root in SKILL_TARGETS.items():
        t = root / "reels"
        if t.exists() or t.is_symlink():
            print(f"  ✓ skill    installed for {name}: {t}")
    print("agents (harnesses that can direct a reel):")
    for h in ("claude", "codex", "gemini", "opencode"):
        note = ""
        if h == "claude" and shutil.which(h):
            good, why = agents.claude_login()
            note = f"  ({why})"
            print(f"  {ok(good)} {h}{note}")
            continue
        print(f"  {ok(shutil.which(h))} {h}")
    h, m = config.harness()
    print(f"models: harness={h} model={m}")
    for r in ("judge", "retro"):
        spec = config.role(r)
        good, why = llm.available(spec) if spec else (False, "none configured/detected")
        print(f"  {ok(good)} {r:6} {spec or '-'}{'' if good else '  (' + why + ')'}")
    print(f"self-improvement: {len(lint.load_rules())} rules · lessons "
          + " · ".join(f"{s} {len(lessons.all_lessons(s))}" for s in ("inbox", "accepted", "rejected")))
    todo = []
    if len(fonts) < len(FONTS) or not (paths.sfx_lib() / "whoosh.wav").exists():
        todo.append("reels setup            # fonts + sound effects, one time")
    if not any((root / "reels").exists() for root in SKILL_TARGETS.values()):
        todo.append("reels install          # put the skill where your agent finds it")
    if shutil.which("claude") and not agents.claude_login()[0]:
        todo.append("claude  → /login          # judge, retro, make and bench call the standalone CLI")
    if todo:
        print("next:\n" + "\n".join("  " + t for t in todo))


def cmd_install(argv):
    ap = argparse.ArgumentParser(prog="reels install", description="Install the Reels-RSI skill into your agent(s).")
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
        dst = SKILL_TARGETS[n] / "reels"
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
    print("✓ done — in Claude Code: /reels 做一个讲…的视频 · in other agents: \"use the reels skill to make a video about …\"")


def language_of(a):
    """--lang, or the language of the topic text; a paper with no topic text follows the shell locale (zh → 中文)."""
    from reels_rsi import langs
    if a.lang != "auto":
        code = a.lang
    elif a.topic.strip():
        code = langs.detect(a.topic)
    else:
        loc = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").lower()
        code = next((c for c in ("zh", "ja", "ko", "es", "fr") if loc.startswith(c)), "en")
    return f"{code} ({langs.get(code)['name']})"


def cmd_make(argv):
    ap = argparse.ArgumentParser(prog="reels make", description="One sentence in, a reel out (headless agent). "
                                 "Explain a paper: `reels make --paper 1706.03762 \"用大白话讲\"`.")
    ap.add_argument("topic", nargs="?", default="", help="what to make; with --paper: the angle / audience (optional)")
    ap.add_argument("--paper", default=None, metavar="SRC",
                    help="explain a paper or document: PDF path, arXiv id or URL, PDF URL, .md / .txt / .html")
    ap.add_argument("--dir", default=None, help="project directory (default videos/<slug>)")
    ap.add_argument("--audience", default="intermediate",
                    help="beginner | intermediate | expert (小白 · 有基础 · 专业人士) — sets depth, terms, equations, numbers, pace")
    ap.add_argument("--length", type=int, default=None, help="seconds (default 60; a paper: 90 / 150 / 270 by audience)")
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16", "1:1"])
    ap.add_argument("--style", default="your choice")
    ap.add_argument("--lang", default="auto", help="zh · en · ja · ko · es · fr (auto = the language of the topic text)")
    ap.add_argument("--quality", default="high", choices=["draft", "standard", "high"])
    ap.add_argument("--output", default="video", choices=["video", "web", "both"],
                    help="deliverable: an MP4 (video), a browser-playable page (web — no render, faster), or both")
    ap.add_argument("--rsi", default="on", choices=["on", "off"],
                    help="off: no lessons, no judge/score loop, no retro — one review round (rules still run)")
    ap.add_argument("--rounds", type=int, default=None, help="max finalize→review rounds (default 3; 1 with --rsi off)")
    ap.add_argument("--fast", action="store_true", help="= --rsi off --rounds 1 --quality standard")
    ap.add_argument("--harness", default=None, help="claude | codex | gemini | opencode")
    ap.add_argument("--model", default=None, help="passed to the harness (e.g. opus, sonnet, gpt-5.1, deepseek/deepseek-chat)")
    ap.add_argument("--yes", action="store_true", help="skip the permission confirmation")
    a = ap.parse_args(argv)
    if not a.topic.strip() and not a.paper:
        ap.error("give a topic, or --paper <pdf | arXiv id | URL>")
    if a.fast:
        a.rsi, a.rounds, a.quality = "off", a.rounds or 1, "standard" if a.quality == "high" else a.quality
    rsi = a.rsi == "on"
    audience = agents.audience_of(a.audience)
    if a.length is None:
        a.length = agents.AUDIENCES[audience]["length"] if a.paper else 60
    h, m = config.harness()
    harness, model = a.harness or h, a.model or m
    paper_title, paper_cache = "", None
    if a.paper:
        from reels_rsi.pipeline import paper as paper_mod
        print(f"▶ ingesting {a.paper} …", flush=True)
        paper_cache = paper_mod.ingest(a.paper)
        paper_title = paper_mod.meta_of(paper_cache).get("title", "")
        print(f"  {paper_title[:90]}  ({paper_cache})", flush=True)
    slug_src = a.topic or paper_title
    slug = re.sub(r"[^\w]+", "-", slug_src.lower()).strip("-_")[:40] or f"reel-{os.getpid()}"   # keeps 中文
    proj = Path(a.dir or f"videos/{slug}").resolve()
    if not a.yes:
        if not sys.stdin.isatty():
            sys.exit("✗ headless make runs an agent with full tool permissions in this folder — pass --yes")
        if input(f"{harness} ({model}) will work in {Path.cwd()} with full tool permissions. Continue? [y/N] ").lower() != "y":
            return
    topic = a.topic.strip()
    if a.paper:
        who = {"beginner": "someone with no background in the field (小白)", "intermediate": "someone who knows the basics (有基础)",
               "expert": "a researcher or senior engineer in the same field (专业人士)"}[audience]
        topic = f"Explain this paper to {who}: “{paper_title}”" + (f"\n   Direction: {topic}" if topic else "")
    blocks = agents.prompt_blocks(proj, a.quality, rsi, a.rounds, a.output, a.paper, paper_title, skill=paths.skill_dir(),
                                  audience=audience)
    prompt = agents.render_prompt("make", skill=paths.skill_dir(), topic=topic, length=a.length, aspect=a.aspect,
                                  style=a.style, dir=proj, quality=a.quality, language=language_of(a), **blocks)
    mode = (("RSI on" if rsi else "RSI off") + f" · ≤{a.rounds or (3 if rsi else 1)} round(s) · output {a.output} · {language_of(a)}"
            f" · audience {audience} ({agents.AUDIENCES[audience]['zh']}) · {a.length}s")
    print(f"▶ {harness} ({model}) is directing: {topic.splitlines()[0]}\n  project: {proj}\n  {mode}", flush=True)
    proj.parent.mkdir(parents=True, exist_ok=True)
    env = {"REELS_RSI": "on" if rsi else "off"}
    res = agents.run(harness, model, prompt, cwd=Path.cwd(), log_path=proj.parent / f"{proj.name}.make.log", env=env)
    print(res["tail"][-1200:])
    video, web = proj / "renders" / "video.mp4", proj / "renders" / "web" / "index.html"
    made = [str(p) for p, want in ((video, a.output in ("video", "both")), (web, a.output in ("web", "both"))) if want and p.exists()]
    print(("✓ " + " · ".join(made) if made else "✗ nothing delivered — see the log")
          + f" · {res['seconds'] / 60:.1f} min" + (f" · ${res['cost_usd']:.2f}" if res.get("cost_usd") else ""))
    if web.exists():
        print(f"  open the page: reels web {proj} --serve --open")
