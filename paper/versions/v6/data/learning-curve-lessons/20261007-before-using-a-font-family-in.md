---
id: 20261007-before-using-a-font-family-in
kind: doc
scope: director
source: 
evidence: 
created: 2026-10-07T04:30:17
accepted: 2026-10-07T04:30:23
---
Before using a font family in a frame, run ls assets/fonts: a new project's font-faces.css lists Instrument Serif/Archivo/etc., but only the Noto subsets (plus any family the preset actually bundles) exist as files, and a frame that names a missing family falls back silently with no lint warning. Use Noto Serif SC / Noto Sans SC for Latin text too, and add every on-screen label string to STORYBOARD.md before 'reels fonts' so its glyphs are in the subset.
