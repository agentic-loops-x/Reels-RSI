---
version: 1
name: Reels-RSI Chalk — Frame (video / frame layer)
description: >
  A classroom blackboard for worked problems and lessons — 小学到高中的数学、物理、化学、语文讲解.
  Deep green-black board with faint eraser haze, chalk lines drawn on stroke by stroke (seeded
  wobble, slightly dusty edges), formulas written step by step, colored chalk for the one thing
  that matters in each step. Noto Serif SC for titles, Noto Sans SC for labels, JetBrains Mono /
  KaTeX for numbers and formulas. Feels like the best teacher you had, working it out with you.
unit: the frame — 1920×1080 primary; 9:16 and 1:1 supported
principle: one step per beat · the answer is verified before it is drawn · colour marks what changed

colors:
  ground: "#22302B"
  ground-deep: "#18231F"
  ink: "#F2EFE6"
  ink-soft: "#B9BFB8"
  chalk-yellow: "#F4D35E"
  chalk-pink: "#F08A9B"
  chalk-blue: "#8EC5E8"
  chalk-green: "#9BD39B"

typography:
  body:       { fontFamily: "Noto Sans SC", px: 32, weight: 400, lineHeight: 1.5, color: "ink" }
  micro-label:{ fontFamily: "Noto Sans SC", px: 18, weight: 600, tracking: "0.2em", color: "ink-soft" }
  mono-data:  { fontFamily: "JetBrains Mono", px: 40, weight: 500, tracking: "0.02em" }
  headline-sm:{ fontFamily: "Noto Serif SC", px: 64, weight: 600, lineHeight: 1.15 }
  headline:   { fontFamily: "Noto Serif SC", px: 104, weight: 700, lineHeight: 1.1 }
  display:    { fontFamily: "Noto Serif SC", px: 160, weight: 800, lineHeight: 1.0 }

spacing:
  pad-edge: "80px"
  gap-region: "44px"

components:
  board:
    background: "{colors.ground} with a soft radial lighter centre, faint eraser smudges (seeded, 3–5% opacity), a thin wooden frame edge optional"
    description: "The ground on every frame."
  chalk-line:
    stroke: "{colors.ink} 3–5px, butt caps on reveal masks, seeded wobble 1–2px, a dusty edge via a weak feTurbulence displacement (scale ≤ 1.5)"
    description: "All figures, axes, arrows and underlines. Drawn on as the narration names them."
  chalk-writing:
    text: "formulas and working written left→right, one line per step, each line revealed on its spoken word"
    description: "Use KaTeX (pinned) for real notation; strike through and rewrite instead of morphing."
  colored-chalk:
    stroke: "{colors.chalk-yellow} for the quantity being solved for, {colors.chalk-pink} for what changed this step, {colors.chalk-blue} for givens, {colors.chalk-green} for the checked answer"
    description: "Colour is meaning, never decoration. Max two colours per step."
  answer-box:
    stroke: "{colors.chalk-green} rectangle drawn around the final answer, plus a ✓ after the check"
    description: "Only after the answer has been verified on screen (substitute back)."
---

# Reels-RSI Chalk — Frame

## Overview

The frame is a blackboard during a great lesson. The problem is written first, then the teacher
draws a picture of it, then works it out one step per beat, colouring what changed, and finally
checks the answer by putting it back into the problem. Calm, clear, never childish.

## The Frame

- **Squint test** — one figure or one line of working dominates; earlier steps dim to ink-soft.
- **Life** — chalk draws on; the camera drifts slowly toward the line being written; a light dust
  puff (seeded particles) when a box or check mark lands.
- **Safe area** — content stays above y = 900 (caption band) and inside 80px edges.

## Do

- Write the problem on screen first (short), then a picture (线段图 / 图形 / 受力图 / 分子模型).
- One step per beat; keep the previous step visible but dimmed so the chain of reasoning stays readable.
- Show the check: substitute the answer back and mark it ✓ in green.

## Don't

- No answer the script has not verified. No skipped steps a student of that grade could not follow.
- No clip-art children, no cartoon mascots, no neon, no glossy cards.
