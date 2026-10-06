---
version: 1
name: Reels-RSI Ink — Frame (video / frame layer)
description: >
  A Chinese ink-wash (水墨) system for Chinese history, poetry, philosophy and culture. Warm xuan
  paper with fibre grain, ink that bleeds and spreads (wet-edge strokes, diluted washes, dry-brush
  texture), one vermilion seal-red accent, distant mountains in layered grey washes. Noto Serif SC
  for display (set vertically when it suits), Noto Sans SC for small labels, JetBrains Mono only for
  dates and numbers. Calm, spacious, literary — negative space is part of the composition (留白).
unit: the frame — 1920×1080 primary; 9:16 and 1:1 supported
principle: 留白 is composition · ink is drawn, never pasted · dates come from the script

colors:
  paper: "#F2EBDD"
  paper-deep: "#E3D8C3"
  ink: "#1E1D1B"
  ink-wash: "#5E5B55"
  ink-mist: "#A9A397"
  seal: "#B23A2A"
  ochre: "#B8894A"
  celadon: "#7E9A8A"

typography:
  body:       { fontFamily: "Noto Sans SC", px: 28, weight: 400, lineHeight: 1.6, color: "ink" }
  micro-label:{ fontFamily: "Noto Sans SC", px: 16, weight: 500, tracking: "0.3em", color: "ink-wash" }
  mono-data:  { fontFamily: "JetBrains Mono", px: 26, weight: 400, tracking: "0.04em" }
  headline-sm:{ fontFamily: "Noto Serif SC", px: 64, weight: 600, lineHeight: 1.2 }
  headline:   { fontFamily: "Noto Serif SC", px: 110, weight: 700, lineHeight: 1.1 }
  display:    { fontFamily: "Noto Serif SC", px: 190, weight: 900, lineHeight: 1.0 }

spacing:
  pad-edge: "88px"
  gap-region: "56px"

components:
  xuan-paper:
    background: "{colors.paper} with a seeded fibre/grain texture (canvas noise at 4–7%) and a faint warm vignette"
    description: "The ground on every frame."
  ink-stroke:
    stroke: "{colors.ink}, variable width (taper in/out), wet edge = an SVG feTurbulence+feDisplacementMap filter or layered translucent strokes"
    description: "All drawing. Brush strokes draw on along their path; washes bloom outward (radius + opacity), never pop."
  mountain-wash:
    background: "3–5 layered ridge silhouettes in {colors.ink-mist}→{colors.ink-wash}, blurred more with distance"
    description: "Depth layers; drift at different parallax rates."
  seal-stamp:
    background: "{colors.seal} square/round seal with paper-white carved characters, slightly rough edge"
    description: "The one accent: a dynasty name, a key year, the film's mark. Stamps in with a small press (scale 1.08→1)."
  vertical-title:
    typography: "{typography.headline} with writing-mode: vertical-rl"
    description: "Classical vertical title column; strokes or characters reveal top to bottom."
---

# Reels-RSI Ink — Frame

## Overview

A scroll unrolling: xuan paper, ink washes, mountains in mist, a red seal. Figures and buildings are
ink silhouettes and brush outlines, never vector clip-art. Motion is slow and liquid — ink spreads,
mist drifts, the camera glides along the scroll (a horizontal pan is the signature move).

## The Frame

- **留白** — 40–55% of the frame is paper; the hero (a ridge, a city wall, a horse, a character)
  sits off-centre with a vertical title column balancing it.
- **Depth** — far washes (mist) · mid ridges · near ink detail; parallax on a slow pan.
- **Safe area** — nothing important below y = 900 (caption band).

## Do

- Draw with tapered brush strokes and washes that bloom; add dry-brush texture with seeded noise.
- Use the seal red exactly once per frame at most.
- Pan along the scroll; let mist drift; reveal vertical text stroke by stroke.

## Don't

- No hard vector outlines of uniform width, no glossy gradients, no drop shadows, no neon.
- No more than one accent color; no Latin display type over Chinese content.
- Never render narration sentences on screen.
