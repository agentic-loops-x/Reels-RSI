---
id: 20261007-put-camera-scale-and-rotation-for
kind: doc
scope: frame
source: 
evidence: 
created: 2026-10-07T01:36:00
accepted: 2026-10-07T01:36:05
---
Put camera scale and rotation for a frame's world wrapper in ONE fromTo (one transformOrigin); two tweens on the same element trip overlapping_gsap_tweens, and a CSS transform (e.g. scaleX(0) in a style) on an element GSAP also animates trips gsap_css_transform_conflict — start such elements with fromTo, not inline CSS transforms.
