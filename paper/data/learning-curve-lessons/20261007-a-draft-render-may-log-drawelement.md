---
id: 20261007-a-draft-render-may-log-drawelement
kind: doc
scope: director
source: 
evidence: 
created: 2026-10-07T03:26:49
accepted: 2026-10-07T03:26:54
---
A draft render may log 'drawElement self-verify failed ... re-rendering via screenshot' at ERROR trace level; it is an automatic fallback, not a failure. Judge the render only by the final 'N MB · Ns video' line and an ffprobe duration, and do not re-run it.
