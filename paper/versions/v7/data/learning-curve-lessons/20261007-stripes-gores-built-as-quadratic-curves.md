---
id: 20261007-stripes-gores-built-as-quadratic-curves
kind: doc
scope: frame
source: 
evidence: 
created: 2026-10-07T04:00:02
accepted: 2026-10-07T04:00:07
---
Stripes/gores built as quadratic curves whose control point equals the outline's max width fall short of it (a Q curve only reaches ~half its control offset), leaving a visible gap ring between the fill and the outline stroke. Overshoot the control point (~2x) and clip the pieces to the outline path; lint and check pass, only the first contact sheet shows the ring.
