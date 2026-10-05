"""Unpinned CDN scripts make renders irreproducible."""
import re

RULE = {
    "id": "unpinned-cdn",
    "severity": "warning",
    "kinds": ["frame", "overlay", "composition"],
    "lesson": "A CDN script without a version (gsap/dist/… instead of gsap@3.14.2/dist/…) can change under you, so a re-render months later looks different or breaks.",
    "fix": "Pin the version in the URL, e.g. https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js",
}


def check(doc):
    out = []
    for m in re.finditer(r"src=\"https://(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/((?:@[\w.-]+/)?[\w.-]+)(@[^/\"]+)?", doc.text):
        if not m.group(2):
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, m.start()),
                                 f"{m.group(1)} loaded without a pinned version"))
    return out
