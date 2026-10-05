"""A composition whose timeline is not registered under its own id renders frozen."""
import re

RULE = {
    "id": "timeline-registration",
    "severity": "error",
    "kinds": ["frame", "overlay"],
    "lesson": "A sub-composition must register its paused timeline at window.__timelines[<its data-composition-id>]; a missing or mismatched id renders the frame frozen at t=0.",
    "fix": "End the script with window.__timelines[\"<composition id>\"] = tl; using the root's exact data-composition-id.",
}


def check(doc):
    m = re.search(r'data-composition-id="([^"]+)"', doc.text)
    if not m:
        return [H.Finding(RULE["id"], RULE["severity"], doc.rel, 1, "no data-composition-id on the root")]
    cid = m.group(1)
    if not re.search(r"__timelines\s*\[\s*[\"'`]" + re.escape(cid) + r"[\"'`]\s*\]\s*=", doc.text):
        return [H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, m.start()),
                          f'timeline not registered as window.__timelines["{cid}"]')]
    return []
