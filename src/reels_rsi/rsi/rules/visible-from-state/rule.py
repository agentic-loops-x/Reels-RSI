"""A fromTo that starts visible and fades out shows its from-state before its cue."""

RULE = {
    "id": "visible-from-state",
    "severity": "warning",
    "kinds": ["frame", "overlay", "kit"],
    "lesson": "fromTo renders its from-state at build time: a tween that starts visible (opacity > 0) and fades to 0 later in the timeline shows the element before its cue (stray chalk-dust specks in a release-test reel).",
    "fix": "Add immediateRender: false to the to-vars (the element then keeps its markup opacity, e.g. 0, until the tween starts).",
}


def num(vars_text, key):
    import re
    m = re.search(r"\b" + key + r"\s*:\s*(-?\d*\.?\d+)", vars_text)
    return float(m.group(1)) if m else None


def check(doc):
    out = []
    for idx, args in H.calls(doc.text, "fromTo"):
        if len(args) < 4:          # no position → starts at the timeline's current end, usually 0
            continue
        frm, to = args[1], args[2]
        a, b = num(frm, "opacity"), num(to, "opacity")
        if a is not None and a > 0 and b == 0 and "immediateRender" not in to:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, idx),
                                 "fromTo starts visible and fades out — visible before its cue"))
    return out
