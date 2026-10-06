"""Learning curve: per reel (in order) and per arm — finalize passes, renderer errors/warnings at the
first and the last pass, rule firings, cost, time, deterministic score, lessons in the ON store at that point.
Compares ON (lessons auto-accepted after each reel) vs OFF (no lessons). Writes curve.json and a figure.

  python curve_analysis.py [--png curve.png]
"""
import glob, json, os, re, sys, statistics as st
from pathlib import Path
C = Path.home() / ".reels/curve"
topics = [l.strip().split("|") for l in open(C / "topics.txt", encoding="utf-8") if l.strip()]
rows = []
for i, (genre, topic) in enumerate(topics, 1):
    for arm in ("ON", "OFF"):
        d = C / arm / f"{i:02d}-{genre}"
        if not (d / "index.html").exists(): continue
        f = d / ".reels/runs.jsonl"
        fins = [json.loads(l) for l in open(f) if l.strip()] if f.exists() else []
        fins = [r for r in fins if r.get("event") == "finalize"]
        rend = next((r for r in reversed(fins) if r.get("event") == "render"), None)
        first, last = (fins[0] if fins else {}), (fins[-1] if fins else {})
        rows.append({"i": i, "arm": arm, "genre": genre, "rendered": (d / "renders/video.mp4").exists(),
                     "passes": len(fins), "hfE_first": first.get("hf_errors", 0), "hfW_first": first.get("hf_warnings", 0),
                     "hfE_last": last.get("hf_errors", 0), "hfW_last": last.get("hf_warnings", 0),
                     "rule_firings": sum(len(r.get("rules", [])) for r in fins),
                     "frames": len(glob.glob(str(d / "compositions/frames/*.html")))})
if not rows: sys.exit("no reels yet")
by = {("ON", r["i"]): r for r in rows if r["arm"] == "ON"} | {("OFF", r["i"]): r for r in rows if r["arm"] == "OFF"}
print(f"{'i':>2} {'genre':5} | {'ON passes':>9} {'E1':>3} {'W1':>3} {'Elast':>5} {'Wlast':>5} {'rules':>5} | {'OFF passes':>10} {'E1':>3} {'W1':>3} {'Elast':>5} {'Wlast':>5} {'rules':>5}")
for i, (genre, _) in enumerate(topics, 1):
    a, b = by.get(("ON", i)), by.get(("OFF", i))
    fa = f"{a['passes']:9} {a['hfE_first']:3} {a['hfW_first']:3} {a['hfE_last']:5} {a['hfW_last']:5} {a['rule_firings']:5}" if a else " " * 35
    fb = f"{b['passes']:10} {b['hfE_first']:3} {b['hfW_first']:3} {b['hfE_last']:5} {b['hfW_last']:5} {b['rule_firings']:5}" if b else ""
    print(f"{i:2} {genre:5} | {fa} | {fb}")
def half(arm, lo, hi, key):
    v = [r[key] for r in rows if r["arm"] == arm and lo <= r["i"] <= hi]
    return st.mean(v) if v else float("nan")
n = max(r["i"] for r in rows)
print(f"\nreels so far: ON {sum(r['arm']=='ON' for r in rows)}  OFF {sum(r['arm']=='OFF' for r in rows)}")
for key in ("passes", "hfE_first", "hfW_first", "hfW_last", "rule_firings"):
    print(f"  {key:10} ON first half {half('ON',1,n//2,key):5.2f} second half {half('ON',n//2+1,n,key):5.2f} | OFF first half {half('OFF',1,n//2,key):5.2f} second half {half('OFF',n//2+1,n,key):5.2f}")
(C / "curve.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
if "--png" in sys.argv:
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(11, 3))
        for arm, c in (("ON", "C0"), ("OFF", "C1")):
            rs = sorted((r for r in rows if r["arm"] == arm), key=lambda r: r["i"])
            for k, key, lab in ((0, "hfW_first", "renderer findings, first pass"), (1, "passes", "finalize passes"), (2, "rule_firings", "rule firings")):
                ax[k].plot([r["i"] for r in rs], [r[key] for r in rs], "o-", ms=3, color=c, label=f"lessons {arm.lower()}"); ax[k].set_title(lab, fontsize=9); ax[k].set_xlabel("reel")
        ax[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(sys.argv[sys.argv.index("--png") + 1], dpi=160)
    except ImportError:
        print("matplotlib not installed; no figure")
