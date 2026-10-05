"""Lessons: what one film teaches the next.

    ~/.evofilm/lessons/inbox/<id>.md      proposed (by `evofilm retro`, an agent, or you)
    ~/.evofilm/lessons/accepted/<id>.md   injected into every future film (`lessons digest`)
    ~/.evofilm/lessons/rejected/<id>.md   kept so the same idea is not proposed again

kinds:  doc   a sentence the director / frame workers must read      → digest
        rule  a mistake a static check can catch                     → ~/.evofilm/rules/<id>/ (must pass its examples)
        taste a preference of yours ("字幕再大一点", "少用霓虹色")    → digest, "Your taste" section
        kit   a reusable component worth extracting                   → digest (as a pointer)
scopes: director · frame · history · solve · script · style · all

Nothing is accepted silently: `lessons accept` is the human gate (or `evolve`, which only
accepts what wins on the benchmark).
"""

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

from evofilm import paths

KINDS = ("doc", "rule", "taste", "kit")
SCOPES = ("director", "frame", "history", "solve", "script", "style", "all")


def parse(path):
    text = Path(path).read_text("utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        body = m.group(2).strip()
    else:
        body = text.strip()
    meta.setdefault("id", Path(path).stem)
    return meta, body


def write(path, meta, body):
    head = "\n".join(f"{k}: {v}" for k, v in meta.items())
    Path(path).write_text(f"---\n{head}\n---\n{body.strip()}\n", "utf-8")


def all_lessons(state="accepted"):
    states = ("inbox", "accepted", "rejected") if state == "all" else (state,)
    out = []
    for st in states:
        for p in sorted(paths.lessons(st).glob("*.md")):
            meta, body = parse(p)
            out.append((st, p, meta, body))
    return out


def find(lid):
    for st, p, meta, body in all_lessons("all"):
        if meta["id"] == lid or p.stem == lid:
            return st, p, meta, body
    sys.exit(f"✗ no lesson {lid}")


def tokens(s):
    return set(re.findall(r"[a-z0-9]+|[一-鿿]", s.lower()))


def similar(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / max(1, len(ta | tb))


def slug(text):
    words = re.findall(r"[a-z0-9]+", text.lower())[:6]
    return "-".join(words) or "lesson"


def add(text, kind="doc", scope="all", source="", evidence="", force=False):
    if kind not in KINDS or scope not in SCOPES:
        raise SystemExit(f"✗ kind ∈ {KINDS}, scope ∈ {SCOPES}")
    for st, p, meta, body in all_lessons("all"):
        if similar(text, body) > 0.6 and not force:
            print(f"  ↺ similar to {st}/{meta['id']} — skipped (use --force to add anyway)")
            return None
    lid = f"{time.strftime('%Y%m%d')}-{slug(text)}"
    path = paths.lessons("inbox") / f"{lid}.md"
    i = 2
    while path.exists():
        path = paths.lessons("inbox") / f"{lid}-{i}.md"
        i += 1
    write(path, {"id": path.stem, "kind": kind, "scope": scope, "source": source, "evidence": evidence.replace("\n", " ")[:300],
                 "created": time.strftime("%Y-%m-%dT%H:%M:%S")}, text)
    print(f"  + inbox/{path.stem} [{kind}/{scope}]")
    return path


def digest(scope="director"):
    """The accepted lessons a role must read — compact markdown, empty string if none."""
    items = [(m, b) for st, p, m, b in all_lessons("accepted") if m.get("scope") in (scope, "all") or scope == "all"
             or (scope == "director" and m.get("scope") in ("script", "style", "history", "solve"))]
    taste = [b for m, b in items if m.get("kind") == "taste"]
    docs = [(m, b) for m, b in items if m.get("kind") in ("doc", "kit")]
    if not taste and not docs:
        return ""
    out = ["\n## Learned from past films (EvoFilm lessons — follow them)\n"]
    out += [f"- [{m.get('scope')}] {b}" for m, b in docs]
    if taste:
        out += ["\n## Your viewer's taste\n"] + [f"- {b}" for b in taste]
    return "\n".join(out) + "\n"


def accept(lid, rule_dir=None):
    st, p, meta, body = find(lid)
    if meta.get("kind") == "rule":
        if not rule_dir:
            sys.exit("✗ a rule lesson is accepted with its rule: `evofilm lessons accept <id> --rule-dir <dir>` "
                     "(scaffold one with `evofilm rules new <rule-id>`)")
        from evofilm.rsi import lint
        src = Path(rule_dir).resolve()
        builtin = src.parent == lint.BUILTIN
        dst = src if builtin else paths.user_rules() / src.name   # a lesson that already became a built-in rule
        if src != dst:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        results = lint.test_rule(lint.load_rule(dst))
        bad = [r for r in results if not r[1]]
        if bad:
            shutil.rmtree(dst) if src != dst else None
            sys.exit("✗ rule fails its own examples: " + "; ".join(f"{n}: {d}" for n, _, d in bad))
        meta["rule"] = f"builtin:{dst.name}" if builtin else str(dst)
    meta["accepted"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    target = paths.lessons("accepted") / p.name
    write(target, meta, body)
    if p != target:
        p.unlink()
    print(f"✓ accepted {meta['id']} [{meta.get('kind')}/{meta.get('scope')}]")


def reject(lid, reason=""):
    st, p, meta, body = find(lid)
    meta["rejected"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if reason:
        meta["reason"] = reason
    target = paths.lessons("rejected") / p.name
    write(target, meta, body)
    if p != target:
        p.unlink()
    print(f"✓ rejected {meta['id']}")


def export(out):
    """Bundle accepted lessons + user rules for an upstream pull request (community self-improvement)."""
    out = Path(out)
    (out / "lessons").mkdir(parents=True, exist_ok=True)
    n = 0
    for st, p, meta, body in all_lessons("accepted"):
        if meta.get("kind") == "taste":
            continue  # personal — never exported
        meta = {k: v for k, v in meta.items() if k != "source"}  # local paths stay local
        write(out / "lessons" / p.name, meta, body)
        n += 1
    rules = [d for d in paths.user_rules().iterdir() if (d / "rule.py").exists()] if paths.user_rules().exists() else []
    for d in rules:
        shutil.copytree(d, out / "rules" / d.name, dirs_exist_ok=True)
    (out / "README.md").write_text(
        f"# EvoFilm lessons export\n\n{n} lessons · {len(rules)} rules. Taste lessons and local paths are excluded.\n"
        "To contribute: copy `rules/<id>/` into `src/evofilm/rsi/rules/` and merge doc lessons into the skill "
        "references they belong to, then run `evofilm rules test` and open a pull request.\n", "utf-8")
    print(f"✓ exported {n} lessons + {len(rules)} rules → {out}")


def feedback(project, text, approve=False, frame=None):
    from evofilm.rsi import runlog
    rec = runlog.append(project, {"event": "feedback", "text": text, "approve": approve, "frame": frame})
    with (paths.home() / "feedback.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**rec, "project": str(Path(project).resolve())}, ensure_ascii=False) + "\n")
    print("✓ feedback recorded" + (" (approval)" if approve else ""))


def cmd_lessons(argv):
    ap = argparse.ArgumentParser(prog="evofilm lessons", description="Manage what past films taught EvoFilm.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list"); ls.add_argument("--state", default="all", choices=["inbox", "accepted", "rejected", "all"])
    sh = sub.add_parser("show"); sh.add_argument("id")
    ad = sub.add_parser("add"); ad.add_argument("text"); ad.add_argument("--kind", default="doc", choices=KINDS)
    ad.add_argument("--scope", default="all", choices=SCOPES); ad.add_argument("--source", default="")
    ad.add_argument("--evidence", default=""); ad.add_argument("--force", action="store_true")
    ac = sub.add_parser("accept"); ac.add_argument("ids", nargs="+"); ac.add_argument("--rule-dir", default=None)
    rj = sub.add_parser("reject"); rj.add_argument("ids", nargs="+"); rj.add_argument("--reason", default="")
    dg = sub.add_parser("digest"); dg.add_argument("--scope", default="director", choices=SCOPES)
    ex = sub.add_parser("export"); ex.add_argument("out")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        rows = all_lessons(a.state)
        for st, p, m, b in rows:
            print(f"{st:9} {m['id']:48} {m.get('kind', ''):5} {m.get('scope', ''):8} {b.splitlines()[0][:70] if b else ''}")
        if not rows:
            print("(no lessons yet — they appear after `evofilm retro <project>`)")
    elif a.cmd == "show":
        st, p, m, b = find(a.id)
        print(f"[{st}] {p}\n" + "\n".join(f"{k}: {v}" for k, v in m.items()) + f"\n\n{b}")
    elif a.cmd == "add":
        add(a.text, a.kind, a.scope, a.source, a.evidence, a.force)
    elif a.cmd == "accept":
        for i in a.ids:
            accept(i, a.rule_dir)
    elif a.cmd == "reject":
        for i in a.ids:
            reject(i, a.reason)
    elif a.cmd == "digest":
        print(digest(a.scope) or "(no accepted lessons for this scope)")
    elif a.cmd == "export":
        export(a.out)


def cmd_feedback(argv):
    ap = argparse.ArgumentParser(prog="evofilm feedback",
                                 description="Record what the viewer said about a film (fuel for retro and taste).")
    ap.add_argument("text")
    ap.add_argument("--project", default=".")
    ap.add_argument("--approve", action="store_true", help="the viewer approved (plan / look-dev / final)")
    ap.add_argument("--frame", default=None)
    a = ap.parse_args(argv)
    feedback(a.project, a.text, a.approve, a.frame)
