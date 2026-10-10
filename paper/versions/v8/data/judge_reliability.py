"""Judge reliability for the first evolve round (judge-only calls; no reels are made).

  absolute : re-score each of the 16 evolve reels 3x with claude-cli:sonnet  -> test-retest spread of the rubric
  pairwise : 8 topics x 3 votes, repeated 3x with sonnet; once each with haiku and opus
             (compare() swaps the order between votes; vote i shows A first when i is even)
Results -> ~/.reels/evolve/20261006-001942/reliability.json (appended per step, so a quota stop loses nothing)
"""
import json, sys, time, traceback
from pathlib import Path
sys.path.insert(0, "/Users/simonlin/code/vedio/reels-rsi.nosync/src")
from reels_rsi.rsi import score

RUNS = Path.home() / ".reels/bench/runs"
OUT = Path.home() / ".reels/evolve/20261006-001942/reliability.json"
TRAIN = ["sci-rainbow", "hist-chibi", "solve-chicken-rabbit", "en-seasons"]
HOLD = ["sci-tides", "hist-silk-road", "solve-buoyancy", "poem-jingyesi"]
def proj(kind, t):
    split = "" if t in TRAIN else "-holdout"
    return RUNS / f"evolve-20261006-001942-{kind}{split}" / t

res = json.loads(OUT.read_text()) if OUT.exists() else {"absolute": {}, "pairwise": []}
def save(): OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)

def retry(fn, what):
    for i in range(20):
        try:
            return fn()
        except Exception as e:  # quota / network: wait and retry
            msg = str(e)[:160]; log("retry", what, "-", msg)
            if "limit" in msg or "quota" in msg or "OAuth" in msg: time.sleep(1800)
            else: time.sleep(60)
    return None

# 1. absolute test-retest
for t in TRAIN + HOLD:
    for kind in ("base", "cand"):
        key = f"{kind}/{t}"
        got = res["absolute"].setdefault(key, [])
        while len(got) < 3:
            j = retry(lambda: score.judge(proj(kind, t), "claude-cli:sonnet"), key)
            if j is None: break
            got.append({"judge_score": score.judge_score(j), "frames": {f["id"]: [f.get(c) for c in score.CRITERIA] for f in j.get("frames", [])}})
            save(); log("absolute", key, got[-1]["judge_score"])

# 2. pairwise repeats and other judges
plan = [("claude-cli:sonnet", r) for r in range(3)] + [("claude-cli:haiku", 0), ("claude-cli:opus", 0)]
done = {(p["judge"], p["repeat"], p["topic"]) for p in res["pairwise"]}
for spec, rep in plan:
    for t in TRAIN + HOLD:
        if (spec, rep, t) in done: continue
        w = retry(lambda: score.compare(proj("base", t), proj("cand", t), spec, votes=3, detail=True), f"{spec} {t}")
        if w is None: continue
        picks = [x.split(":")[0] for x in w["why"]]          # "A"/"B" per vote, in vote order
        first = ["A" if i % 2 == 0 else "B" for i in range(len(picks))]
        res["pairwise"].append({"judge": spec, "repeat": rep, "topic": t, "base": w["A"], "cand": w["B"],
                                "picks": picks, "picked_first_shown": [p == f for p, f in zip(picks, first)], "why": w["why"]})
        save(); log("pairwise", spec, rep, t, w["A"], w["B"])
log("done")
