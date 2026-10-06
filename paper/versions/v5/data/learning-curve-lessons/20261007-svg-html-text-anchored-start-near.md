---
id: 20261007-svg-html-text-anchored-start-near
kind: doc
scope: frame
source: 
evidence: 
created: 2026-10-07T02:05:21
accepted: 2026-10-07T02:05:27
---
SVG/HTML text anchored 'start' near the right half needs its width checked: monospace width ≈ chars × 0.6 × font-size, so a 12-char equation at 76 px is ~550 px wide and clipped off the 1920 canvas when started at x=1230, with lint and check passing. Compute x + width ≤ 1840 before placing, and put equations/answers in a screen-fixed layer, not the camera world.
