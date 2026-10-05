"""Wall-clock time and unseeded randomness break seek-based rendering."""
import re

RULE = {
    "id": "nondeterminism",
    "severity": "error",
    "kinds": ["frame", "overlay", "composition", "kit"],
    "lesson": "Frames are rendered by seeking a paused timeline; Math.random, Date.now, requestAnimationFrame, timers or self-animating libraries (HanziWriter's animator) give different pixels on every render and every seek.",
    "fix": "Use a seeded PRNG (mulberry32) and drive all motion from the paused GSAP timeline (proxy-clock tween + onUpdate for canvas/three.js).",
}
PATTERNS = r"Math\.random\s*\(|Date\.now\s*\(|performance\.now\s*\(|new Date\s*\(\s*\)|requestAnimationFrame\s*\(|setTimeout\s*\(|setInterval\s*\(|HanziWriter\.create\s*\(|\.animateCharacter\s*\("


def blank(m):
    return __import__("re").sub(r"[^\n]", " ", m.group(0))


def check(doc):
    text = re.sub(r"/\*.*?\*/", blank, doc.text, flags=re.S)
    text = re.sub(r"(?<![:\"'\\])//[^\n]*", blank, text)
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return [H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(text, m.start()), f"{m.group(0).rstrip('( ')} in a seek-rendered composition")
            for m in re.finditer(PATTERNS, text)]
