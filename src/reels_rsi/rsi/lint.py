"""Reels-RSI rules: lessons compiled into static checks.

A lesson written in a doc can be forgotten by the next model; a rule cannot. Every rule is a
folder — `rule.py` + a failing example (`bad.*`) + a passing example (`good.*`) — so a rule is
code plus the evidence that it catches the mistake and nothing else:

    rules/<id>/rule.py     RULE = {...}; def check(doc) -> list[Finding]
    rules/<id>/bad.html    must produce ≥ 1 finding of <id>
    rules/<id>/good.html   must produce none

Built-in rules ship in the package; rules you (or `reels retro` → `lessons accept`) add live in
~/.reels/rules/<id>/ and load the same way. `reels rules test` proves every rule on its examples.
"""

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from reels_rsi import paths

BUILTIN = Path(__file__).resolve().parent / "rules"
GENERATED = {"captions.html"}


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    fix: str = ""


# ── helpers rules use ────────────────────────────────────────────────────────
def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def balanced(text, start, open_ch="(", close_ch=")"):
    """Return the substring from text[start] (an open_ch) to its matching close_ch, skipping strings."""
    depth, i, quote = 0, start, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


def split_args(inner):
    """Split a call's argument text at top-level commas."""
    out, depth, cur, quote, i = [], 0, "", None, 0
    while i < len(inner):
        c = inner[i]
        if quote:
            cur += c
            if c == "\\" and i + 1 < len(inner):
                cur += inner[i + 1]
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
            cur += c
        elif c in "([{":
            depth += 1
            cur += c
        elif c in ")]}":
            depth -= 1
            cur += c
        elif c == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    if cur.strip():
        out.append(cur.strip())
    return out


def calls(text, name):
    """Yield (index, [args]) for every `.name(` / `name(` call."""
    for m in re.finditer(r"(?<![\w$])" + re.escape(name) + r"\s*\(", text):
        body = balanced(text, m.end() - 1)
        yield m.start(), split_args(body[1:-1])


HELPERS = SimpleNamespace(Finding=Finding, line_of=line_of, balanced=balanced, split_args=split_args, calls=calls)


# ── loading ──────────────────────────────────────────────────────────────────
def rule_dirs():
    """Built-in rules, then the user's. A user rule with a built-in's name replaces it (a refined rule)."""
    found = {d.name: d for d in sorted(BUILTIN.iterdir()) if (d / "rule.py").exists()}
    user = paths.user_rules()
    if user.exists():
        found.update({d.name: d for d in sorted(user.iterdir()) if (d / "rule.py").exists()})
    return [found[k] for k in sorted(found)]


def load_rule(d):
    spec = importlib.util.spec_from_file_location(f"reels_rule_{d.name.replace('-', '_')}", d / "rule.py")
    mod = importlib.util.module_from_spec(spec)
    mod.H = HELPERS
    spec.loader.exec_module(mod)
    mod.RULE.setdefault("id", d.name)
    mod.DIR = d
    return mod


def load_rules():
    """Every rule that loads. A broken rule (e.g. a user rule with a syntax error) is reported and
    skipped — one bad rule must never take the whole check down."""
    out = []
    for d in rule_dirs():
        try:
            out.append(load_rule(d))
        except Exception as e:  # noqa: BLE001 — any error in third-party rule code
            print(f"  ⚠ rule {d.name} failed to load and was skipped: {type(e).__name__}: {e}", file=sys.stderr)
    return out


def code_view(html):
    """The frame as code: <script>, <style>, tags and attributes kept; text shown on screen blanked
    (newlines kept, so line numbers stay true). A reel that shows code — `tl.fromTo(c, {opacity: 0.9} …)`
    as an example on screen — must not trip the rules meant for its own animation code."""
    out, pos = [], 0
    for m in re.finditer(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]*>", html, re.S | re.I):
        out.append(re.sub(r"[^\n]", " ", html[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(re.sub(r"[^\n]", " ", html[pos:]))
    return "".join(out)


def doc_for(path, root=None):
    path = Path(path)
    rel = str(path.relative_to(root)) if root else path.name
    kind = ("overlay" if "/overlays/" in f"/{rel}" else "frame" if "/frames/" in f"/{rel}" else
            "kit" if path.suffix == ".js" else "composition")
    raw = path.read_text("utf-8", errors="replace")
    text = code_view(raw) if path.suffix in (".html", ".htm") else raw
    return SimpleNamespace(path=path, rel=rel, kind=kind, text=text, raw=raw)


def project_files(project, frame=None):
    project = Path(project)
    from reels_rsi.project import is_placeholder
    files = [p for p in project.glob("compositions/**/*.html") if p.name not in GENERATED and not is_placeholder(p)]
    files += [p for p in project.glob("assets/*.js")]
    if frame:
        files = [p for p in files if p.stem.startswith(frame)]
    return sorted(files)


def lint_docs(docs, rules=None):
    rules = rules if rules is not None else load_rules()
    out = []
    for doc in docs:
        for r in rules:
            kinds = r.RULE.get("kinds")
            if kinds and doc.kind not in kinds:
                continue
            try:
                found = r.check(doc) or []
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠ rule {r.RULE['id']} crashed on {doc.rel}: {type(e).__name__}: {e}", file=sys.stderr)
                continue
            for f in found:
                f.rule, f.severity = r.RULE["id"], f.severity or r.RULE.get("severity", "warning")
                f.fix = f.fix or r.RULE.get("fix", "")
                out.append(f)
    return out


def lint_project(project, frame=None, rules=None):
    project = Path(project).resolve()
    return lint_docs([doc_for(p, project) for p in project_files(project, frame)], rules)


def print_findings(findings):
    if not findings:
        print("  ✓ no rule findings")
    for f in findings:
        mark = "✗" if f.severity == "error" else "⚠"
        print(f"  {mark} {f.rule} {f.file}:{f.line} — {f.message}" + (f"\n      fix: {f.fix}" if f.fix else ""))


# ── commands ─────────────────────────────────────────────────────────────────
def cmd_lint(argv):
    ap = argparse.ArgumentParser(prog="reels lint", description="Run Reels-RSI rules on a project (or files).")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--project", default=".")
    ap.add_argument("--frame", default=None, help="only files whose name starts with this (e.g. 04)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.files:
        findings = lint_docs([doc_for(p) for p in a.files])
    else:
        findings = lint_project(a.project, a.frame)
    if a.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print_findings(findings)
    sys.exit(1 if any(f.severity == "error" for f in findings) else 0)


def test_rule(mod):
    """[(example, ok, detail)] — bad examples must fire this rule, good ones must not."""
    results = []
    examples = sorted(p for p in mod.DIR.iterdir() if p.stem.startswith(("bad", "good")) and p.suffix in (".html", ".js"))
    if not any(p.stem.startswith("bad") for p in examples) or not any(p.stem.startswith("good") for p in examples):
        return [(mod.DIR.name, False, "needs at least one bad.* and one good.* example")]
    for ex in examples:
        doc = doc_for(ex)
        doc.kind = mod.RULE.get("kinds", [doc.kind])[0] if mod.RULE.get("kinds") else doc.kind
        hits = [f for f in lint_docs([doc], [mod])]
        want = ex.stem.startswith("bad")
        results.append((ex.name, bool(hits) == want, f"{len(hits)} finding(s)"))
    return results


TEMPLATE = '''"""{lesson}"""

RULE = {{
    "id": "{id}",
    "severity": "warning",          # error | warning
    "kinds": ["frame", "overlay"],  # frame | overlay | composition | kit
    "lesson": "{lesson}",
    "fix": "TODO: one line telling the author what to do instead",
}}


def check(doc):
    out = []
    # doc.raw = the whole file · doc.text = its code view (HTML text shown on screen blanked — use it for
    # rules about the animation code) · doc.rel, doc.kind · helpers: H.calls(text, "fromTo"), H.balanced,
    # H.split_args, H.line_of
    for m in __import__("re").finditer(r"TODO-pattern", doc.raw):
        out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.raw, m.start()), "TODO message"))
    return out
'''


def cmd_rules(argv):
    ap = argparse.ArgumentParser(prog="reels rules", description="List, test or scaffold Reels-RSI rules.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    t = sub.add_parser("test")
    t.add_argument("ids", nargs="*")
    n = sub.add_parser("new", help="scaffold ~/.reels/rules/<id>/ (rule.py + bad.html + good.html)")
    n.add_argument("id")
    n.add_argument("--lesson", default="TODO: the mistake this rule prevents and why it matters")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for r in load_rules():
            origin = "user" if paths.user_rules() in r.DIR.parents else "builtin"
            print(f"{r.RULE['id']:28} {r.RULE.get('severity', 'warning'):8} {origin:8} {r.RULE.get('lesson', '')[:90]}")
        return
    if a.cmd == "new":
        d = paths.user_rules() / a.id
        if d.exists():
            sys.exit(f"✗ {d} exists")
        d.mkdir(parents=True)
        (d / "rule.py").write_text(TEMPLATE.format(id=a.id, lesson=a.lesson.replace('"', "'")), "utf-8")
        (d / "bad.html").write_text("<!-- minimal frame that MUST trigger the rule -->\n", "utf-8")
        (d / "good.html").write_text("<!-- the corrected version — must NOT trigger the rule -->\n", "utf-8")
        print(f"✓ scaffolded {d} — fill rule.py + examples, then `reels rules test {a.id}`")
        return
    failed = 0
    for r in load_rules():
        if a.ids and r.RULE["id"] not in a.ids:
            continue
        for name, ok, detail in test_rule(r):
            failed += not ok
            print(f"  {'✓' if ok else '✗'} {r.RULE['id']}/{name}: {detail}")
    print("✓ all rules pass their examples" if not failed else f"✗ {failed} example(s) failed")
    sys.exit(1 if failed else 0)
