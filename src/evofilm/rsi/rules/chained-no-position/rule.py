"""A chained tween without a position lands at the timeline's end, not on its cue."""
import re

RULE = {
    "id": "chained-no-position",
    "severity": "warning",
    "kinds": ["frame", "overlay"],
    "lesson": "A chained .to()/.from() without a position argument is appended at the end of the timeline, so the reveal drifts away from the spoken word it was cued to.",
    "fix": "Give every chained tween an explicit absolute position in seconds (the word time) or a label.",
}
NEED = {"to": 3, "from": 3, "set": 3, "fromTo": 4}


def check(doc):
    out, t = [], doc.text
    for m in re.finditer(r"\)\s*\.(to|from|fromTo|set)\s*\(", t):
        if "timeline(" in t[max(0, m.start() - 60):m.start() + 1]:
            continue
        body = H.balanced(t, m.end() - 1)
        if len(H.split_args(body[1:-1])) < NEED[m.group(1)]:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, m.start()),
                                 f"chained .{m.group(1)}() has no position argument"))
    return out
