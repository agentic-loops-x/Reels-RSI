---
id: 20261007-world-space-map-labels-scale-with
kind: doc
scope: history
source: 
evidence: 
created: 2026-10-07T04:11:15
accepted: 2026-10-07T04:11:20
---
World-space map labels scale with the camera: a 30-38 px label under a 3.4x push renders 100-130 px and lands on the screen-fixed title or a neighbouring label. Size and place each world label from its END scale (screen = focus + scale*(p-focus)) and keep ones that are not the frame's focus away from the other labels' boxes; content_overlap only fires late in the frame.
