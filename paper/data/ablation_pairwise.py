"""Position-balanced pairwise judging between ablation conditions on the 4 train topics.
   lessons effect : A (rules on, lessons on) vs C (rules on, lessons off); B vs D (rules off)
   rules effect   : A vs B (lessons on); C vs D (lessons off)
4 votes per pair (2 per order) with claude-cli:sonnet. Results -> ~/.reels/evolve/ablation_pairwise.json"""
import json, glob, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/simonlin/Desktop/code/vedio/reels-rsi.nosync/src")
from reels_rsi.rsi import score
HOMES = {"A": "~/.reels", "B": "~/.reels", "C": "~/.cache/reels-ablation-home", "D": "~/.cache/reels-ablation-home"}
LABEL = {"A": "A-ruleson-lessonson", "B": "B-rulesoff-lessonson", "C": "C-ruleson-lessonsoff", "D": "D-rulesoff-lessonsoff"}
TOPICS = ["sci-rainbow", "hist-chibi", "solve-chicken-rabbit", "en-seasons"]
def proj(c, t):
    runs = sorted(glob.glob(os.path.expanduser(f"{HOMES[c]}/bench/runs/*abl-{LABEL[c]}")))
    return Path(runs[-1]) / t
OUT = Path.home() / ".reels/evolve/ablation_pairwise.json"
res = json.loads(OUT.read_text()) if OUT.exists() else []
done = {(r["pair"], r["topic"]) for r in res}
for pair, what in (("A-C", "lessons (rules on)"), ("B-D", "lessons (rules off)"), ("A-B", "rules (lessons on)"), ("C-D", "rules (lessons off)")):
    x, y = pair.split("-")
    for t in TOPICS:
        if (pair, t) in done: continue
        px, py = proj(x, t), proj(y, t)
        if not (px / "renders/video.mp4").exists() or not (py / "renders/video.mp4").exists():
            print("skip", pair, t, "(not rendered)"); continue
        for i in range(10):
            try:
                w = score.compare(px, py, "claude-cli:sonnet", votes=4, detail=True); break
            except Exception as e:
                print("retry", str(e)[:120]); time.sleep(1800 if "limit" in str(e) else 60)
        else:
            continue
        res.append({"pair": pair, "what": what, "topic": t, x: w["A"], y: w["B"], "first": w["first"], "why": w["why"]})
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
        print(time.strftime("%H:%M:%S"), pair, t, f"{x} {w['A']} : {y} {w['B']}", flush=True)
print("done")
