"""A second fromTo on the same target renders its from-state immediately and overwrites the first."""
import re

RULE = {
    "id": "repeat-fromto",
    "severity": "warning",
    "kinds": ["frame", "overlay"],
    "lesson": "Every fromTo renders its from-state at build time; a second fromTo on the same target overwrites the first one's start state, so the element pops or flickers.",
    "fix": "Add immediateRender: false to every fromTo after the first on the same target (or use .to for the later moves).",
}


def stable(target, text):
    """Only targets that name the same element on every call: selector strings and declared consts —
    not loop/callback parameters (forEach(function (c) { tl.fromTo(c, …) }) hits a new element each time)."""
    if target[:1] in "\"'`":
        return True
    if not re.fullmatch(r"[A-Za-z_$][\w$]*", target):
        return False
    t = re.escape(target)
    if re.search(r"function\s*\w*\s*\([^)]*\b" + t + r"\b|\(\s*[^()]*\b" + t + r"\b[^()]*\)\s*=>|\b" + t + r"\s*=>", text):
        return False
    return bool(re.search(r"\b(?:const|let|var)\s+" + t + r"\s*=", text))


def check(doc):
    seen, out = set(), []
    for idx, args in H.calls(doc.text, "fromTo"):
        if len(args) < 3:
            continue
        target = args[0].strip()
        if not stable(target, doc.text):
            continue
        if target in seen and "immediateRender" not in args[2]:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, idx),
                                 f"repeated fromTo on {target[:40]} without immediateRender: false"))
        seen.add(target)
    return out
