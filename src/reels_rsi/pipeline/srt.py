"""Export subtitles for upload platforms (B站 / YouTube / 视频号 accept .srt).

Reads caption_groups.json (written by reels captions). Writes renders/subtitles.srt, plus
renders/subtitles.en.srt and a combined bilingual renders/subtitles.zh-en.srt when the groups
carry English. Run after finalize.

Usage: reels srt --project <dir>
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


def cjk(text):
    return any("\u3000" <= c <= "\u9fff" or "\uff00" <= c <= "\uffef" for c in text)


def merge(groups):
    """On-screen caption groups are short (2-3 English words for karaoke). A subtitle file wants
    reading-sized cues: join consecutive groups until a sentence ends, a pause (> 0.5 s) or a
    length cap (42 Latin / 18 CJK characters) — the usual subtitle limits."""
    cues = []
    for g in groups:
        text = g["text"].strip()
        if cues:
            a, b, prev = cues[-1]
            zh = cjk(prev + text)
            joined = prev + " " + text          # caption groups carry no clause punctuation; zh subtitles separate clauses with a space
            ends = prev.rstrip()[-1:] in ".?!。？！…"
            if not ends and g["start"] - b <= 0.5 and len(joined) <= (18 if zh else 42):
                cues[-1] = (a, g["end"], joined)
                continue
        cues.append((g["start"], g["end"], text))
    return cues


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    project = Path(ap.parse_args(argv).project)
    groups = json.loads((project / "caption_groups.json").read_text("utf-8"))["groups"]
    out = project / "renders"
    out.mkdir(exist_ok=True)
    if any(g.get("en") for g in groups):     # bilingual: keep the clause groups the English lines up with
        write(out / "subtitles.srt", [(g["start"], g["end"], g["text"]) for g in groups])
        write(out / "subtitles.en.srt", [(g["start"], g["end"], g.get("en", "")) for g in groups])
        write(out / "subtitles.zh-en.srt", [(g["start"], g["end"], g["text"] + ("\n" + g["en"] if g.get("en") else "")) for g in groups])
    else:
        write(out / "subtitles.srt", merge(groups))
    print("✓ subtitles → renders/")


if __name__ == "__main__":
    main()
