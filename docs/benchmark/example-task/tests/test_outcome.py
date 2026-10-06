"""RRBench outcome tests for one task — they read the final reel only, never the project or the agent's log.

    RRB_OUTPUT=/path/to/output  pytest docs/benchmark/example-task/tests -q

/path/to/output holds video.mp4 and, optionally, subtitles.srt (the output contract, docs/benchmark.md §2).
Without subtitles the transcript comes from faster-whisper if it is installed. The "answer is on screen"
check asks a vision model (RRB_JUDGE, default claude-cli:sonnet) and quotes what it saw; it is skipped,
not passed, when no judge is available.
"""

import json
import os
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]
CFG = tomllib.loads((TASK / "task.toml").read_text("utf-8"))
FACTS = tomllib.loads((TASK / "facts.toml").read_text("utf-8"))
OUT = Path(os.environ.get("RRB_OUTPUT", "/output"))
VIDEO = OUT / "video.mp4"


def probe():
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", str(VIDEO)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


DIGIT = dict(zip("零一二两三四五六七八九", [0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))


def cn_number(s):
    """三十五 → 35, 十二 → 12, 九十四 → 94, 一百二十 → 120 (up to 9999)."""
    total, cur = 0, 0
    for ch in s:
        if ch in DIGIT:
            cur = DIGIT[ch]
        else:
            unit = {"十": 10, "百": 100, "千": 1000}[ch]
            total += (cur or 1) * unit
            cur = 0
    return total + cur


def normalize(text):
    return re.sub(r"[零一二两三四五六七八九十百千]+", lambda m: str(cn_number(m.group())), text)


def transcript():
    srt = OUT / "subtitles.srt"
    if srt.exists():
        lines = [ln for ln in srt.read_text("utf-8").splitlines()
                 if ln.strip() and not ln.strip().isdigit() and "-->" not in ln]
        return normalize(" ".join(lines))
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        pytest.skip("no subtitles.srt and faster-whisper is not installed")
    segs, _ = WhisperModel("small").transcribe(str(VIDEO), language=CFG["language"][:2])
    return normalize(" ".join(s.text for s in segs))


def frames(fracs, tmp):
    dur = float(probe()["format"]["duration"])
    out = []
    for i, f in enumerate(fracs):
        p = Path(tmp) / f"f{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * f:.2f}", "-i", str(VIDEO), "-frames:v", "1",
                        "-vf", "scale=960:-2", str(p)], check=True)
        out.append(p)
    return out


# ── gates ────────────────────────────────────────────────────────────────────
def test_renders_with_picture_and_sound():
    kinds = {s["codec_type"] for s in probe()["streams"]}
    assert {"video", "audio"} <= kinds


def test_aspect():
    v = next(s for s in probe()["streams"] if s["codec_type"] == "video")
    want = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0}[CFG["aspect"]]
    assert abs(v["width"] / v["height"] - want) < 0.02


def test_length_window():
    lo, hi = CFG["length"]
    assert lo <= float(probe()["format"]["duration"]) <= hi


@pytest.mark.parametrize("fact", sorted(FACTS["required"]))
def test_required_fact_is_said(fact):
    assert re.search(FACTS["required"][fact], transcript()), f"not said: {fact}"


@pytest.mark.parametrize("claim", sorted(FACTS["forbidden"]))
def test_no_forbidden_claim(claim):
    m = re.search(FACTS["forbidden"][claim], transcript())
    assert not m, f"forbidden ({claim}): …{m.group(0)}…"


def test_no_frozen_or_black_stretch():
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(VIDEO), "-vf",
                        "freezedetect=n=0.002:d=3,blackdetect=d=2:pix_th=0.05", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    dur = float(probe()["format"]["duration"])
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    freezes = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", r.stderr)]
    freezes += [dur - s for s in starts[len(freezes):]]     # a freeze that runs to the end reports no duration
    tail = lambda s, d: s + d >= dur - 1.0
    bad = [d for s, d in zip(starts, freezes) if not tail(s, d) or d > 4.0]   # a held end card ≤ 4 s is fine
    assert not bad, f"picture frozen for {max(bad):.1f}s"
    assert "black_start" not in r.stderr, "black stretch ≥ 2 s"


def test_answer_is_on_screen():
    """The final answer must be visible, not only spoken. The vision model only TRANSCRIBES what is on
    screen; the decision is made here, in code — a model asked "is it visible?" flipped on a borderline
    frame between two runs, while transcription is stable and its output is evidence anyone can check."""
    spec = os.environ.get("RRB_JUDGE", "claude-cli:sonnet")
    try:
        from reels_rsi import llm
    except ImportError:
        pytest.skip("no judge library")
    ok, why = llm.available(spec)
    if not ok:
        pytest.skip(f"no judge: {why}")
    with tempfile.TemporaryDirectory() as tmp:
        imgs = frames((0.75, 0.85, 0.95), tmp)
        j = llm.complete_json(spec, """These are frames from the last quarter of a lesson video.
Transcribe every piece of text, number and label drawn on screen (ignore the subtitle bar at the bottom),
one entry per frame. Return JSON: {"frames": ["…text of frame 1…", "…frame 2…", "…frame 3…"]}""", images=imgs)
    print("on screen:", j)
    lines = [normalize(ln) for fr in j.get("frames", []) for ln in str(fr).splitlines()]
    a = FACTS["answer"]
    for label, n in (("鸡", a["chickens"]), ("兔", a["rabbits"])):
        # the count, as its own number, on a line that names the animal: "鸡 23" · "兔 = 12" · "鸡 35−12=23" · "23 只鸡"
        hit = [ln for ln in lines if label in ln and re.search(rf"(^|[^\d.]){n}($|[^\d.])", ln.split(label, 1)[1] + " "
                                                                 + ln.split(label, 1)[0][-6:])]
        assert hit, f"{n} {label} is not stated on screen at the end — saw: {' | '.join(lines)[:240]}"
