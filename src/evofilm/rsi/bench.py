"""EvoFilm Bench: the same topics, any model, any skill version — one comparable number.

    evofilm bench topics
    evofilm bench run   [--split train|holdout|all] [--topics a,b] [--harness claude --model opus]
                         [--skill-dir DIR] [--judge provider:model] [--label NAME] [--yes] [--dry-run]
    evofilm bench report [--md LEADERBOARD.md]

A run = one headless agent session per topic (agents.py), then `score` on the result. Runs live in
~/.evofilm/bench/runs/<run-id>/ with summary.json; `report` turns them into a leaderboard.
Each film is a real agent session with full tool permissions — run it on a machine/container you
are happy to let an agent work in (`--yes` acknowledges this).
"""

import argparse
import json
import os
import re
import statistics
import sys
import time
import tomllib
from pathlib import Path

from evofilm import agents, config, paths
from evofilm.rsi import score as scoring


def topics(split="all", ids=None):
    items = tomllib.loads(paths.BENCH_TOPICS.read_text("utf-8"))["topic"]
    if ids:
        return [t for t in items if t["id"] in ids]
    return [t for t in items if split == "all" or t["split"] == split]


def runs_root():
    p = paths.home() / "bench" / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def style_for(genre):
    return {"history": "ink or atlas (your choice)", "solve": "chalk", "science": "deepspace or notebook (your choice)"}.get(genre, "your choice")


def run(split="train", ids=None, harness=None, model=None, skill_dir=None, judge=None, label=None,
        quality="draft", dry_run=False):
    h, m = config.harness()
    harness, model = harness or h, model or m
    skill = Path(skill_dir).resolve() if skill_dir else paths.skill_dir()
    judge = judge or config.role("judge")
    rid = f"{time.strftime('%Y%m%d-%H%M%S')}-{label or re.sub(r'[^a-z0-9]+', '-', f'{harness}-{model}'.lower())}"
    root = runs_root() / rid
    chosen = topics(split, ids)
    plan = {"id": rid, "harness": harness, "model": model, "skill": str(skill), "judge": judge, "split": split,
            "topics": [t["id"] for t in chosen], "quality": quality, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        t = chosen[0]
        print("\n--- prompt for", t["id"], "---\n" + make_prompt(t, root / t["id"], skill, quality))
        return None
    root.mkdir(parents=True)
    env = {**os.environ, "EVOFILM_SKILL_DIR": str(skill)}
    rows = []
    progress = root / "summary.json"          # written as we go: a crash never loses the films already made
    progress.write_text(json.dumps({**plan, "rows": rows, "mean": 0.0, "complete": False, "missing": plan["topics"]},
                                   ensure_ascii=False, indent=2), "utf-8")
    for t in chosen:
        proj = root / t["id"]
        print(f"▶ {t['id']} ({harness}/{model}) …", flush=True)
        res = agents.run(harness, model, make_prompt(t, proj, skill, quality), cwd=root, log_path=root / f"{t['id']}.log", env=env)
        row = {"topic": t["id"], "split": t["split"], "genre": t["genre"], "agent_ok": res["ok"], "seconds": res["seconds"],
               "cost_usd": res["cost_usd"], "turns": res["turns"]}
        infra = None if res["ok"] else infra_error(res["tail"])
        if infra:
            # not the skill's fault — a score here would be noise that evolve then trusts
            row.update(status="infra-error", error=infra, composite=None, det=None, judge=None, rendered=False,
                       notes=[], top_issues=[])
            rows.append(row)
            progress.write_text(json.dumps({**plan, "rows": rows, "mean": mean(rows), "complete": False},
                                           ensure_ascii=False, indent=2), "utf-8")
            print(f"  ✗ {infra} — topic not scored", flush=True)
            if INFRA_STOP.search(infra):
                print("  stopping: the remaining topics would fail the same way", flush=True)
                break
            continue
        rows.append(row)
        score_row(row, proj, judge)
        progress.write_text(json.dumps({**plan, "rows": rows, "mean": mean(rows), "complete": False},
                                       ensure_ascii=False, indent=2), "utf-8")
        print(f"  composite {row['composite']} · det {row['det']} · judge {row['judge']} · {row['seconds']}s"
              + (f" · ${row['cost_usd']:.2f}" if row.get("cost_usd") else ""))
    summary = {**plan, "finished": time.strftime("%Y-%m-%dT%H:%M:%S"), "rows": rows}
    return save(root, summary, plan["topics"])


def score_row(row, proj, judge):
    try:
        s = scoring.score(proj, judge, use_judge=bool(judge)) if (proj / "index.html").exists() else None
    except Exception as e:  # noqa: BLE001 — a scoring crash must not lose the film or the run
        row.update(status="score-error", error=f"{type(e).__name__}: {e}"[:300], composite=None, det=None, judge=None,
                   rendered=(proj / "renders" / "video.mp4").exists(), notes=[], top_issues=[])
        print(f"  ✗ scoring failed: {row['error']} — rescore later with `evofilm bench rescore`", flush=True)
        return row
    if s is None:
        row.update(composite=0.0, det=0.0, judge=None, rendered=False, notes=[], top_issues=["no project produced"])
    else:
        row.update(status="scored", composite=s["composite"], det=s["det_score"], judge=s["judge_score"],
                   rendered=s["deterministic"]["rendered"],
                   notes=[f.get("note", "") for f in (s.get("judge") or {}).get("frames", []) if f.get("note")][:6],
                   top_issues=(s.get("judge") or {}).get("top_issues", []),
                   findings=last_findings(proj))
    return row


def save(root, summary, topic_ids):
    rows = summary["rows"]
    rid = summary["id"]
    scored = [r["topic"] for r in rows if r.get("composite") is not None]
    missing = [t for t in topic_ids if t not in scored]
    summary.update(mean=mean(rows), complete=not missing, missing=missing)
    (root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
    if missing:
        print(f"⚠ bench {rid}: INCOMPLETE — not scored: {', '.join(missing)}. Mean {summary['mean']} over "
              f"{len(scored)} topic(s) is not comparable; rerun those topics. → {root}")
    else:
        print(f"✓ bench {rid}: mean composite {summary['mean']} over {len(rows)} topic(s) → {root}")
    return summary


# Failures of the environment, not of the film: quota, login, network, provider outages.
INFRA = re.compile(r"session limit|usage limit|rate.?limit|quota|credit balance|Failed to authenticate|"
                   r"OAuth|not logged in|overloaded|ECONNRESET|ETIMEDOUT|network error|503 Service|529", re.I)
INFRA_STOP = re.compile(r"limit|quota|credit|authenticate|OAuth|logged in", re.I)


def infra_error(tail):
    m = INFRA.search(tail or "")
    if not m:
        return None
    line = next((ln.strip() for ln in (tail or "").splitlines() if m.group(0) in ln), m.group(0))
    return line[:200]


def rescore(rid, judge=None):
    """Score the films a run already made again — after a scoring crash, or to re-judge with another
    judge (then compare only runs scored by the same judge). Agent infra errors stay unscored."""
    summary = load(rid)
    root = runs_root() / rid
    judge = judge or summary.get("judge") or config.role("judge")
    summary["judge"] = judge
    done = {r["topic"]: r for r in summary.get("rows", [])}
    rows = []
    for tid in summary["topics"]:
        row = done.get(tid) or {"topic": tid, "agent_ok": None}
        t = next((x for x in topics() if x["id"] == tid), {})
        row.setdefault("split", t.get("split")); row.setdefault("genre", t.get("genre"))
        if row.get("status") != "infra-error":
            print(f"▶ rescoring {tid} …", flush=True)
            score_row(row, root / tid, judge)
            print(f"  composite {row['composite']} · det {row['det']} · judge {row['judge']}")
        rows.append(row)
    summary["rows"] = rows
    summary["rescored"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return save(root, summary, summary["topics"])


def last_findings(proj):
    from evofilm.rsi import runlog
    fin = next((r for r in reversed(runlog.read(proj)) if r.get("event") == "finalize"), {})
    return sorted({f"hyperframes/{i['code']}" for i in fin.get("hf_findings", [])} | {f"rule/{f['rule']}" for f in fin.get("rules", [])})


def make_prompt(t, proj, skill, quality):
    return agents.render_prompt("make", skill=skill, topic=t["prompt"], length=t.get("length", 30),
                                aspect=t.get("aspect", "16:9"), style=style_for(t.get("genre")), dir=proj, quality=quality)


def mean(rows):
    vals = [r["composite"] for r in rows if r.get("composite") is not None]
    return round(statistics.mean(vals), 1) if vals else 0.0


def load(rid):
    p = runs_root() / rid / "summary.json"
    if not p.exists():
        sys.exit(f"✗ no bench run {rid}")
    return json.loads(p.read_text("utf-8"))


def all_runs():
    return [json.loads(p.read_text("utf-8")) for p in sorted(runs_root().glob("*/summary.json"))]


def report(md=None):
    runs = all_runs()
    lines = ["| run | harness / model | skill | split | topics | rendered | composite | judge | det | avg time | avg cost |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in sorted(runs, key=lambda s: -s["mean"]):
        rows = [r for r in s["rows"] if r.get("composite") is not None]
        if not rows:
            continue
        if not s.get("complete", True):
            s = {**s, "id": s["id"] + " ⚠ incomplete"}
        def avg(key, fmt="{:.1f}", scale=1):
            vals = [r[key] / scale for r in rows if isinstance(r.get(key), (int, float))]
            return fmt.format(statistics.mean(vals)) if vals else "-"
        lines.append(f"| {s['id']} | {s['harness']} / {s['model']} | {Path(s['skill']).name} | {s['split']} | {len(rows)} | "
                     f"{sum(1 for r in rows if r.get('rendered'))}/{len(rows)} | **{s['mean']}** | "
                     f"{avg('judge')} | {avg('det')} | {avg('seconds', '{:.1f} min', 60)} | {avg('cost_usd', '${:.2f}')} |")
    text = "# EvoFilm Bench — leaderboard\n\n" + "\n".join(lines) + "\n"
    if md:
        Path(md).write_text(text, "utf-8")
        print(f"✓ {md}")
    print(text if runs else "(no bench runs yet — `evofilm bench run --split train --yes`)")


def cmd_bench(argv):
    ap = argparse.ArgumentParser(prog="evofilm bench", description="Score models and skill versions on fixed topics.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("topics")
    r = sub.add_parser("run")
    r.add_argument("--split", default="train", choices=["train", "holdout", "all"])
    r.add_argument("--topics", default=None, help="comma list of topic ids")
    r.add_argument("--harness", default=None); r.add_argument("--model", default=None)
    r.add_argument("--skill-dir", default=None); r.add_argument("--judge", default=None)
    r.add_argument("--label", default=None); r.add_argument("--quality", default="draft", choices=["draft", "standard", "high"])
    r.add_argument("--yes", action="store_true", help="I understand each topic runs a full-permission agent session")
    r.add_argument("--dry-run", action="store_true")
    rp = sub.add_parser("report"); rp.add_argument("--md", default=None)
    rs = sub.add_parser("rescore", help="score an existing run's films again (no new films)")
    rs.add_argument("run_id"); rs.add_argument("--judge", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "topics":
        for t in topics():
            print(f"{t['id']:22} {t['split']:8} {t['genre']:8} {t.get('length', 30)}s {t.get('aspect', '16:9'):5} {t['prompt']}")
    elif a.cmd == "run":
        if not a.yes and not a.dry_run:
            sys.exit("✗ each topic runs a headless agent with full tool permissions and costs model usage — rerun with --yes (or --dry-run)")
        run(a.split, a.topics.split(",") if a.topics else None, a.harness, a.model, a.skill_dir, a.judge, a.label, a.quality, a.dry_run)
    elif a.cmd == "rescore":
        rescore(a.run_id, a.judge)
    else:
        report(a.md)
