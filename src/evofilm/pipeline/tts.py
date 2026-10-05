"""Voice SCRIPT.md, build word timings and the music bed → audio_meta.json (frame-keyed).

Providers (--provider auto picks the first available):
  elevenlabs  needs ELEVENLABS_API_KEY; voice via --voice <voice_id> or ELEVENLABS_VOICE_ID.
              Uses /with-timestamps (character alignment → per-character words).   [UNTESTED: no key yet]
  edge        free Microsoft Edge TTS, native WordBoundary timings. Default voice zh-CN-YunxiNeural.
              Good Chinese voices: zh-CN-YunxiNeural (male, lively) · zh-CN-XiaoxiaoNeural (female, warm)
              · zh-CN-YunjianNeural (male, deep) · zh-CN-XiaoyiNeural (female, bright).

Music bed (--bgm):
  auto   a user track in <project>/assets/music/ (mp3/wav/m4a) if present, else `evofilm music`
         (mood from STORYBOARD `music:`; accents land on the real cut times)
  synth  always `evofilm music`
  none   no music
  <path> a specific file

Language: --lang auto detects Chinese vs English from SCRIPT.md. English default voice
en-US-AndrewNeural (also good: en-US-AvaNeural, en-GB-RyanNeural).

Then writes the real voice durations into STORYBOARD.md (`- duration:` per frame).

Usage: evofilm voice --project <dir> [--provider auto|edge|elevenlabs] [--voice ...] [--rate +0%] [--bgm auto] [--lang auto|zh|en]
"""

import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from evofilm.pipeline import music

PUNCT = "，。？！；：、—…,.?!;:「」“”"


def parse_script(text):
    """[(frame, spoken_text)] from SCRIPT.md: indented blocks under '## Line N — … (Frame N)'."""
    lines, cur = [], None
    for raw in text.splitlines():
        m = re.match(r"^##\s+Line\s+\d+.*\(Frame\s+(\d+)\)", raw)
        if m:
            cur = [int(m.group(1)), ""]
            lines.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^(?: {4,}|\t)(.+)$", raw)
        if m:
            cur[1] += m.group(1).strip()
    return [(f, t) for f, t in lines if t]


def attach_punct(words, source):
    """Glue the punctuation that follows each spoken word in `source` onto that word."""
    pos = 0
    for w in words:
        i = source.find(w["text"], pos)
        if i < 0:
            continue
        j = i + len(w["text"])
        while j < len(source) and source[j] in PUNCT:
            j += 1
        w["text"] = source[i:j]
        pos = j
    return words


# ── providers ────────────────────────────────────────────────────────────────
DEFAULT_VOICE = {"zh": "zh-CN-YunxiNeural", "en": "en-US-AndrewNeural"}


async def edge_synth(text, voice, rate, mp3, lang="zh", attempts=4):
    """edge-tts with retries — the service drops connections now and then."""
    for i in range(attempts):
        try:
            return await _edge_once(text, voice, rate, mp3, lang)
        except Exception as e:  # aiohttp / websocket / service errors
            if i == attempts - 1:
                sys.exit(f"✗ edge-tts failed after {attempts} tries ({type(e).__name__}: {str(e)[:160]}) — "
                         "check the network (speech.platform.bing.com) and rerun; finished frames are kept with --only")
            wait = 2 ** i * 2
            print(f"  ⚠ edge-tts {type(e).__name__} — retry in {wait}s", flush=True)
            await asyncio.sleep(wait)


async def _edge_once(text, voice, rate, mp3, lang):
    import edge_tts
    comm = edge_tts.Communicate(text, voice or DEFAULT_VOICE[lang], rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as fh:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": round(s, 3),
                              "end": round(s + chunk["duration"] / 1e7, 3)})
    return words


def elevenlabs_synth(text, voice, mp3):
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = voice or os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice:
        sys.exit("✗ elevenlabs: pass --voice <voice_id> or set ELEVENLABS_VOICE_ID")
    model = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": model}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    Path(mp3).write_bytes(base64.b64decode(data["audio_base64"]))
    al = data.get("alignment") or data.get("normalized_alignment") or {}
    words = []
    for ch, s, e in zip(al.get("characters", []), al.get("character_start_times_seconds", []),
                        al.get("character_end_times_seconds", [])):
        if ch.strip() == "":
            continue
        if ch in PUNCT and words:
            continue  # attach_punct re-adds punctuation from the source text
        words.append({"text": ch, "start": round(s, 3), "end": round(e, 3)})
    return words


def pick_provider(name):
    if name != "auto":
        return name
    return "elevenlabs" if os.environ.get("ELEVENLABS_API_KEY") else "edge"


# ── music ────────────────────────────────────────────────────────────────────
def user_track(project, mode):
    """A user-supplied bed (path or assets/music/*) → project-relative path, else None."""
    music_dir = project / "assets" / "music"
    if mode not in ("auto", "synth", "none"):
        src = Path(mode).expanduser().resolve()
        music_dir.mkdir(parents=True, exist_ok=True)
        dst = music_dir / src.name
        if src != dst:
            shutil.copyfile(src, dst)
        return f"assets/music/{dst.name}"
    if mode == "auto" and music_dir.exists():
        tracks = sorted(p for p in music_dir.iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac"))
        if tracks:
            return f"assets/music/{tracks[0].name}"
    return None


def sync_durations(storyboard_path, voices):
    """Write each voiced frame's real duration into its `- duration:` line (port of HyperFrames' sync-durations)."""
    dur = {v["frame"]: v["duration_s"] for v in voices if v.get("duration_s")}
    lines = Path(storyboard_path).read_text("utf-8").split("\n")
    cur, updated = None, 0
    for i, line in enumerate(lines):
        h = re.match(r"^#{2,3}\s+(?:frame|beat|scene)\b.*?(\d+)", line, re.I)
        if h:
            cur = int(h.group(1))
            continue
        if cur in dur:
            m = re.match(r"^(\s*[-*]\s+duration\s*:\s*).*", line, re.I)
            if m:
                lines[i] = f"{m.group(1)}{dur.pop(cur)}s"
                updated += 1
    Path(storyboard_path).write_text("\n".join(lines), "utf-8")
    print(f"✓ sync-durations: {updated} frame duration(s) updated"
          + (f" · no `- duration:` line for frame(s) {', '.join(map(str, dur))}" if dur else ""))


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()), 3)


async def _main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--provider", default="auto", choices=["auto", "edge", "elevenlabs"])
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", default="+0%", help="edge only, e.g. +8%%")
    ap.add_argument("--bgm", default="auto")
    ap.add_argument("--only", default=None, help="comma list of frame numbers to re-voice")
    ap.add_argument("--lang", default="auto", choices=["auto", "zh", "en"])
    a = ap.parse_args(argv)

    from evofilm.project import require_project
    project = require_project(a.project, need=("SCRIPT.md", "STORYBOARD.md"))
    provider = pick_provider(a.provider)
    voice_dir = project / "assets" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    meta_path = project / "audio_meta.json"
    old = {v["frame"]: v for v in json.loads(meta_path.read_text("utf-8")).get("voices", [])} \
        if meta_path.exists() else {}
    only = {int(x) for x in a.only.split(",")} if a.only else None

    lines = parse_script((project / "SCRIPT.md").read_text("utf-8"))
    lang = a.lang if a.lang != "auto" else ("zh" if any("\u4e00" <= ch <= "\u9fff" for _, t in lines for ch in t) else "en")
    voices = []
    for frame, text in lines:
        if only is not None and frame not in only and frame in old:
            voices.append(old[frame])
            continue
        mp3, wav = voice_dir / f"{frame:02d}.mp3", voice_dir / f"{frame:02d}.wav"
        if provider == "elevenlabs":
            words = elevenlabs_synth(text, a.voice, mp3)
        else:
            words = await edge_synth(text, a.voice, a.rate, mp3, lang)
        words = attach_punct(words, text)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "44100", "-ac", "1",
                        str(wav)], check=True)
        mp3.unlink()
        for i, w in enumerate(words):
            w["id"] = f"w{i}"
        voices.append({"frame": frame, "path": f"assets/voice/{frame:02d}.wav", "duration_s": probe(wav),
                       "words": words})
        print(f"  frame {frame:02d}: {voices[-1]['duration_s']:.2f}s · {len(words)} words")

    total = sum(v["duration_s"] for v in voices)
    meta = {
        "bgm": None,
        "bgm_pending": False,
        "voices": voices,
        "sfx": json.loads(meta_path.read_text("utf-8")).get("sfx", []) if meta_path.exists() else [],
        "language": lang,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    sync_durations(project / "STORYBOARD.md", voices)

    # music after the sync, so a generated bed accents the real cut times
    track = user_track(project, a.bgm) if a.bgm != "none" else None
    kind = "user track" if track else None
    if not track and a.bgm in ("auto", "synth"):
        track, mood = music.generate(project)
        kind = f"synth ({mood})" if track else None
    meta["bgm"] = {"path": track, "volume": None, "query": kind, "duration_s": None} if track else None
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    print(f"✓ tts ({provider}, {lang}): {len(voices)} lines · {total:.1f}s narration · music: {kind or 'none'}")


def main(argv=None):
    asyncio.run(_main(argv))


if __name__ == "__main__":
    main()
