"""Evolve: the skill rewrites itself, and keeps a change only if the benchmark says it is better.

    reels evolve [--baseline RUN_ID] [--harness claude --model opus] [--judge …] [--margin 3] [--yes] [--dry-run]
    reels evolve apply <evolve-id>      copy an accepted candidate over the installed skill (backup kept)

One round:
  1. baseline   the current skill makes the train reels (reuse --baseline, or run it now)
  2. propose    an agent reads the baseline's judge notes, findings and the lesson inbox, and edits a
                COPY of the skill (≤ 3 focused edits + CHANGES.md)                — prompts/propose.md
  3. evaluate   the candidate makes the same train topics. Per topic the judge sees both reels blind,
                order swapped between 3 votes (`score.compare`). The candidate must win most of the
                votes, render at least as many reels and lose no topic by more than 10 composite points.
                Absolute 1–5 scores from one judge are noisy; "which of these two is better" is not.
  4. confirm    both versions make the holdout topics; the candidate must win at least half the votes
                there (guards against overfitting the train topics)
  5. report     report.md (per topic: votes, the judge's reasons, a side-by-side image of both reels)
                + skill.patch. Nothing changes until you run `evolve apply` — the human gate.

Cost: one round = 4 + 4 + 4 + 4 reels, plus ~40 judge calls. A quota/login stop pauses the round;
`reels evolve --resume <id>` continues it. `--dry-run` prints the plan without running anything.
"""

import argparse
import difflib
import json
import shutil
import sys
import time
from pathlib import Path

from reels_rsi import agents, config, paths
from reels_rsi.rsi import bench, lessons


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
        if f.is_file() and f.suffix == ".md" and f.name not in ("CHANGES.md", "TOOL-BUGS.md"):
            rel = f.relative_to(cand)
            old = (base / rel).read_text("utf-8").splitlines(keepends=True) if (base / rel).exists() else []
            lines += difflib.unified_diff(old, f.read_text("utf-8").splitlines(keepends=True), f"a/{rel}", f"b/{rel}")
    return "".join(lines)


def require_complete(summary, what):
    if not summary.get("complete", True):
        sys.exit(f"✗ {what} bench run {summary['id']} is incomplete (not scored: {', '.join(summary.get('missing', []))}) — "
                 "its mean is not comparable. Fix the cause (quota, login, network) and rerun.")


def verdict(base, cand, pairs):
    b = {r["topic"]: r for r in base["rows"]}
    worst = min((r["composite"] - b[r["topic"]]["composite"] for r in cand["rows"] if r["topic"] in b), default=0)
    renders = (sum(1 for r in cand["rows"] if r.get("rendered")), sum(1 for r in base["rows"] if r.get("rendered")))
    cv, bv = votes(pairs)
    checks = {f"pairwise: candidate wins more than half the votes ({cv}–{bv})": cv > bv, "no topic −10": worst > -10,
              "renders ≥": renders[0] >= renders[1]}
    return all(checks.values()), checks, worst


def votes(pairs):
    return sum(p["cand"] for p in pairs.values()), sum(p["base"] for p in pairs.values())


def pairwise(root, st, tag, base, cand, n=4):
    """Blind pairwise judgments per topic, cached in state.json so a resumed round never re-asks."""
    from reels_rsi import llm
    from reels_rsi.rsi import score
    cache = st.setdefault("pairwise", {}).setdefault(tag, {})
    rows_b = {r["topic"]: r for r in base["rows"]}
    for r in cand["rows"]:
        t = r["topic"]
        if t in cache or t not in rows_b:
            continue
        pb, pc = bench.runs_root() / base["id"] / t, bench.runs_root() / cand["id"] / t
        rb, rc = rows_b[t].get("rendered"), r.get("rendered")
        if not (rb and rc):                      # a reel that never rendered loses every vote
            cache[t] = {"base": n if rb else 0, "cand": n if rc else 0, "why": ["only one version rendered"]}
        else:
            print(f"▶ pairwise {tag}/{t} …", flush=True)
            try:
                w = score.compare(pb, pc, st["judge"], votes=n, detail=True)
            except llm.LLMError as e:
                save_state(root, st)
                stopped(root, f"pairwise judging ({str(e)[:120]})")
            cache[t] = {"base": w["A"], "cand": w["B"],
                        "why": [x.replace("A:", "baseline:", 1).replace("B:", "candidate:", 1) for x in w["why"]]}
        img = score.side_by_side(pb, pc, root / "compare" / f"{tag}-{t}.jpg")
        cache[t]["image"] = f"compare/{tag}-{t}.jpg" if img else None
        save_state(root, st)
        print(f"  baseline {cache[t]['base']} · candidate {cache[t]['cand']}", flush=True)
    return cache


def cmd_evolve(argv):
    if argv and argv[0] == "apply":
        return apply(argv[1:])
    ap = argparse.ArgumentParser(prog="reels evolve", description="One benchmark-gated self-improvement round of the skill.")
    ap.add_argument("--baseline", default=None, help="reuse a bench run id of the current skill on the train split")
    ap.add_argument("--harness", default=None); ap.add_argument("--model", default=None)
    ap.add_argument("--judge", default=None); ap.add_argument("--margin", type=float, default=3.0, help=argparse.SUPPRESS)  # kept for old scripts
    ap.add_argument("--max-edits", type=int, default=3)
    ap.add_argument("--skip-holdout", action="store_true")
    ap.add_argument("--resume", default=None, metavar="EVOLVE_ID", help="continue a round stopped by quota/login")
    ap.add_argument("--yes", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.resume:
        root = evolve_root() / a.resume
        if not (root / "state.json").exists():
            sys.exit(f"✗ no evolve round {a.resume}")
        st = json.loads((root / "state.json").read_text("utf-8"))
        print(f"↻ resuming evolve {a.resume} ({st['harness']}/{st['model']})", flush=True)
        return run_round(root, st)
    h, m = config.harness()
    harness, model = a.harness or h, a.model or m
    eid = time.strftime("%Y%m%d-%H%M%S")
    current = paths.skill_dir()
    if a.dry_run:
        print(f"evolve {eid}: harness {harness}/{model} · judge {a.judge or config.role('judge')} · skill {current}")
        print(f"  1 baseline  {'reuse ' + a.baseline if a.baseline else 'bench run --split train (' + str(len(bench.topics('train'))) + ' reels)'}")
        print(f"  2 propose   ≤{a.max_edits} edits to a copy of the skill (prompts/propose.md)")
        print("  3 evaluate  candidate on train; blind pairwise per topic (3 votes, order swapped) — accept if it wins")
        print("              most votes, no topic −10 composite, renders ≥")
        print(f"  4 confirm   holdout ({len(bench.topics('holdout'))} reels × 2 versions, candidate wins ≥ half the votes)" if not a.skip_holdout else "  4 confirm   skipped")
        print("  5 report    report.md + skill.patch → `reels evolve apply <id>`")
        print("  a quota/login stop saves the round: `reels evolve --resume <id>` continues it")
        return
    if not a.yes:
        sys.exit("✗ evolve runs many full-permission agent sessions (≈ 16 reels per round) — rerun with --yes, or --dry-run")
    root = evolve_root() / eid
    root.mkdir(parents=True)
    st = {"id": eid, "harness": harness, "model": model, "judge": a.judge or config.role("judge"), "margin": a.margin,
          "max_edits": a.max_edits, "skip_holdout": a.skip_holdout, "current": str(current),
          "runs": {"base": a.baseline or f"evolve-{eid}-base", "cand": f"evolve-{eid}-cand",
                   "hold_base": f"evolve-{eid}-base-holdout", "hold_cand": f"evolve-{eid}-cand-holdout"}}
    save_state(root, st)
    return run_round(root, st)


def save_state(root, st):
    (root / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), "utf-8")


def stopped(root, what, summary=None):
    """Quota / login / network stopped the round: keep everything, tell the user how to continue."""
    missing = ", ".join((summary or {}).get("missing", []))
    sys.exit(f"⏸ evolve paused at {what}" + (f" (not scored yet: {missing})" if missing else "") +
             f" — the reels made so far are kept.\n  When the quota resets / login works: reels evolve --resume {root.name}")


def ensure_run(root, st, key, split, skill):
    """The bench run for one stage: load it if complete, continue it if not, else start it."""
    rid = st["runs"][key]
    common = dict(harness=st["harness"], model=st["model"], judge=st["judge"])
    if (bench.runs_root() / rid / "summary.json").exists():
        summary = bench.load(rid)
        if not summary.get("complete", True):
            summary = bench.run(resume=rid)
    else:
        summary = bench.run(split, skill_dir=skill, rid=rid, **common)
    if not summary.get("complete", True):
        stopped(root, f"{key} ({rid})", summary)
    return summary


def pair_table(title, base, cand, pairs):
    b = {r["topic"]: r for r in base["rows"]}
    out = [f"### {title}\n", "| topic | composite base → cand | votes base : cand |", "|---|---|---|"]
    for r in cand["rows"]:
        p = pairs.get(r["topic"], {})
        out.append(f"| {r['topic']} | {b.get(r['topic'], {}).get('composite', '-')} → {r['composite']} | "
                   f"{p.get('base', '-')} : {p.get('cand', '-')} |")
    for t, p in pairs.items():
        out.append(f"\n**{t}** — " + " · ".join(p.get("why", [])))
        if p.get("image"):
            out.append(f"\n![{t}: baseline left, candidate right]({p['image']})")
    return "\n".join(out) + "\n\n"


def run_round(root, st):
    current = Path(st["current"])
    cand = root / "skill"
    base = ensure_run(root, st, "base", "train", current)

    if not (root / "skill.patch").exists() or not (root / "skill.patch").read_text("utf-8").strip():
        shutil.rmtree(cand, ignore_errors=True)
        shutil.copytree(current, cand, ignore=shutil.ignore_patterns("__pycache__"))
        inbox = "\n".join(f"- [{m.get('kind')}/{m.get('scope')}] {b}" for _, _, m, b in lessons.all_lessons("inbox")) or "(empty)"
        prompt = agents.render_prompt("propose", candidate=cand, baseline=baseline_digest(base), inbox=inbox,
                                      max_edits=st["max_edits"])
        print("▶ proposing skill edits …", flush=True)
        res = agents.run(st["harness"], st["model"], prompt, cwd=root, log_path=root / "propose.log")
        if not res["ok"] and bench.infra_error(res["tail"]):
            shutil.rmtree(cand, ignore_errors=True)
            stopped(root, "propose")
        diff = patch(current, cand)
        (root / "skill.patch").write_text(diff, "utf-8")
        if not diff.strip():
            sys.exit(f"✗ the proposer changed nothing ({res['tail'][-300:]})")
    diff = (root / "skill.patch").read_text("utf-8")

    cs = ensure_run(root, st, "cand", "train", cand)
    pairs = pairwise(root, st, "train", base, cs)
    ok, checks, worst = verdict(base, cs, pairs)
    hold, hold_pairs = None, {}
    if ok and not st["skip_holdout"]:
        hb = ensure_run(root, st, "hold_base", "holdout", current)
        hc = ensure_run(root, st, "hold_cand", "holdout", cand)
        hold_pairs = pairwise(root, st, "holdout", hb, hc)
        hold = (hb["mean"], hc["mean"])
        hv = votes(hold_pairs)
        checks[f"holdout: candidate wins ≥ half the votes ({hv[0]}–{hv[1]})"] = hv[0] >= hv[1]
        ok = ok and hv[0] >= hv[1]
    eid = st["id"]
    changes = (cand / "CHANGES.md").read_text("utf-8") if (cand / "CHANGES.md").exists() else "(no CHANGES.md)"
    bugs = (cand / "TOOL-BUGS.md").read_text("utf-8").strip() if (cand / "TOOL-BUGS.md").exists() else ""
    report = (f"# Evolve {eid} — {'ACCEPTED' if ok else 'REJECTED'}\n\n"
              f"harness {st['harness']}/{st['model']} · judge {st['judge']}\n\n| | baseline | candidate |\n|---|---|---|\n"
              f"| train mean | {base['mean']} | {cs['mean']} |\n"
              + (f"| holdout mean | {hold[0]} | {hold[1]} |\n" if hold else "")
              + f"\nworst topic delta: {worst:+.1f}\n\nchecks: " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items())
              + "\n\n" + pair_table("Train", base, cs, pairs)
              + (pair_table("Holdout", hb, hc, hold_pairs) if hold_pairs else "")
              + f"\n## Proposed changes\n\n{changes}\n\n"
              + (f"## Tool bugs found (for a developer — not applied by `evolve apply`)\n\n{bugs}\n\n" if bugs else "")
              + "## Patch\n\n```diff\n{diff}\n```\n")
    (root / "report.md").write_text(report, "utf-8")
    (root / "result.json").write_text(json.dumps({"id": eid, "accepted": ok, "checks": checks, "base": base["id"],
                                                  "cand": cs["id"], "holdout": hold, "votes": votes(pairs),
                                                  "holdout_votes": votes(hold_pairs) if hold_pairs else None},
                                                 ensure_ascii=False, indent=2), "utf-8")
    st["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_state(root, st)
    print(f"{'✓ ACCEPTED' if ok else '✗ rejected'}: train {base['mean']} → {cs['mean']}" + (f" · holdout {hold[0]} → {hold[1]}" if hold else ""))
    print(f"  report: {root / 'report.md'}" + (f"\n  apply:  reels evolve apply {eid}" if ok else ""))


def apply(argv):
    ap = argparse.ArgumentParser(prog="reels evolve apply")
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
        if f.name in ("CHANGES.md", "TOOL-BUGS.md"):
            continue
        dst = target / f.relative_to(root / "skill")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dst)
    print(f"✓ applied evolve {a.id} to {target} (backup: {backup})")
