"""Make the video cover / thumbnail (封面).

Two ways:
  1. Dedicated cover (best): write compositions/cover.html — a normal single-frame sub-composition
     (id "cover", 1920×1080 or 1080×1920) with a big title, the film's hero visual and no captions.
     `cover.py --project . --composition` snapshots it alone via a temporary preview index.
  2. Frame grab: `cover.py --project . --at 12.5` grabs the rendered MP4 at that time, nudged to the
     nearest moment with no caption on screen (uses caption_groups.json).

Writes renders/cover.jpg (and cover.png for the composition route).
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path



def caption_free(t, groups, total):
    def busy(x):
        return any(g["start"] - 0.05 <= x <= g["end"] + 0.05 for g in groups)
    for d in [i * 0.1 for i in range(0, 60)]:
        for x in (t + d, t - d):
            if 0 <= x <= total and not busy(x):
                return x
    return t


def from_video(project, at):
    video = project / "renders" / "video.mp4"
    if not video.exists():
        raise SystemExit("✗ renders/video.mp4 not found — render first, or use --composition")
    groups = json.loads((project / "caption_groups.json").read_text("utf-8"))["groups"] \
        if (project / "caption_groups.json").exists() else []
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(video)], capture_output=True, text=True).stdout.strip())
    t = caption_free(at, groups, total)
    out = project / "renders" / "cover.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                    "-q:v", "2", str(out)], check=True)
    print(f"✓ cover from {t:.2f}s → {out}")


def from_composition(project):
    comp = project / "compositions" / "cover.html"
    if not comp.exists():
        raise SystemExit("✗ compositions/cover.html not found")
    tmp = project / ".hyperframes" / "cover-project"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for name in ("package.json", "hyperframes.json", "meta.json"):
        if (project / name).exists():
            shutil.copy(project / name, tmp / name)
    (tmp / "compositions").mkdir()
    shutil.copy(comp, tmp / "compositions" / "cover.html")
    for d in ("assets", "public"):
        if (project / d).exists():
            (tmp / d).symlink_to((project / d).resolve())
    src = comp.read_text("utf-8")
    w = re.search(r'data-width="(\d+)"', src).group(1)
    h = re.search(r'data-height="(\d+)"', src).group(1)
    (tmp / "index.html").write_text(f"""<!doctype html>
<html><head><meta charset="UTF-8" /><meta name="viewport" content="width={w}, height={h}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#000}}#root{{position:relative;width:100%;height:100%}}</style>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="2" data-width="{w}" data-height="{h}">
  <div id="el-cover" data-composition-id="cover" data-composition-src="compositions/cover.html" data-start="0" data-duration="2" data-track-index="0" data-width="{w}" data-height="{h}"></div>
</div>
<script>window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>
""", "utf-8")
    from evofilm.project import hf
    hf(tmp, ["snapshot", "--at", "1.9"], capture=True)
    shots = sorted((tmp / "snapshots").glob("frame-*.png"))
    if not shots:
        raise SystemExit("✗ cover snapshot failed")
    (project / "renders").mkdir(exist_ok=True)
    png = project / "renders" / "cover.png"
    shutil.copy(shots[0], png)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-q:v", "2", str(project / "renders" / "cover.jpg")], check=True)
    shutil.rmtree(tmp)
    print(f"✓ cover composition → {png}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evofilm cover")
    ap.add_argument("--project", default=".")
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--composition", action="store_true")
    a = ap.parse_args(argv)
    p = Path(a.project).resolve()
    from_composition(p) if a.composition else from_video(p, a.at if a.at is not None else 1.0)


if __name__ == "__main__":
    main()
