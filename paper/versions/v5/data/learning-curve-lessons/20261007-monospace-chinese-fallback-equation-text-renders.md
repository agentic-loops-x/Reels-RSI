---
id: 20261007-monospace-chinese-fallback-equation-text-renders
kind: doc
scope: solve
source: 
evidence: 
created: 2026-10-07T02:52:13
accepted: 2026-10-07T02:52:18
---
Monospace/Chinese-fallback equation text renders much wider than chars × 0.6 × size (a 10-char row at 96 px was ~700 px): never place the next segment of a split equation by that estimate — put each equation row in one text element, or position follow-on segments from a measured getComputedTextLength()/getBBox() after fonts load; only the contact sheet showed segments colliding.
