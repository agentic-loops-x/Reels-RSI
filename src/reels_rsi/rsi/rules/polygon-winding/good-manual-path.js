// A hand-projected region: each lon/lat point goes through proj() and the result is a plain SVG path.
// Ring direction is irrelevant to SVG fill, so a counter-clockwise ring here is fine (no GeoJSON involved).
const pathD = (pts) => "M" + pts.map((p) => proj(p).map((v) => v.toFixed(1)).join(",")).join("L");
const border = [[124, 34.2], [120.5, 33.4], [118.5, 32.6], [116.5, 31.9], [114.6, 31.6], [113.2, 32.0]];
const wu = border.slice(0, 5).concat([[113.6, 30.0], [113.3, 28.6], [114.2, 27.0], [114.6, 24.0], [124, 24]]);
el("path", { d: pathD(wu) + "Z", fill: "#2E3B55", opacity: 0.38 }, g);
