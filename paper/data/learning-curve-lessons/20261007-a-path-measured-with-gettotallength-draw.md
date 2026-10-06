---
id: 20261007-a-path-measured-with-gettotallength-draw
kind: doc
scope: frame
source: 
evidence: 
created: 2026-10-07T03:01:59
accepted: 2026-10-07T03:02:06
---
A path measured with getTotalLength() (draw-on, dots travelling along a river/route) must carry its d in the markup: setting d from a JS variable via setAttribute still trips lint svg_measure_before_path_d. Write the static d string in the SVG, and set d from JS only for paths you never measure.
