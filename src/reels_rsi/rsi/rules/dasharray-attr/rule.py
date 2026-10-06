"""A stroke-dasharray attribute on a path that is later drawn on makes it appear fully drawn."""
import re

RULE = {
    "id": "dasharray-attr",
    "severity": "error",
    "kinds": ["frame", "overlay"],
    "lesson": "A stroke-dasharray attribute in the markup of a path that a tween draws on makes the path appear fully drawn from t=0.",
    "fix": "Delete the stroke-dasharray attribute; set strokeDasharray only in the tween's from-vars.",
}


def check(doc):
    t, out = doc.text, []
    if "strokeDashoffset" not in t:
        return out
    for m in re.finditer(r"<(?:path|line|polyline|polygon|circle|rect|ellipse)\b[^>]*\bstroke-dasharray\s*=", t):
        end = t.find(">", m.start())
        idm = re.search(r'\bid="([^"]+)"', t[m.start():end])
        if not idm:
            continue
        for ref in re.finditer(r"[#\"']" + re.escape(idm.group(1)) + r"[\"']", t[end:]):
            window = t[end + ref.start(): end + ref.start() + 300]
            if "strokeDashoffset" in window:
                out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, m.start()),
                                     f"#{idm.group(1)} has a stroke-dasharray attribute but is drawn on by a tween"))
                break
    return out
