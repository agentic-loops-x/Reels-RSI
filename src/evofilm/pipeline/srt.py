"""Export subtitles for upload platforms (B站 / YouTube / 视频号 accept .srt).

Reads caption_groups.json (written by evofilm captions). Writes renders/subtitles.srt, plus
renders/subtitles.en.srt and a combined bilingual renders/subtitles.zh-en.srt when the groups
carry English. Run after finalize.

Usage: evofilm srt --project <dir>
"""

import argparse
import json
from pathlib import Path


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write(path, cues):
    path.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n" for i, (a, b, text) in enumerate(cues, 1)), "utf-8")
    print(f"  {path.name}: {len(cues)} cues")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    project = Path(ap.parse_args(argv).project)
    groups = json.loads((project / "caption_groups.json").read_text("utf-8"))["groups"]
    out = project / "renders"
    out.mkdir(exist_ok=True)
    write(out / "subtitles.srt", [(g["start"], g["end"], g["text"]) for g in groups])
    if any(g.get("en") for g in groups):
        write(out / "subtitles.en.srt", [(g["start"], g["end"], g.get("en", "")) for g in groups])
        write(out / "subtitles.zh-en.srt", [(g["start"], g["end"], g["text"] + ("\n" + g["en"] if g.get("en") else "")) for g in groups])
    print("✓ subtitles → renders/")


if __name__ == "__main__":
    main()
