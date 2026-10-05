"""Chinese text without a shipped font renders as tofu in the headless render browser."""
import re

RULE = {
    "id": "cjk-font",
    "severity": "error",
    "kinds": ["frame", "overlay", "composition"],
    "lesson": "The render Chrome has no CJK system fonts; Chinese text without an @font-face for a shipped font renders as empty boxes.",
    "fix": "Paste the Noto Serif SC / Noto Sans SC @font-face lines from assets/fonts/font-faces.css into the frame's <style> (takeloop fonts subsets them).",
}


def check(doc):
    t = re.sub(r"<!--.*?-->", "", doc.text, flags=re.S)
    t = re.sub(r"/\*.*?\*/|(?<![:\"'])//[^\n]*", "", t, flags=re.S)
    m = re.search(r"[\u4e00-\u9fff]", t)
    if m and not re.search(r"@font-face[^}]*Noto (?:Sans|Serif) SC", doc.text):
        return [H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(doc.text, doc.text.find(m.group(0))),
                          "Chinese text but no Noto SC @font-face in this composition")]
    return []
