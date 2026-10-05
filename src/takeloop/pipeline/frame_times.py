"""Print review timestamps for every frame host in an assembled index.html.

Default: three samples per frame — 30%, 60% and 92% of its window — so a review sees the build-up,
the middle and the landed state (the moment front-loading or a frozen hold shows up).
  takeloop times --project <dir>                → "1.08,2.16,3.31,..."  (for `hyperframes snapshot --at`)
  takeloop times --project <dir> --frame 04     → only frame 04's samples
  takeloop times --project <dir> --list         → one line per frame: id start end
"""

import argparse
import re
from pathlib import Path


def hosts(index_html):
    out = []
    for m in re.finditer(r"<div\b[^>]*data-composition-src=\"compositions/frames/([^\"]+)\.html\"[^>]*>", index_html, re.S):
        tag = m.group(0)
        start = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
        dur = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
        out.append((m.group(1), start, dur))
    return sorted(out, key=lambda h: h[1])


def sample_times(project, fractions=(0.3, 0.6, 0.92), frame=None):
    hs = hosts((Path(project) / "index.html").read_text("utf-8"))
    return [s + d * f for fid, s, d in hs if not frame or fid.startswith(frame) for f in fractions]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--frame", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fractions", default="0.3,0.6,0.92")
    a = ap.parse_args(argv)
    hs = hosts((Path(a.project) / "index.html").read_text("utf-8"))
    if a.frame:
        hs = [h for h in hs if h[0].startswith(a.frame)]
    if a.list:
        for fid, s, d in hs:
            print(f"{fid} {s:.2f} {s + d:.2f}")
        return
    fr = [float(x) for x in a.fractions.split(",")]
    print(",".join(f"{s + d * f:.2f}" for _, s, d in hs for f in fr))


if __name__ == "__main__":
    main()
