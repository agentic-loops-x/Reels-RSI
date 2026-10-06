"""Round-capped mask strokes leak a dot before a brush reveal starts."""
import re

RULE = {
    "id": "round-cap-mask",
    "severity": "warning",
    "kinds": ["frame", "overlay", "kit"],
    "lesson": "A brush stroke revealed through a mask whose stroke has round caps shows a dot at the start point before the reveal begins (the cap extends past dashoffset 0).",
    "fix": "Use stroke-linecap: butt on mask/reveal strokes.",
}


def check(doc):
    out, t = [], doc.text
    for m in re.finditer(r"<mask\b.*?</mask>", t, re.S):
        for c in re.finditer(r"stroke-linecap\s*[=:]\s*[\"']?round", m.group(0)):
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, m.start() + c.start()), "round linecap inside a <mask>"))
    for c in re.finditer(r"[\"']stroke-linecap[\"']\s*,\s*[\"']round[\"']|strokeLinecap\s*[:=]\s*[\"']round", t):
        near = t[max(0, c.start() - 400):c.end() + 400]
        if re.search(r"mask", near, re.I) and not re.search(r"<mask\b", t[max(0, c.start() - 2000):c.start()]):
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, c.start()), "round linecap on a stroke built next to mask code"))
    return out
