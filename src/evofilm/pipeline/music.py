"""Procedural, cut-aware music bed — free, offline, deterministic.

Moods (pick from STORYBOARD frontmatter `music:` keywords, or --mood):
  ambient    soft pad chords + sparse plucks            (science, calm explainers)
  cinematic  low strings-like pad, timpani-ish hits and swells on every cut   (history, documentary)
  epic       cinematic + driving low pulse + bigger hits  (battles, climaxes, launches)
  upbeat     ~104 BPM kick/hat groove + bright plucks     (product, lifestyle, listicles)
  none       no music

Cut-awareness: frame start times (from STORYBOARD durations) get a hit/accent, and the chord
changes on cuts, so the score breathes with the edit. A user track in <project>/assets/music/
always wins over this (evofilm voice --bgm auto handles that).

Usage: evofilm music --project <dir> [--mood auto|ambient|cinematic|epic|upbeat] [--out assets/bgm/bed.wav]
"""

import argparse
import re
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
KEYWORDS = {
    "epic": ["epic", "battle", "war", "史诗", "战", "激昂", "宏大", "launch", "climax"],
    "cinematic": ["cinematic", "history", "documentary", "历史", "纪录", "电影", "古", "悠远", "庄重", "solemn"],
    "upbeat": ["upbeat", "energetic", "fun", "轻快", "欢快", "活泼", "节奏", "product", "pop"],
    "ambient": ["ambient", "calm", "curious", "science", "科普", "安静", "舒缓", "pad"],
}
CHORDS = [  # I–vi–IV–V in C, root-position voicings (Hz)
    (130.81, 164.81, 196.00, 246.94), (110.00, 130.81, 164.81, 196.00),
    (87.31, 130.81, 174.61, 220.00), (98.00, 146.83, 196.00, 246.94)]
MINOR = [  # i–VI–III–VII in A minor (for cinematic/epic)
    (110.00, 130.81, 164.81, 220.00), (87.31, 110.00, 130.81, 174.61),
    (65.41, 98.00, 130.81, 164.81), (98.00, 123.47, 146.83, 196.00)]


def frame_starts(storyboard):
    starts, t = [], 0.0
    for m in re.finditer(r"^\s*-\s+duration\s*:\s*([\d.]+)s?\s*$", storyboard, re.M):
        starts.append(t)
        t += float(m.group(1))
    return starts, t


def detect_mood(storyboard):
    m = re.search(r"^music:\s*(.+)$", storyboard, re.M)
    text = (m.group(1) if m else "").lower()
    if text.strip() == "none":
        return "none"
    for mood, words in KEYWORDS.items():
        if any(w in text for w in words):
            return mood
    return "ambient"


def pad(t, chord_seq, starts, total, bright=0.35):
    sig = np.zeros_like(t)
    bounds = list(starts) + [total + 4]
    for i in range(len(bounds) - 1):
        c = chord_seq[i % len(chord_seq)]
        a, b = bounds[i], bounds[i + 1]
        w = np.clip(np.minimum((t - a + 1.2) / 1.2, (b + 1.2 - t) / 1.2), 0, 1) ** 1.5
        for k, f in enumerate(c):
            lfo = 0.78 + 0.22 * np.sin(2 * np.pi * (0.07 + 0.011 * k) * t + k)
            det = np.sin(2 * np.pi * f * 1.004 * t) * 0.5
            sig += w * lfo * (np.sin(2 * np.pi * f * t) + det + bright * np.sin(2 * np.pi * 2 * f * t)) / (k + 2)
    return sig / (np.max(np.abs(sig)) + 1e-9)


def add(buf, sample, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    n = min(len(sample), len(buf) - i)
    buf[i:i + n] += sample[:n]


def timpani(f=55.0, dur=1.6, amp=1.0, seed=0):
    tt = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(seed)
    body = np.sin(2 * np.pi * (f * (1 + 0.6 * np.exp(-tt * 18))) * tt) * np.exp(-tt * 2.6)
    noise = rng.standard_normal(len(tt)) * np.exp(-tt * 30) * 0.25
    return amp * (body + noise)


def swell(dur=2.0, f=220.0):
    tt = np.arange(int(dur * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * m * tt) / m for m in (1, 1.5, 2, 3))
    return s * (tt / dur) ** 2.5 * 0.35


def pluck(f, dur=1.2, amp=0.18):
    tt = np.arange(int(dur * SR)) / SR
    return amp * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 4)


def kick(amp=0.9):
    tt = np.arange(int(0.35 * SR)) / SR
    return amp * np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)


def hat(seed, amp=0.12):
    tt = np.arange(int(0.05 * SR)) / SR
    n = np.random.default_rng(seed).standard_normal(len(tt))
    n = np.diff(n, prepend=0)  # crude high-pass
    return amp * n * np.exp(-tt * 90)


def compose(mood, starts, total):
    length = total + 4
    t = np.arange(int(length * SR)) / SR
    out = np.zeros_like(t)
    if mood == "ambient":
        out += 0.6 * pad(t, CHORDS, starts, total)
        notes = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46]
        for i, at in enumerate(np.arange(1.5, total, 1.75)):
            add(out, pluck(notes[i % len(notes)] * (0.5 if (i // 6) % 2 else 1)), at)
        for s in starts[1:]:
            add(out, pluck(1046.5, 2.0, 0.12), s)
    elif mood in ("cinematic", "epic"):
        out += 0.7 * pad(t, MINOR, starts, total, bright=0.15)
        for i, s in enumerate(starts):
            if s > 0:
                add(out, timpani(55.0 if i % 2 else 49.0, amp=0.55 if mood == "cinematic" else 0.8, seed=i), s)
            if i + 1 < len(starts):
                add(out, swell(min(2.2, starts[i + 1] - s), 220.0), max(0, starts[i + 1] - 2.2))
        if mood == "epic":
            beat = 60 / 96
            for j, at in enumerate(np.arange(0, total, beat / 2)):
                add(out, timpani(41.2, 0.4, 0.22 if j % 2 else 0.32, seed=100 + j), at)
    elif mood == "upbeat":
        out += 0.35 * pad(t, CHORDS, starts, total, bright=0.5)
        beat = 60 / 104
        for j, at in enumerate(np.arange(0, total + 2, beat / 2)):
            if j % 2 == 0:
                add(out, kick(), at)
            add(out, hat(j), at + (beat / 4 if j % 2 else 0))
        notes = [659.25, 783.99, 880.0, 783.99]
        for j, at in enumerate(np.arange(0, total, beat)):
            add(out, pluck(notes[j % 4], 0.5, 0.12), at)
        for s in starts[1:]:
            add(out, swell(0.8, 440.0) * 0.6, max(0, s - 0.8))
    fade = int(2.5 * SR)
    out[:int(0.8 * SR)] *= np.linspace(0, 1, int(0.8 * SR))
    out[-fade:] *= np.linspace(1, 0, fade)
    return (out / (np.max(np.abs(out)) + 1e-9) * 0.85).astype(np.float32)


def generate(project, mood="auto", out="assets/bgm/bed.wav"):
    project = Path(project)
    sb = (project / "STORYBOARD.md").read_text("utf-8")
    if mood == "auto":
        mood = detect_mood(sb)
    if mood == "none":
        return None, mood
    starts, total = frame_starts(sb)
    path = project / out
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, compose(mood, starts, total), SR)
    return out, mood


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evofilm music")
    ap.add_argument("--project", default=".")
    ap.add_argument("--mood", default="auto", choices=["auto", "ambient", "cinematic", "epic", "upbeat", "none"])
    ap.add_argument("--out", default="assets/bgm/bed.wav")
    a = ap.parse_args(argv)
    rel, mood = generate(a.project, a.mood, a.out)
    print(f"✓ music: {mood}" + (f" → {rel}" if rel else ""))


if __name__ == "__main__":
    main()
