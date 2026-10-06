"""Build the mutant reels for this task from a passing output folder; each must FAIL its target test.

    python make_mutants.py <passing-output-dir> <mutants-dir>
"""
import re, shutil, subprocess, sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
srt = (src / "subtitles.srt").read_text("utf-8")

def mutant(name, srt_text=None, video_filter=None, extra=()):
    d = dst / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "subtitles.srt").write_text(srt_text if srt_text is not None else srt, "utf-8")
    if video_filter is None and not extra:
        shutil.copyfile(src / "video.mp4", d / "video.mp4")
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src / "video.mp4"), *extra,
                        *(["-vf", video_filter] if video_filter else []), *([] if "-filter:a" in extra else ["-c:a", "copy"]), str(d / "video.mp4")], check=True)
    print("  mutant:", name)

# 1. wrong answer said: rabbits 13 / chickens 22
mutant("wrong-answer", srt.replace("十二", "十三").replace("二十三", "二十二"))
# 2. off-audience method: the narration sets up an equation
mutant("uses-equation", srt.replace("先画三十五个头", "设兔有 x 只，列方程，先画三十五个头", 1))
# 3. answer never on screen: the last 40 % of the picture is frozen on the 55 % frame
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(src / "video.mp4")], capture_output=True, text=True).stdout)
t = dur * 0.55
mutant("answer-hidden", video_filter=f"trim=0:{t:.2f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={dur - t:.2f}")
# 4. far over length: 2× slower picture and sound
mutant("too-long", extra=("-filter:a", "atempo=0.5"), video_filter="setpts=2.0*PTS")
