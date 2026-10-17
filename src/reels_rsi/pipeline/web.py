"""Web output: the reel as a page that plays in any browser — no MP4 render, seconds instead of minutes.

    reels web <project> [--serve] [--port 3005] [--open]

renders/web/
  index.html      a page with the HyperFrames player (play/pause, scrub, speed, fullscreen)
  player.js       the <hyperframes-player> web component, from the HyperFrames CLI version the project pins
  runtime.js      the HyperFrames runtime the player needs inside the composition
  composition/    index.html + compositions/ + assets/ (voice, music, SFX, fonts, kits) — a copy, untouched
                  except for one <script src="../runtime.js"> line

The folder is static: any file server shows it (`reels web --serve`, `python -m http.server`, GitHub Pages,
an S3 bucket). Opening index.html as a file:// does not work — browsers refuse to load the sub-compositions.
A hosted link with one command is `reels hf --project . publish` (HeyGen account).
"""

import argparse
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from reels_rsi import paths

SKIP_DIRS = {"music", "__pycache__"}          # assets/music = the user's raw track; the bed is assets/bgm
SKIP_SUFFIX = {".map", ".py", ".pyc", ".md"}
PLAYER = "dist/hyperframes-player.global.js"
RUNTIME = "dist/hyperframe.runtime.iife.js"


def hf_package_dir(version):
    """Where npx cached hyperframes@<version> (prefetching it when it is not there yet)."""
    def scan():
        for pj in sorted((Path.home() / ".npm" / "_npx").glob("*/node_modules/hyperframes/package.json")):
            try:
                if json.loads(pj.read_text("utf-8")).get("version") == version:
                    return pj.parent
            except (OSError, ValueError):
                continue
        return None
    d = scan()
    if d is None:
        subprocess.run(["npx", "-y", f"hyperframes@{version}", "--version"], capture_output=True)
        d = scan()
    if d is None or not (d / PLAYER).exists():
        raise SystemExit(f"✗ cannot find the player in hyperframes@{version} (npx cache) — `npx -y hyperframes@{version} --version` then retry")
    return d


def canvas_of(index_html):
    m = re.search(r'id="root"[^>]*?data-width="(\d+)"[^>]*?data-height="(\d+)"', index_html, re.S)
    return (int(m.group(1)), int(m.group(2))) if m else (1920, 1080)


def duration_of(index_html):
    m = re.search(r'id="root"[^>]*?data-duration="([\d.]+)"', index_html, re.S)
    return float(m.group(1)) if m else 0.0


def copy_tree(src, dst):
    def ignore(d, names):
        return [n for n in names if n in SKIP_DIRS or Path(n).suffix in SKIP_SUFFIX or n.startswith(".")]
    shutil.copytree(src, dst, ignore=ignore, dirs_exist_ok=True)


def page(title, w, h, duration):
    return f"""<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ height: 100%; }}
      body {{ background: #0b0b0c; color: #e8e8e8; font-family: system-ui, -apple-system, "PingFang SC", "Noto Sans SC", sans-serif;
             display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; gap: 14px; }}
      .wrap {{ width: min(100%, calc((100vh - 110px) * {w} / {h})); aspect-ratio: {w} / {h}; border-radius: 10px; overflow: hidden;
              background: #000; box-shadow: 0 20px 60px rgba(0,0,0,.5); }}
      hyperframes-player {{ display: block; width: 100%; height: 100%; }}
      h1 {{ font-size: 15px; font-weight: 500; color: #bdbdbd; letter-spacing: .01em; }}
      .meta {{ font-size: 12px; color: #6a6a6a; font-family: ui-monospace, Menlo, monospace; }}
      a {{ color: #8a8a8a; }}
    </style>
  </head>
  <body>
    <h1>{title}</h1>
    <div class="wrap"><hyperframes-player src="composition/index.html" controls></hyperframes-player></div>
    <div class="meta">{duration:.0f} s · {w}×{h} · made with <a href="https://github.com/agentic-loops-x/Reels-RSI">Reels-RSI</a> · plays with HyperFrames</div>
    <script src="player.js"></script>
  </body>
</html>
"""


def export(project, out=None):
    """Write renders/web/ for a finalized project (index.html must exist). Returns the folder."""
    from reels_rsi.project import hf_version, require_project
    project = require_project(project, need=("hyperframes.json", "index.html"))
    out = Path(out).resolve() if out else project / "renders" / "web"
    pkg = hf_package_dir(hf_version(project))
    index = (project / "index.html").read_text("utf-8")
    shutil.rmtree(out, ignore_errors=True)
    (out / "composition").mkdir(parents=True)
    shutil.copyfile(pkg / PLAYER, out / "player.js")
    shutil.copyfile(pkg / RUNTIME, out / "runtime.js")
    for d in ("compositions", "assets"):
        if (project / d).is_dir():
            copy_tree(project / d, out / "composition" / d)
    if "runtime.js" not in index:        # what `hyperframes play` injects when it serves the composition
        index = index.replace("<head>", '<head>\n    <script src="../runtime.js"></script>', 1)
    (out / "composition" / "index.html").write_text(index, "utf-8")
    w, h = canvas_of(index)
    meta = project / ".reels" / "project.json"
    title = ""
    if meta.exists():
        title = json.loads(meta.read_text("utf-8")).get("title") or ""
    (out / "index.html").write_text(page(title or project.name, w, h, duration_of(index)), "utf-8")
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    from reels_rsi.rsi import runlog
    runlog.append(project, {"event": "web", "ok": True, "bytes": size, "duration_s": duration_of(index)})
    return out, size


def serve(folder, port=3005, open_browser=False):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    handler.log_message = lambda *a, **k: None          # type: ignore[attr-defined]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://localhost:{port}/"
    print(f"▶ {url}  (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reels web", description="Export the reel as a browser-playable page (renders/web/), no MP4.")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--out", default=None, help="output folder (default renders/web)")
    ap.add_argument("--serve", action="store_true", help="serve the folder on localhost after exporting")
    ap.add_argument("--port", type=int, default=3005)
    ap.add_argument("--open", action="store_true", help="with --serve: open the browser")
    a = ap.parse_args(argv)
    t0 = time.time()
    out, size = export(a.project, a.out)
    print(f"✓ {out} · {size / 1e6:.1f} MB · {time.time() - t0:.1f}s\n"
          f"  serve it: reels web {Path(a.project).resolve()} --serve   (or any static file server; file:// will not work)")
    if a.serve:
        serve(out, a.port, a.open)
