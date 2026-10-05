"""Text in the caption band collides with the karaoke captions."""
import re

RULE = {
    "id": "caption-band",
    "severity": "warning",
    "kinds": ["frame"],
    "lesson": "Frame text placed in the caption band (below y=900 on 1080p, y=1600 on 1920-tall) collides with the karaoke captions.",
    "fix": "Move the text above the band; purely decorative shapes there are fine.",
}


def check(doc):
    out, t = [], doc.text
    limit = 1600 if 'data-height="1920"' in t else 900
    for m in re.finditer(r"\{([^{}]*)\}|style=\"([^\"]*)\"", t):
        body = m.group(1) or m.group(2) or ""
        top = re.search(r"(?<![-\w])top\s*:\s*(\d+)px", body)
        if top and int(top.group(1)) >= limit and "font-size" in body:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, m.start()),
                                 f"text styled at top: {top.group(1)}px (caption band starts at {limit})"))
    return out
