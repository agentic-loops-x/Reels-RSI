---
version: 1
name: TakeLoop Notebook — Frame (video / frame layer)
description: >
  A hand-drawn science-notebook system for history, geography, biology and everyday science.
  Warm grid paper, wobbly pen line art drawn on stroke by stroke, highlighter-yellow and marker
  red/blue fills, sticky-note labels. Noto Serif SC display, Noto Sans SC labels, JetBrains Mono
  for numbers. Feels like a great teacher sketching while talking — friendly, clear, alive.
unit: the frame — 1920×1080 primary; 9:16 and 1:1 supported
principle: everything is drawn, nothing is pasted · one sketch per frame · numbers come from the script

colors:
  paper: "#F4EFE3"
  paper-deep: "#E8E0CC"
  ink: "#2A2A2E"
  ink-soft: "#6B6A70"
  highlight: "#F7D84A"
  marker-red: "#E2553F"
  marker-blue: "#3F6FD8"
  marker-green: "#4E9A5E"

typography:
  body:       { fontFamily: "Noto Sans SC", px: 30, weight: 400, lineHeight: 1.5, color: "ink" }
  micro-label:{ fontFamily: "Noto Sans SC", px: 16, weight: 600, tracking: "0.24em", upper: true, color: "ink-soft" }
  mono-data:  { fontFamily: "JetBrains Mono", px: 28, weight: 400, tracking: "0.02em" }
  headline-sm:{ fontFamily: "Noto Serif SC", px: 64, weight: 600, lineHeight: 1.15 }
  headline:   { fontFamily: "Noto Serif SC", px: 104, weight: 700, lineHeight: 1.1 }
  display:    { fontFamily: "Noto Serif SC", px: 170, weight: 800, lineHeight: 1.0 }

spacing:
  pad-edge: "76px"
  gap-region: "48px"

components:
  grid-paper:
    background: "{colors.paper} with a 48px grid of 1px {colors.ink} lines at 6% opacity, faint paper grain"
    description: "The ground on every frame."
  pen-line:
    stroke: "{colors.ink} 3–4px, round caps, slightly wobbly paths (seeded jitter of 1–3px), drawn on via stroke-dashoffset"
    description: "All illustration. Draw it as the narration names it — never pop a finished drawing in."
  highlighter:
    background: "{colors.highlight} at 70–85%, slightly skewed rectangle behind a key word"
    description: "The emphasis device. Sweeps in left-to-right."
  marker-fill:
    background: "{colors.marker-red} / {colors.marker-blue} / {colors.marker-green} at 55–80%, hatched or flat, slightly misregistered from the pen line"
    description: "Color for illustrated objects; offset 4–8px from the outline like a hand-colored sketch."
  sticky-label:
    background: "{colors.highlight} or {colors.paper-deep} square, rotated ±3°, ink text"
    description: "Callouts and labels. Max 3 per frame."
---

# TakeLoop Notebook — Frame

## Overview

The frame is a page in a beautifully kept science notebook. Pen drawings appear stroke by stroke
as the narrator explains, then get marker color and a highlighter sweep. Arrows, labels and little
annotations make causation visible. The tone is warm and curious, never childish.

## The Frame

- **Squint test** — one drawing dominates (40–60% of the frame); labels are small and few.
- **Life** — strokes draw on, colors fill in slightly after the line, the page drifts very slightly
  (a slow pan across the notebook) so holds never freeze.
- **Safe area** — content stays above y = 900 (caption band) and inside 76px edges.

## Colors

`paper` ground, `ink` for every line and word. `highlight` is the emphasis color. Marker red/blue/
green fill drawn objects; keep at most two marker colors per frame.

## Typography

Noto Serif SC for headlines and hero words, Noto Sans SC for labels, JetBrains Mono for numbers.
Text is ink; emphasis is the highlighter behind it, not a text color.

## Do

- Draw everything with pen strokes, seeded wobble, and stroke-dashoffset draw-on.
- Use arrows, numbered steps and sticky labels to show cause → effect.
- Pan the "page" slowly; let hand-drawn imperfection be deterministic (seeded).

## Don't

- No vector-clipart perfection, no drop shadows, no glossy gradients, no stock icons.
- No more than three labels per frame; never render narration sentences as on-screen text.
