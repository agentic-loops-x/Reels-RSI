"""Judge and deterministic scores of the 48 learning-curve reels: per arm, paired by topic, and trend."""
import json, random, statistics as st
from pathlib import Path
random.seed(2)
C = Path.home() / ".reels/curve"
topics = [l.strip().split("|")[0] for l in open(C / "topics.txt", encoding="utf-8") if l.strip()]
rows = []
for i, g in enumerate(topics, 1):
    for arm in ("ON", "OFF"):
        f = C / arm / f"{i:02d}-{g}" / ".reels/score.json"
        if not f.exists(): continue
        s = json.loads(f.read_text())
        rows.append({"i": i, "arm": arm, "genre": g, "judge": s.get("judge_score"), "det": s.get("det_score"), "composite": s.get("composite")})
def spearman(x, y):
    rx = [sorted(x).index(v) + 1 for v in x]; ry = [sorted(y).index(v) + 1 for v in y]
    n = len(x); mx = sum(rx) / n; my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry)); den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return num / den if den else 0
for key in ("judge", "det", "composite"):
    for arm in ("ON", "OFF"):
        rs = [r for r in rows if r["arm"] == arm and r[key] is not None]
        if len(rs) < 3: continue
        print(f"{key:9} {arm:3} n={len(rs):2} mean {st.mean(r[key] for r in rs):5.1f}  first half {st.mean(r[key] for r in rs if r['i'] <= 12):5.1f} second half {st.mean(r[key] for r in rs if r['i'] > 12):5.1f}  trend rho {spearman([r['i'] for r in rs], [r[key] for r in rs]):+.2f}")
    ON = {r["i"]: r[key] for r in rows if r["arm"] == "ON" and r[key] is not None}
    OFF = {r["i"]: r[key] for r in rows if r["arm"] == "OFF" and r[key] is not None}
    common = sorted(set(ON) & set(OFF))
    if len(common) >= 3:
        d = [ON[i] - OFF[i] for i in common]; obs = st.mean(d); c = 0; N = 100000
        for _ in range(N):
            m = st.mean(x * random.choice((1, -1)) for x in d); c += abs(m) >= abs(obs) - 1e-12
        print(f"{key:9} paired ON-OFF over {len(common)} topics: {obs:+.2f}  p={c/N:.3f}  ON higher on {sum(x>0 for x in d)}, lower on {sum(x<0 for x in d)}")
(C / "scores.json").write_text(json.dumps(rows, indent=1))
