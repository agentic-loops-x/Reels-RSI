"""Analyse the 2x2 memory ablation: per condition, rule violations in the FINAL output (all 13 rules run
offline, regardless of the switch used while making), finalize passes, renderer findings at the last pass,
script length, cost and time. Also the retro audit of what the agents would have been told.

  python ablation_analysis.py  [--json out.json]
"""
import glob, json, os, re, subprocess, sys, collections
from pathlib import Path

R = os.path.expanduser("~/.cache/reels-rsi-dev/venv/bin/reels")
HOMES = {"A-ruleson-lessonson": "~/.reels", "B-rulesoff-lessonson": "~/.reels",
         "C-ruleson-lessonsoff": "~/.cache/reels-ablation-home", "D-rulesoff-lessonsoff": "~/.cache/reels-ablation-home"}
TOPICS = ["sci-rainbow", "hist-chibi", "solve-chicken-rabbit", "en-seasons"]

def find_run(cond):
    home = Path(os.path.expanduser(HOMES[cond]))
    runs = sorted(glob.glob(str(home / "bench/runs" / f"*abl-{cond}")))
    return Path(runs[-1]) if runs else None

def lint(project):
    env = {k: v for k, v in os.environ.items() if k != "REELS_RULES"}
    out = subprocess.run([R, "lint", "--project", str(project), "--json"], capture_output=True, text=True, env=env).stdout
    try: return json.loads(out)
    except Exception: return []

def chars(script):
    return sum(len(re.sub(r"[\s，。？！、；：,.?!]", "", l[4:])) for l in open(script, encoding="utf-8") if l.startswith("    "))

rows = []
for cond in HOMES:
    run = find_run(cond)
    if not run: print(cond, "— no run yet"); continue
    summary = json.loads((run / "summary.json").read_text()) if (run / "summary.json").exists() else {}
    srows = {r["topic"]: r for r in summary.get("rows", [])}
    for t in TOPICS:
        p = run / t
        if not (p / "index.html").exists(): rows.append({"cond": cond, "topic": t, "made": False}); continue
        findings = lint(p)
        runs_f = p / ".reels/runs.jsonl"
        fins = [json.loads(l) for l in open(runs_f) if l.strip()] if runs_f.exists() else []
        fins = [r for r in fins if r.get("event") == "finalize"]
        last = fins[-1] if fins else {}
        fired = collections.Counter(x["rule"] for r in fins for x in r.get("rules", []))
        rows.append({"cond": cond, "topic": t, "made": True, "rendered": (p / "renders/video.mp4").exists(),
                     "violations": len(findings), "violation_rules": sorted(collections.Counter(f["rule"] for f in findings).items()),
                     "fired_during_authoring": dict(fired), "passes": len(fins),
                     "final_hf_errors": last.get("hf_errors", 0), "final_hf_warnings": last.get("hf_warnings", 0),
                     "frames": len(glob.glob(str(p / "compositions/frames/*.html"))),
                     "script_chars": chars(p / "SCRIPT.md") if (p / "SCRIPT.md").exists() else None,
                     "cost_usd": srows.get(t, {}).get("cost_usd"), "seconds": srows.get(t, {}).get("seconds"),
                     "turns": srows.get(t, {}).get("turns"), "composite": srows.get(t, {}).get("composite"),
                     "judge": srows.get(t, {}).get("judge"), "det": srows.get(t, {}).get("det"), "run": str(run)})

print(f"{'condition':22} {'topic':22} rend viol  passes hfE hfW frames chars  cost   sec  judge")
for r in rows:
    if not r.get("made"): print(f"{r['cond']:22} {r['topic']:22} (not made)"); continue
    print(f"{r['cond']:22} {r['topic']:22} {str(r['rendered'])[:1]:>4} {r['violations']:4}  {r['passes']:6} {r['final_hf_errors']:3} {r['final_hf_warnings']:3} {r['frames']:6} {r['script_chars'] or 0:5}  {r['cost_usd'] or 0:5.2f} {r['seconds'] or 0:5.0f}  {r['judge']}")
    if r["violation_rules"]: print(" " * 46, "violations:", r["violation_rules"], "| fired while authoring:", r["fired_during_authoring"])
print("\nper condition:")
for cond in HOMES:
    rs = [r for r in rows if r["cond"] == cond and r.get("made")]
    if not rs: continue
    print(f"  {cond:22} reels {len(rs)} rendered {sum(r['rendered'] for r in rs)} violations {sum(r['violations'] for r in rs)} "
          f"passes {sum(r['passes'] for r in rs)} hfE {sum(r['final_hf_errors'] for r in rs)} hfW {sum(r['final_hf_warnings'] for r in rs)} "
          f"cost ${sum(r['cost_usd'] or 0 for r in rs):.2f} judge {[r['judge'] for r in rs]}")
if "--json" in sys.argv:
    Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
