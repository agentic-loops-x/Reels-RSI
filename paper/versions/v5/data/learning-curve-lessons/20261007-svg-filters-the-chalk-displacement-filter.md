---
id: 20261007-svg-filters-the-chalk-displacement-filter
kind: doc
scope: solve
source: 
evidence: 
created: 2026-10-07T01:25:40
accepted: 2026-10-07T01:25:47
---
SVG filters (the chalk displacement filter from K.defs) are clipped to the element's bounding box: a perfectly horizontal or vertical thick stroke has a zero-extent bbox, so a 22 px bar renders as a hairline while lint/check pass and only the contact sheet shows it. Draw thick bars/segments without filter (or as a filled rect) and keep the filter for thin strokes.
