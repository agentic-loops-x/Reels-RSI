---
id: 20261007-map-frames-draw-into-an-svg
kind: doc
scope: history
source: 
evidence: 
created: 2026-10-07T00:30:30
accepted: 2026-10-07T00:30:35
---
Map frames draw into an svg with a 1920x1080 viewBox: when the camera zooms out below 1.0 or the focus point is shifted off-centre, the unpainted edge of the map shows as a hard-edged parchment rectangle. Set svg{overflow:visible} on map svgs (or keep scale >= 1) — lint and check pass, only the contact sheet shows it.
