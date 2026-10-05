"""svgOrigin set only in a fromTo's to-vars makes the element jump on the first frame."""

RULE = {
    "id": "svgorigin-one-sided",
    "severity": "error",
    "kinds": ["frame", "overlay"],
    "lesson": "svgOrigin given only in a fromTo's to-vars: the from-state rotates/scales around the old origin, so the element jumps when the tween starts.",
    "fix": "Put the same svgOrigin in both the from-vars and the to-vars.",
}


def check(doc):
    out = []
    for idx, args in H.calls(doc.text, "fromTo"):
        if len(args) >= 3 and "svgOrigin" in args[2] and "svgOrigin" not in args[1]:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, idx),
                                 "svgOrigin only in the to-vars of a fromTo"))
    return out
