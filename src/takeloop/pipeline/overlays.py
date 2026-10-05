"""Mount film-wide overlay compositions (a timeline ribbon, chapter titles, a corner logo …).

Frames are separate sub-compositions that each get their own local clock; anything that must
persist ACROSS frames (a year ruler that keeps advancing, a chapter bar, a map inset) lives in
compositions/overlays/<name>.html and is mounted here on the root timeline for the whole film.
Overlay compositions see GLOBAL time (0 → film end), so they can key off frame start times —
`takeloop times --project . --list` prints them.

Run after assemble-index (takeloop finalize does it). Idempotent: re-running replaces the block.

Overlay file contract = a normal sub-composition: <template> root with
  data-composition-id="overlay-<name>"  and  window.__timelines["overlay-<name>"].
Keep overlays out of the caption band (y > 900) unless they ARE captions.
"""

import argparse
import re
from pathlib import Path

START, END = "<!-- takeloop:overlays -->", "<!-- /takeloop:overlays -->"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    project = Path(ap.parse_args(argv).project)
    index = project / "index.html"
    s = index.read_text("utf-8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
    overlays = sorted((project / "compositions" / "overlays").glob("*.html")) \
        if (project / "compositions" / "overlays").exists() else []
    if not overlays:
        index.write_text(s, "utf-8")
        print("  overlays: none")
        return
    root = re.search(r'<div\b[^>]*data-composition-id="[^"]+"[^>]*data-duration="([\d.]+)"', s, re.S) or \
        re.search(r'data-duration="([\d.]+)"', s)
    total = root.group(1)
    w = re.search(r'data-width="(\d+)"', s).group(1)
    h = re.search(r'data-height="(\d+)"', s).group(1)
    blocks = [START]
    for i, f in enumerate(overlays):
        name = f.stem
        cid = f"overlay-{name}"
        inner = f.read_text("utf-8")
        if f'data-composition-id="{cid}"' not in inner:
            raise SystemExit(f"✗ {f.name}: root must carry data-composition-id=\"{cid}\"")
        blocks.append(
            f'      <div id="el-{cid}" class="scene" data-composition-id="{cid}" '
            f'data-composition-src="compositions/overlays/{f.name}" data-start="0" '
            f'data-duration="{total}" data-track-index="{3 + i}" data-width="{w}" data-height="{h}"></div>')
    blocks.append(END)
    # mount just before the captions host so captions stay on top
    anchor = s.find("<!-- captions -->")
    if anchor < 0:
        anchor = s.rfind("</div>\n    <script")
    s = s[:anchor] + "\n".join(blocks) + "\n      " + s[anchor:]
    index.write_text(s, "utf-8")
    print(f"  overlays: {', '.join(f.stem for f in overlays)} (0 → {total}s)")


if __name__ == "__main__":
    main()
