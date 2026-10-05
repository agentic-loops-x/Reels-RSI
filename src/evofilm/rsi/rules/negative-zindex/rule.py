"""Negative z-index hides a layer behind the composition root."""
import re

RULE = {
    "id": "negative-zindex",
    "severity": "error",
    "kinds": ["frame", "overlay", "composition"],
    "lesson": "A negative z-index puts the layer behind the composition root's background — it vanishes in the render (HyperFrames lint also rejects it).",
    "fix": "Order layers by DOM order (later = on top) or use z-index >= 0.",
}


def check(doc):
    return [H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, m.start()), m.group(0).strip())
            for m in re.finditer(r"z-index\s*:\s*-\d+|zIndex\s*:\s*[\"']?-\d+", doc.text)]
