---
id: 20261007-a-gsap-x-y-rotation-tween
kind: doc
scope: frame
source: 
evidence: 
created: 2026-10-07T01:43:38
accepted: 2026-10-07T01:43:43
---
A GSAP x/y/rotation tween on an SVG <g> that also carries a transform="translate() scale()" attribute replaces that attribute: the flip/offset is lost and the subject lands off-canvas, with lint and check passing. Put the static transform on an inner <g> and tween only the outer wrapper.
