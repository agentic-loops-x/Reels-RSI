"""Procedural sound effects for takeloop videos — free, offline, deterministic.

  library            synthesize the SFX set into ~/.takeloop/sfx/*.wav (takeloop setup runs this once)
  cues --project D   read `- sfx: name@offset, name@offset` lines from D/STORYBOARD.md frames,
                     copy the used files into D/assets/sfx/ and write them into D/audio_meta.json
                     as {frame, file, offset_s, duration_s, volume} (the assembler mounts them)

Available names: whoosh, whoosh-soft, pop, tick, chime, swell, impact, sparkle, click
Optional volume: name@offset@0.3   (default per-sound volume otherwise)
"""

import argparse
import json
import re
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf

from takeloop import paths
SR = 44100
DEFAULT_VOL = {"whoosh": 0.32, "whoosh-soft": 0.22, "pop": 0.35, "tick": 0.25, "chime": 0.3,
               "swell": 0.28, "impact": 0.4, "sparkle": 0.25, "click": 0.3}


def env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a) ** 2
    if r:
        e[-r:] = np.linspace(1, 0, r) ** 2
    return e


def band_noise(n, f_lo, f_hi, rng, frames=64):
    """Noise whose pass-band sweeps linearly from f_lo to f_hi (FFT-masked per chunk)."""
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    hop = n // frames
    win = np.hanning(hop * 2)
    for k in range(frames - 1):
        seg = noise[k * hop: k * hop + hop * 2]
        if len(seg) < hop * 2:
            break
        spec = np.fft.rfft(seg * win)
        freqs = np.fft.rfftfreq(len(seg), 1 / SR)
        c = f_lo + (f_hi - f_lo) * k / frames
        mask = np.exp(-0.5 * ((np.log(freqs + 1) - np.log(c)) / 0.5) ** 2)
        out[k * hop: k * hop + hop * 2] += np.fft.irfft(spec * mask, len(seg))
    return out / (np.max(np.abs(out)) + 1e-9)


def tone(freqs, dur, decay):
    t = np.arange(int(dur * SR)) / SR
    sig = sum(np.sin(2 * np.pi * f * t) * a for f, a in freqs)
    return sig * np.exp(-t / decay)


def synth(name):
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    if name in ("whoosh", "whoosh-soft"):
        dur = 0.7 if name == "whoosh" else 0.55
        n = int(dur * SR)
        sig = band_noise(n, 300, 3500 if name == "whoosh" else 1800, rng)
        return sig * env(n, dur * 0.55, dur * 0.4)
    if name == "pop":
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        f = 900 * np.exp(-t * 18) + 250
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
    if name == "tick":
        return tone([(2200, 1), (4400, 0.3)], 0.04, 0.008)
    if name == "click":
        return tone([(1400, 1), (2800, 0.4)], 0.05, 0.012)
    if name == "chime":
        f0 = 880
        return tone([(f0, 1), (f0 * 2.76, 0.4), (f0 * 5.4, 0.18), (f0 * 1.5, 0.3)], 1.6, 0.45)
    if name == "swell":
        dur = 1.6
        n = int(dur * SR)
        t = np.arange(n) / SR
        pad = sum(np.sin(2 * np.pi * f * t) for f in (220, 277.2, 329.6)) / 3
        sig = 0.6 * pad + 0.4 * band_noise(n, 400, 2500, rng)
        return sig * (t / dur) ** 2 * env(n, 0, 0.12)
    if name == "impact":
        n = int(0.6 * SR)
        t = np.arange(n) / SR
        f = 110 * np.exp(-t * 6) + 40
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        crack = band_noise(n, 2000, 800, rng) * np.exp(-t * 40)
        return body + 0.35 * crack
    if name == "sparkle":
        out = np.zeros(int(0.9 * SR))
        for i in range(7):
            start = int(i * 0.09 * SR)
            b = tone([(2000 + 350 * ((i * 5) % 7), 1)], 0.25, 0.05)
            out[start: start + len(b)] += b[: len(out) - start]
        return out
    raise ValueError(f"unknown sfx: {name}")


def cmd_library():
    LIB = paths.sfx_lib()
    LIB.mkdir(parents=True, exist_ok=True)
    for name in DEFAULT_VOL:
        sig = synth(name)
        sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.9
        sf.write(LIB / f"{name}.wav", sig.astype(np.float32), SR)
    print(f"✓ sfx library: {len(DEFAULT_VOL)} sounds → {LIB}")


def parse_cues(storyboard):
    cues, frame = [], None
    for line in storyboard.splitlines():
        h = re.match(r"^#{2,3}\s+(?:frame|beat|scene)\b.*?(\d+)", line, re.I)
        if h:
            frame = int(h.group(1))
            continue
        m = re.match(r"^\s*[-*]\s+sfx\s*:\s*(.+)$", line, re.I)
        if m and frame is not None:
            for item in m.group(1).split(","):
                parts = item.strip().split("@")
                name = parts[0].strip()
                if not name or name.lower() in ("none", "-", "no"):
                    continue
                offset = float(parts[1]) if len(parts) > 1 and parts[1].strip() else 0.0
                vol = float(parts[2]) if len(parts) > 2 else DEFAULT_VOL.get(name, 0.3)
                cues.append((frame, name, offset, vol))
    return cues


def cmd_cues(project):
    project = Path(project).resolve()
    meta_path = project / "audio_meta.json"
    if not meta_path.exists():
        sys.exit("✗ audio_meta.json missing — run `takeloop voice` first")
    meta = json.loads(meta_path.read_text("utf-8"))
    cues = parse_cues((project / "STORYBOARD.md").read_text("utf-8"))
    (project / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    LIB = paths.sfx_lib()
    if not LIB.exists():
        cmd_library()
    out = []
    for frame, name, offset, vol in cues:
        src = LIB / f"{name}.wav"
        if not src.exists():
            print(f"⚠ unknown sfx '{name}' (frame {frame}) — skipped; known: {', '.join(DEFAULT_VOL)}")
            continue
        dst = project / "assets" / "sfx" / src.name
        shutil.copyfile(src, dst)
        out.append({"frame": frame, "file": f"assets/sfx/{src.name}", "offset_s": offset,
                    "duration_s": round(sf.info(dst).duration, 3), "volume": vol})
    meta["sfx"] = out
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    print(f"✓ sfx cues: {len(out)} → audio_meta.json")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="takeloop sfx")
    ap.add_argument("cmd", choices=["library", "cues"])
    ap.add_argument("--project", default=".")
    a = ap.parse_args(argv)
    cmd_library() if a.cmd == "library" else cmd_cues(a.project)


if __name__ == "__main__":
    main()
