"""Summarise reliability.json: absolute test-retest spread, pairwise repeat stability, judge agreement,
position bias."""
import json, statistics as st, itertools, collections
from pathlib import Path
d = json.loads((Path.home() / ".reels/evolve/20261006-001942/reliability.json").read_text())
TRAIN = ["sci-rainbow", "hist-chibi", "solve-chicken-rabbit", "en-seasons"]
HOLD = ["sci-tides", "hist-silk-road", "solve-buoyancy", "poem-jingyesi"]

print("== absolute rubric, 3 re-scores per reel (claude-cli:sonnet)")
sds, diffs = [], {}
for t in TRAIN + HOLD:
    b = [x["judge_score"] for x in d["absolute"].get(f"base/{t}", []) if x["judge_score"] is not None]
    c = [x["judge_score"] for x in d["absolute"].get(f"cand/{t}", []) if x["judge_score"] is not None]
    sb = st.pstdev(b) if len(b) > 1 else float("nan"); sc = st.pstdev(c) if len(c) > 1 else float("nan")
    if len(b) > 1: sds.append(sb)
    if len(c) > 1: sds.append(sc)
    mb = st.mean(b) if b else float("nan"); mc = st.mean(c) if c else float("nan")
    diffs[t] = mc - mb
    print(f"  {t:22} base {b} sd {sb:4.1f} | cand {c} sd {sc:4.1f} | cand-base {mc-mb:+5.1f}")
if sds:
    print(f"  within-reel SD: median {st.median(sds):.1f}, max {max(sds):.1f}  (range of the rubric: 20-100)")
    tb = [st.mean([x['judge_score'] for x in d['absolute'][f'base/{t}'] if x['judge_score'] is not None]) for t in TRAIN if f'base/{t}' in d['absolute']]
    tc = [st.mean([x['judge_score'] for x in d['absolute'][f'cand/{t}'] if x['judge_score'] is not None]) for t in TRAIN if f'cand/{t}' in d['absolute']]
    if tb and tc: print(f"  train means over re-scores: base {st.mean(tb):.1f} cand {st.mean(tc):.1f}")
    hb = [st.mean([x['judge_score'] for x in d['absolute'][f'base/{t}'] if x['judge_score'] is not None]) for t in HOLD if f'base/{t}' in d['absolute']]
    hc = [st.mean([x['judge_score'] for x in d['absolute'][f'cand/{t}'] if x['judge_score'] is not None]) for t in HOLD if f'cand/{t}' in d['absolute']]
    if hb and hc: print(f"  holdout means over re-scores: base {st.mean(hb):.1f} cand {st.mean(hc):.1f}")

print("\n== pairwise (3 votes per topic per repeat)")
byjudge = collections.defaultdict(list)
for p in d["pairwise"]: byjudge[(p["judge"], p["repeat"])].append(p)
for (j, r), ps in sorted(byjudge.items()):
    tr = [p for p in ps if p["topic"] in TRAIN]; ho = [p for p in ps if p["topic"] in HOLD]
    v = lambda L: (sum(p["base"] for p in L), sum(p["cand"] for p in L))
    firsts = [x for p in ps for x in p["picked_first_shown"]]
    print(f"  {j:18} repeat {r}: train base:cand {v(tr)}  holdout {v(ho)}  topics won by cand {sum(p['cand']>p['base'] for p in ps)}/{len(ps)}  picked-first-shown {sum(firsts)}/{len(firsts)}")
# topic-level agreement between (judge, repeat) runs: does the majority winner agree?
runs = sorted(byjudge)
print("\n== topic winners per run (C = candidate, B = baseline, - = tie)")
for t in TRAIN + HOLD:
    row = []
    for k in runs:
        p = next((p for p in byjudge[k] if p["topic"] == t), None)
        row.append("?" if p is None else ("C" if p["cand"] > p["base"] else "B" if p["base"] > p["cand"] else "-"))
    print(f"  {t:22} " + " ".join(f"{k[0].split(':')[1][:5]}{k[1]}={w}" for k, w in zip(runs, row)))
pairs = list(itertools.combinations(runs, 2))
if pairs:
    agree = []
    for a, b in pairs:
        wa = {p["topic"]: p["cand"] > p["base"] for p in byjudge[a]}; wb = {p["topic"]: p["cand"] > p["base"] for p in byjudge[b]}
        common = set(wa) & set(wb)
        if common: agree.append(sum(wa[t] == wb[t] for t in common) / len(common))
    if agree: print(f"\n  mean topic-winner agreement between runs: {st.mean(agree):.2f} ({len(pairs)} run pairs)")
