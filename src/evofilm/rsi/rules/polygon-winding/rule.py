"""Counter-clockwise lon/lat rings make d3-geo treat the polygon as the whole globe minus the shape."""
import re

RULE = {
    "id": "polygon-winding",
    "severity": "warning",
    "kinds": ["frame", "overlay", "kit"],
    "lesson": "d3-geo wants polygon rings clockwise on the map; a counter-clockwise ring means 'the globe minus this shape' — fitExtent shrinks the map to a speck and pins collapse with it.",
    "fix": "Reverse the ring (north edge eastward, then down the east side, then back west along the south) — or drop the .reverse().",
}
NUM = r"-?\d+(?:\.\d+)?"
PAIR = r"\[\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\]"
RING = re.compile(r"\[\s*" + PAIR + r"(?:\s*,\s*" + PAIR + r"){3,}\s*,?\s*\]")
NAMEY = re.compile(r"(poly|territor|border|region|empire|realm|zone|area|疆|域)", re.I)


GEO = re.compile(r"d3\.geo|geoPath|geo[A-Z]\w+\(|[\"']Polygon[\"']|EF_GEO|projection")


def check(doc):
    out, t = [], doc.text
    if not GEO.search(t):
        return out  # no map code in this file — small closed shapes are screen coordinates
    for m in RING.finditer(t):
        pts = [tuple(map(float, p)) for p in re.findall(r"\[\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\]", m.group(0))]
        if not all(-180 <= x <= 180 and -90 <= y <= 90 for x, y in pts):
            continue  # screen coordinates, not lon/lat
        before = t[max(0, m.start() - 300):m.start()]
        closed = pts[0] == pts[-1]
        if not (closed or "Polygon" in before or NAMEY.search(before[-80:])):
            continue
        area = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))
        if re.match(r"\s*\.\s*reverse\s*\(", t[m.end():m.end() + 30]):
            area = -area
        if area > 0:
            out.append(H.Finding(RULE["id"], RULE["severity"], doc.rel, H.line_of(t, m.start()),
                                 f"lon/lat ring of {len(pts)} points is counter-clockwise"))
    return out
