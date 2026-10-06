"""Stroke-order data for Chinese characters (汉字笔顺) → <project>/assets/hanzi.js

  reels hanzi 静夜思 --project .

Writes window.EF_HANZI = {"静": {"strokes": [svg path…], "medians": [[[x,y]…]…]}, …} from
hanzi-writer-data (derived from Make Me a Hanzi / Arphic fonts, Arphic Public License — a credit
line is added to CREDITS.md). Coordinates are a 1024 box with y pointing UP: draw inside
<g transform="translate(0, 900) scale(1, -1)">. Animate each stroke yourself with a mask path along
its median (stroke-dashoffset), stroke by stroke — never HanziWriter's own animation loop, which
runs on requestAnimationFrame and breaks seek-rendering. See references/solve.md.
"""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/{}.json"
CREDIT = ("- assets/hanzi.js — stroke data from hanzi-writer-data (Make Me a Hanzi, derived from Arphic fonts) · "
          "Arphic Public License · https://github.com/chanind/hanzi-writer-data\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reels hanzi", description="Fetch stroke-order data for characters.")
    ap.add_argument("chars")
    ap.add_argument("--project", default=".")
    a = ap.parse_args(argv)
    project = Path(a.project)
    out = project / "assets" / "hanzi.js"
    data = {}
    if out.exists():
        text = out.read_text("utf-8")
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    for ch in dict.fromkeys(c for c in a.chars if "一" <= c <= "鿿"):
        if ch in data:
            continue
        with urllib.request.urlopen(URL.format(urllib.parse.quote(ch)), timeout=60) as r:
            j = json.loads(r.read())
        data[ch] = {"strokes": j["strokes"], "medians": j["medians"]}
        print(f"  {ch}: {len(j['strokes'])} strokes")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("window.EF_HANZI = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", "utf-8")
    credits = project / "CREDITS.md"
    if not credits.exists():
        credits.write_text("# Credits — third-party material\n\n", "utf-8")
    if "hanzi-writer-data" not in credits.read_text("utf-8"):
        with credits.open("a", encoding="utf-8") as fh:
            fh.write(CREDIT)
    print(f"✓ {len(data)} characters → {out}")


if __name__ == "__main__":
    main()
