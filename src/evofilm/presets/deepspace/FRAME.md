---
version: 1
name: EvoFilm Deep Space — Frame (video / frame layer)
description: >
  A dark, cinematic science-explainer system for physics, astronomy, chemistry and technology.
  Deep night-navy ground with a faint star field, luminous line work and glowing focal objects,
  one warm amber accent for "energy / the answer", one cool cyan for "signal / data". Noto Serif
  SC for display, Noto Sans SC for labels, JetBrains Mono for every number and unit. Depth comes
  from light — glow, haze and parallax layers — never from drop shadows or cards.
unit: the frame — 1920×1080 primary; 9:16 and 1:1 supported
principle: light is the depth · one glowing focal object per frame · numbers come from the script

colors:
  canvas: "#0A0F24"
  canvas-deep: "#060918"
  haze: "#1A2350"
  ink: "#ECE8DC"
  ink-dim: "#9AA3C7"
  amber: "#FFC24D"
  cyan: "#6FD3FF"
  coral: "#FF7A59"

typography:
  body:       { fontFamily: "Noto Sans SC", px: 30, weight: 400, lineHeight: 1.5, color: "ink" }
  micro-label:{ fontFamily: "Noto Sans SC", px: 16, weight: 500, tracking: "0.3em", upper: true, color: "ink-dim" }
  mono-data:  { fontFamily: "JetBrains Mono", px: 28, weight: 400, tracking: "0.04em" }
  headline-sm:{ fontFamily: "Noto Serif SC", px: 64, weight: 500, lineHeight: 1.15 }
  headline:   { fontFamily: "Noto Serif SC", px: 104, weight: 600, lineHeight: 1.1 }
  display:    { fontFamily: "Noto Serif SC", px: 180, weight: 700, lineHeight: 1.0 }
  numeral:    { fontFamily: "JetBrains Mono", px: 200, weight: 700, lineHeight: 0.95 }

spacing:
  pad-edge: "76px"
  gap-region: "48px"

components:
  star-field:
    background: "{colors.canvas} with 120–240 seeded 1–2px dots in {colors.ink} at 15–60% opacity, 2–3 parallax depths"
    description: "The ground on every frame. Seeded positions (deterministic). Drifts slowly with the camera."
  focal-glow:
    background: "radial {colors.amber} or {colors.cyan} 35–60% core → transparent, behind the focal object"
    description: "The primary depth layer — the eye lands where the light is. One per frame."
  haze-band:
    background: "soft linear/radial {colors.haze} at 40–70%"
    description: "Atmosphere: a horizon glow, a nebula wash, the edge of a planet."
  line-work:
    stroke: "{colors.ink} 2–3px (diagrams) · {colors.cyan} for signals/waves · {colors.amber} for energy/answers"
    description: "Every diagram is luminous line art — draw it on (stroke-dashoffset), never pop it in whole."
  data-label:
    typography: "{typography.mono-data}"
    description: "Every figure and unit (nm, km/s, ×) in mono, ink or ink-dim."
  hairline:
    rule: "1px {colors.ink} at 18%"
    description: "Only separator. No boxes, no cards."
---

# EvoFilm Deep Space — Frame

## Overview

A planetarium-show register: the frame is **night**, the content is **light**. Every frame is a
dark field with a seeded star field and one luminous focal object (a planet, a wave, a molecule,
a formula) surrounded by a soft glow. Line diagrams are drawn in light; numbers are mono. The mood
is calm wonder — closer to a documentary title sequence than a slide deck.

## The Frame

- **Squint test** — after a blur you still find the one glowing focal object; everything else recedes.
- **Density** — the focal object fills 40–60% of the frame; 3 depth layers minimum (stars · haze/mid · focal).
- **Camera** — every shot has one slow camera move (push-in, drift, parallax); stars move slowest.
- **Safe area** — content stays above y = 900 (caption band) and inside 76px edges; glows and stars bleed.

## Colors

`canvas` is the universal ground (never pure black). `ink` is all text and neutral line work.
`amber` = energy, heat, "the answer", the sun. `cyan` = signal, data, cold light, waves. `coral` only
for warm-end phenomena (sunsets, red light, danger). Spectrum colors may appear as data colors when
the topic demands it (light, rainbows), slightly desaturated so they glow rather than shout.

## Typography

Noto Serif SC (500–700) for every headline and hero word; Noto Sans SC for labels and short body;
JetBrains Mono for all numerals, units and formulas' numbers. Text is ink or ink-dim — never amber
or cyan text except a single hero number.

## Do

- Ground every frame in canvas + star field; put a focal glow behind the hero.
- Draw diagrams on with strokes; let light travel (beams, waves, particles) to show causation.
- Keep one slow camera move alive under every shot; give holds an ambient idle (twinkle, drift).

## Don't

- No cards, drop shadows, rounded panels, neon outlines, lens flares, RGB splits, or purple-blue "AI" gradients.
- No pure #000 ground, no more than one glow per frame, no rainbow text.
- Never render a narration sentence as on-screen text.
