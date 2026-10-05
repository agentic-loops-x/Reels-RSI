"""Evolve: the skill rewrites itself, and keeps a change only if the benchmark says it is better.

    evofilm evolve [--baseline RUN_ID] [--harness claude --model opus] [--judge …] [--margin 3] [--yes] [--dry-run]
    evofilm evolve apply <evolve-id>      copy an accepted candidate over the installed skill (backup kept)

One round:
  1. baseline   the current skill's scores on the train topics (reuse --baseline, or run it now)
  2. propose    an agent reads the baseline's judge notes, findings and the lesson inbox, and edits a
                COPY of the skill (≤ 3 focused edits + CHANGES.md)                — prompts/propose.md
  3. evaluate   the candidate makes the same train films; it must beat the baseline mean composite
                by --margin, lose no topic by more than 10, and render at least as many films
  4. confirm    both versions make the holdout films; the candidate must not be worse there
                (guards against overfitting the train topics and judge-pleasing)
  5. report     report.md + skill.patch. Nothing changes until you run `evolve apply` — the human gate.

Cost: one round = up to 4 + 4 + 4 + 4 films. `--dry-run` prints the plan without running anything.
"""

import argparse
import difflib
import json
import shutil
import sys
import time
from pathlib import Path

from evofilm import agents, config, paths
from evofilm.rsi import bench, lessons


def evolve_root():
    p = paths.home() / "evolve"
    p.mkdir(parents=True, exist_ok=True)
    return p


def baseline_digest(summary):
    out = [f"mean composite {summary['mean']} ({summary['harness']}/{summary['model']})"]
    for r in summary["rows"]:
        out.append(f"\n### {r['topic']} ({r['genre']}): composite {r['composite']} · judge {r['judge']} · det {r['det']} · rendered {r.get('rendered')}")
        out += [f"- judge: {n}" for n in r.get("notes", [])]
        out += [f"- top issue: {t}" for t in r.get("top_issues", [])]
        if r.get("findings"):
            out.append("- findings: " + ", ".join(r["findings"]))
    return "\n".join(out)


def patch(base, cand):
    lines = []
    for f in sorted(cand.rglob("*")):
        if f.is_file() and f.suffix == ".md" and f.name != "CHANGES.md":
            rel = f.relative_to(cand)
            old = (base / rel).read_text("utf-8").splitlines(keepends=True) if (base / rel).exists() else []
            lines += difflib.unified_diff(old, f.read_text("utf-8").splitlines(keepends=True), f"a/{rel}", f"b/{rel}")
    return "".join(lines)


def require_complete(summary, what):
    if not summary.get("complete", True):
        sys.exit(f"✗ {what} bench run {summary['id']} is incomplete (not scored: {', '.join(summary.get('missing', []))}) — "
                 "its mean is not comparable. Fix the cause (quota, login, network) and rerun.")


def verdict(base, cand, margin):
    b = {r["topic"]: r for r in base["rows"]}
    worst = min((r["composite"] - b[r["topic"]]["composite"] for r in cand["rows"] if r["topic"] in b), default=0)
    renders = (sum(1 for r in cand["rows"] if r.get("rendered")), sum(1 for r in base["rows"] if r.get("rendered")))
    checks = {"mean +margin": cand["mean"] >= base["mean"] + margin, "no topic −10": worst > -10, "renders ≥": renders[0] >= renders[1]}
    return all(checks.values()), checks, worst


def cmd_evolve(argv):
    if argv and argv[0] == "apply":
        return apply(argv[1:])
    ap = argparse.ArgumentParser(prog="evofilm evolve", description="One benchmark-gated self-improvement round of the skill.")
    ap.add_argument("--baseline", default=None, help="reuse a bench run id of the current skill on the train split")
    ap.add_argument("--harness", default=None); ap.add_argument("--model", default=None)
    ap.add_argument("--judge", default=None); ap.add_argument("--margin", type=float, default=3.0)
    ap.add_argument("--max-edits", type=int, default=3)
    ap.add_argument("--skip-holdout", action="store_true")
    ap.add_argument("--yes", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    h, m = config.harness()
    harness, model = a.harness or h, a.model or m
    eid = time.strftime("%Y%m%d-%H%M%S")
    root = evolve_root() / eid
    current = paths.skill_dir()
    if a.dry_run:
        print(f"evolve {eid}: harness {harness}/{model} · judge {a.judge or config.role('judge')} · skill {current}")
        print(f"  1 baseline  {'reuse ' + a.baseline if a.baseline else 'bench run --split train (' + str(len(bench.topics('train'))) + ' films)'}")
        print(f"  2 propose   ≤{a.max_edits} edits to a copy of the skill (prompts/propose.md)")
        print(f"  3 evaluate  candidate on train; accept if mean ≥ baseline + {a.margin}, no topic −10, renders ≥")
        print(f"  4 confirm   holdout ({len(bench.topics('holdout'))} films × 2 versions)" if not a.skip_holdout else "  4 confirm   skipped")
        print("  5 report    report.md + skill.patch → `evofilm evolve apply <id>`")
        return
    if not a.yes:
        sys.exit("✗ evolve runs many full-permission agent sessions (≈ 16 films per round) — rerun with --yes, or --dry-run")
    root.mkdir(parents=True)
    common = dict(harness=harness, model=model, judge=a.judge)

    base = bench.load(a.baseline) if a.baseline else bench.run("train", label=f"evolve-{eid}-base", skill_dir=current, **common)
    require_complete(base, "baseline")
    cand = root / "skill"
    shutil.copytree(current, cand, ignore=shutil.ignore_patterns("__pycache__"))
    inbox = "\n".join(f"- [{m.get('kind')}/{m.get('scope')}] {b}" for st, p, m, b in lessons.all_lessons("inbox")) or "(empty)"
    prompt = agents.render_prompt("propose", candidate=cand, baseline=baseline_digest(base), inbox=inbox, max_edits=a.max_edits)
    print("▶ proposing skill edits …", flush=True)
    res = agents.run(harness, model, prompt, cwd=root, log_path=root / "propose.log")
    diff = patch(current, cand)
    (root / "skill.patch").write_text(diff, "utf-8")
    if not diff.strip():
        sys.exit(f"✗ the proposer changed nothing ({res['tail'][-300:]})")

    cs = bench.run("train", label=f"evolve-{eid}-cand", skill_dir=cand, **common)
    require_complete(cs, "candidate")
    ok, checks, worst = verdict(base, cs, a.margin)
    hold = None
    if ok and not a.skip_holdout:
        hb = bench.run("holdout", label=f"evolve-{eid}-base-holdout", skill_dir=current, **common)
        hc = bench.run("holdout", label=f"evolve-{eid}-cand-holdout", skill_dir=cand, **common)
        require_complete(hb, "holdout baseline"); require_complete(hc, "holdout candidate")
        hold = (hb["mean"], hc["mean"])
        checks["holdout ≥"] = hc["mean"] >= hb["mean"] - 1
        ok = ok and checks["holdout ≥"]
    changes = (cand / "CHANGES.md").read_text("utf-8") if (cand / "CHANGES.md").exists() else "(no CHANGES.md)"
    report = (f"# Evolve {eid} — {'ACCEPTED' if ok else 'REJECTED'}\n\n"
              f"harness {harness}/{model}\n\n| | baseline | candidate |\n|---|---|---|\n"
              f"| train mean | {base['mean']} | {cs['mean']} |\n"
              + (f"| holdout mean | {hold[0]} | {hold[1]} |\n" if hold else "")
              + f"\nworst topic delta: {worst:+.1f}\n\nchecks: " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items())
              + f"\n\n## Proposed changes\n\n{changes}\n\n## Patch\n\n```diff\n{diff}\n```\n")
    (root / "report.md").write_text(report, "utf-8")
    (root / "result.json").write_text(json.dumps({"id": eid, "accepted": ok, "checks": checks, "base": base["id"],
                                                  "cand": cs["id"], "holdout": hold}, indent=2), "utf-8")
    print(f"{'✓ ACCEPTED' if ok else '✗ rejected'}: train {base['mean']} → {cs['mean']}" + (f" · holdout {hold[0]} → {hold[1]}" if hold else ""))
    print(f"  report: {root / 'report.md'}" + (f"\n  apply:  evofilm evolve apply {eid}" if ok else ""))


def apply(argv):
    ap = argparse.ArgumentParser(prog="evofilm evolve apply")
    ap.add_argument("id")
    ap.add_argument("--force", action="store_true", help="apply even if the round was rejected")
    a = ap.parse_args(argv)
    root = evolve_root() / a.id
    result = json.loads((root / "result.json").read_text("utf-8"))
    if not result["accepted"] and not a.force:
        sys.exit("✗ this round was rejected by the benchmark (use --force to apply anyway)")
    target = paths.skill_dir()
    backup = root / "backup"
    shutil.copytree(target, backup, dirs_exist_ok=True)
    for f in (root / "skill").rglob("*.md"):
        if f.name == "CHANGES.md":
            continue
        dst = target / f.relative_to(root / "skill")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dst)
    print(f"✓ applied evolve {a.id} to {target} (backup: {backup})")
