"""Lessons: what one reel teaches the next.

    ~/.reels/lessons/inbox/<id>.md      proposed (by `reels retro`, an agent, or you)
    ~/.reels/lessons/accepted/<id>.md   injected into every future reel (`lessons digest`)
    ~/.reels/lessons/rejected/<id>.md   kept so the same idea is not proposed again

kinds:  doc   a sentence the director / frame workers must read      → digest
        rule  a mistake a static check can catch                     → ~/.reels/rules/<id>/ (must pass its examples)
        taste a preference of yours ("字幕再大一点", "少用霓虹色")    → digest, "Your taste" section
        kit   a reusable component worth extracting                   → digest (as a pointer)
scopes: director · frame · history · solve · script · style · all
when:   optional conditions, all must hold for the reel: "preset=chalk", "aspect=9:16", "mode=solve",
        comma-separated ("preset=chalk, aspect=9:16"). No `when` = every reel. history/solve scopes
        reach a reel's frame workers only when the reel is in that mode.

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

from reels_rsi import paths

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


WHEN_KEYS = ("preset", "aspect", "mode")


def parse_when(when):
    out = {}
    for part in filter(None, (x.strip() for x in (when or "").split(","))):
        k, _, v = part.partition("=")
        if k.strip() not in WHEN_KEYS or not v.strip():
            raise SystemExit(f"✗ when: use {', '.join(k + '=…' for k in WHEN_KEYS)} (got {part!r})")
        out[k.strip()] = v.strip()
    return out


def applies(meta, reel):
    """Does a lesson apply to this reel? reel = {"preset", "aspect", "mode"} or None (= show everything)."""
    if reel is None:
        return True
    return all(str(reel.get(k, "")) == v for k, v in parse_when(meta.get("when", "")).items())


def add(text, kind="doc", scope="all", source="", evidence="", force=False, when=""):
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
    meta = {"id": path.stem, "kind": kind, "scope": scope}
    if when:
        meta["when"] = ", ".join(f"{k}={v}" for k, v in parse_when(when).items())
    meta.update(source=source, evidence=evidence.replace("\n", " ")[:300], created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    write(path, meta, text)
    print(f"  + inbox/{path.stem} [{kind}/{scope}]" + (f" when {meta['when']}" if when else ""))
    return path


def in_scope(lesson_scope, role, reel):
    if role == "all" or lesson_scope in (role, "all"):
        return True
    mode = (reel or {}).get("mode")
    if lesson_scope in ("history", "solve"):            # mode lessons: the director always (unless the reel says otherwise),
        return reel is None and role == "director" or (reel is not None and lesson_scope == mode)   # workers in that mode
    return role == "director" and lesson_scope in ("script", "style")


def digest(scope="director", reel=None):
    """The accepted lessons a role must read — compact markdown, empty string if none. With `reel`
    ({"preset", "aspect", "mode"}), only the lessons that apply to that reel."""
    items = [(m, b) for st, p, m, b in all_lessons("accepted")
             if in_scope(m.get("scope"), scope, reel) and applies(m, reel)]
    taste = [b for m, b in items if m.get("kind") == "taste"]
    docs = [(m, b) for m, b in items if m.get("kind") in ("doc", "kit")]
    if not taste and not docs:
        return ""
    out = ["\n## Learned from past reels (Reels-RSI lessons — follow them)\n"]
    out += [f"- [{m.get('scope')}] {b}" for m, b in docs]
    if taste:
        out += ["\n## Your viewer's taste\n"] + [f"- {b}" for b in taste]
    return "\n".join(out) + "\n"


def set_when(lid, when):
    st, p, meta, body = find(lid)
    if when:
        meta["when"] = ", ".join(f"{k}={v}" for k, v in parse_when(when).items())
    else:
        meta.pop("when", None)
    write(p, meta, body)
    print(f"✓ {meta['id']}: " + (f"when {meta['when']}" if when else "applies to every reel"))


def accept(lid, rule_dir=None):
    st, p, meta, body = find(lid)
    if meta.get("kind") == "rule":
        if not rule_dir:
            sys.exit("✗ a rule lesson is accepted with its rule: `reels lessons accept <id> --rule-dir <dir>` "
                     "(scaffold one with `reels rules new <rule-id>`)")
        from reels_rsi.rsi import lint
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
        f"# Reels-RSI lessons export\n\n{n} lessons · {len(rules)} rules. Taste lessons and local paths are excluded.\n"
        "To contribute: copy `rules/<id>/` into `src/reels_rsi/rsi/rules/` and merge doc lessons into the skill "
        "references they belong to, then run `reels rules test` and open a pull request.\n", "utf-8")
    print(f"✓ exported {n} lessons + {len(rules)} rules → {out}")


def feedback(project, text, approve=False, frame=None):
    from reels_rsi.rsi import runlog
    rec = runlog.append(project, {"event": "feedback", "text": text, "approve": approve, "frame": frame})
    with (paths.home() / "feedback.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**rec, "project": str(Path(project).resolve())}, ensure_ascii=False) + "\n")
    print("✓ feedback recorded" + (" (approval)" if approve else ""))


def cmd_lessons(argv):
    ap = argparse.ArgumentParser(prog="reels lessons", description="Manage what past reels taught Reels-RSI.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list"); ls.add_argument("--state", default="all", choices=["inbox", "accepted", "rejected", "all"])
    sh = sub.add_parser("show"); sh.add_argument("id")
    ad = sub.add_parser("add"); ad.add_argument("text"); ad.add_argument("--kind", default="doc", choices=KINDS)
    ad.add_argument("--scope", default="all", choices=SCOPES); ad.add_argument("--source", default="")
    ad.add_argument("--evidence", default=""); ad.add_argument("--force", action="store_true")
    ad.add_argument("--when", default="", help='only for some reels: "preset=chalk", "aspect=9:16", "mode=solve"')
    wh = sub.add_parser("when", help="limit a lesson to some reels (empty = every reel)")
    wh.add_argument("id"); wh.add_argument("conditions", nargs="?", default="")
    ac = sub.add_parser("accept"); ac.add_argument("ids", nargs="+"); ac.add_argument("--rule-dir", default=None)
    rj = sub.add_parser("reject"); rj.add_argument("ids", nargs="+"); rj.add_argument("--reason", default="")
    dg = sub.add_parser("digest"); dg.add_argument("--scope", default="director", choices=SCOPES)
    dg.add_argument("--project", default=None, help="only the lessons that apply to this reel (preset, aspect, mode)")
    ex = sub.add_parser("export"); ex.add_argument("out")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        rows = all_lessons(a.state)
        for st, p, m, b in rows:
            when = f" [when {m['when']}]" if m.get("when") else ""
            print(f"{st:9} {m['id']:48} {m.get('kind', ''):5} {m.get('scope', ''):8} {b.splitlines()[0][:70] if b else ''}{when}")
        if not rows:
            print("(no lessons yet — they appear after `reels retro <project>`)")
    elif a.cmd == "show":
        st, p, m, b = find(a.id)
        print(f"[{st}] {p}\n" + "\n".join(f"{k}: {v}" for k, v in m.items()) + f"\n\n{b}")
    elif a.cmd == "add":
        add(a.text, a.kind, a.scope, a.source, a.evidence, a.force, a.when)
    elif a.cmd == "when":
        set_when(a.id, a.conditions)
    elif a.cmd == "accept":
        for i in a.ids:
            accept(i, a.rule_dir)
    elif a.cmd == "reject":
        for i in a.ids:
            reject(i, a.reason)
    elif a.cmd == "digest":
        reel = None
        if a.project:
            from reels_rsi.project import reel_context
            reel = reel_context(a.project)
        print(digest(a.scope, reel) or "(no accepted lessons for this scope)")
    elif a.cmd == "export":
        export(a.out)


def cmd_feedback(argv):
    ap = argparse.ArgumentParser(prog="reels feedback",
                                 description="Record what the viewer said about a reel (fuel for retro and taste).")
    ap.add_argument("text")
    ap.add_argument("--project", default=".")
    ap.add_argument("--approve", action="store_true", help="the viewer approved (plan / look-dev / final)")
    ap.add_argument("--frame", default=None)
    a = ap.parse_args(argv)
    feedback(a.project, a.text, a.approve, a.frame)
