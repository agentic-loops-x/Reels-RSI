"""Weaker director (claude-cli haiku), rules on vs off, 4 train topics: rendered?, violations in the final
output (all 13 rules offline), rule firings during authoring, passes, renderer errors/warnings at the last
pass, det/judge, cost."""
import glob, json, os, collections, subprocess
from pathlib import Path
R = os.path.expanduser("~/.cache/reels-rsi-dev/venv/bin/reels")
TOPICS = ["sci-rainbow", "hist-chibi", "solve-chicken-rabbit", "en-seasons"]
def lint(p):
    env = {k: v for k, v in os.environ.items() if k != "REELS_RULES"}
    out = subprocess.run([R, "lint", "--project", str(p), "--json"], capture_output=True, text=True, env=env).stdout
    try: return json.loads(out)
    except Exception: return []
rows = []
for cond in ("H1-ruleson", "H2-rulesoff"):
    runs = sorted(glob.glob(os.path.expanduser(f"~/.reels/bench/runs/*dir-haiku-{cond}")))
    if not runs: continue
    run = Path(runs[-1]); summ = json.loads((run / "summary.json").read_text()); srows = {r["topic"]: r for r in summ["rows"]}
    for t in TOPICS:
        p = run / t
        if not (p / "index.html").exists():
            rows.append({"cond": cond, "topic": t, "made": False, "status": srows.get(t, {}).get("status")}); continue
        f = p / ".reels/runs.jsonl"
        fins = [json.loads(l) for l in open(f) if l.strip()] if f.exists() else []
        fins = [r for r in fins if r.get("event") == "finalize"]; last = fins[-1] if fins else {}
        viol = lint(p)
        rows.append({"cond": cond, "topic": t, "made": True, "rendered": (p / "renders/video.mp4").exists(),
                     "violations": collections.Counter(x["rule"] for x in viol), "fired": collections.Counter(x["rule"] for r in fins for x in r.get("rules", [])),
                     "passes": len(fins), "hfE": last.get("hf_errors", 0), "hfW": last.get("hf_warnings", 0),
                     "frames": len(glob.glob(str(p / "compositions/frames/*.html"))), "det": srows.get(t, {}).get("det"),
                     "judge": srows.get(t, {}).get("judge"), "composite": srows.get(t, {}).get("composite"),
                     "cost": srows.get(t, {}).get("cost_usd"), "sec": srows.get(t, {}).get("seconds"), "turns": srows.get(t, {}).get("turns")})
print(f"{'cond':12} {'topic':22} made rend frames passes hfE hfW  det  judge comp   cost  violations | fired")
for r in rows:
    if not r["made"]: print(f"{r['cond']:12} {r['topic']:22} no   ({r['status']})"); continue
    print(f"{r['cond']:12} {r['topic']:22} yes  {str(r['rendered'])[0]:>4} {r['frames']:6} {r['passes']:6} {r['hfE']:3} {r['hfW']:3} {r['det'] or 0:5.0f} {r['judge'] or 0:5.1f} {r['composite'] or 0:5.1f} {r['cost'] or 0:6.2f}  {dict(r['violations'])} | {dict(r['fired'])}")
for cond in ("H1-ruleson", "H2-rulesoff"):
    rs = [r for r in rows if r["cond"] == cond and r["made"]]
    if rs: print(f"{cond}: made {len(rs)} rendered {sum(r['rendered'] for r in rs)} violations {sum(sum(r['violations'].values()) for r in rs)} fired {sum(sum(r['fired'].values()) for r in rs)} passes {sum(r['passes'] for r in rs)} hfE {sum(r['hfE'] for r in rs)} hfW {sum(r['hfW'] for r in rs)} mean det {sum(r['det'] or 0 for r in rs)/len(rs):.0f} cost ${sum(r['cost'] or 0 for r in rs):.2f}")
json.dump(rows, open(os.path.expanduser("~/.reels/evolve/haiku_results.json"), "w"), ensure_ascii=False, indent=1, default=dict)
