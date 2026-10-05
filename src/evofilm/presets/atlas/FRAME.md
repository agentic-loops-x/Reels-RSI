---
version: 1
name: EvoFilm Atlas — Frame (video / frame layer)
description: >
  An antique-atlas system for world history, wars, exploration, empires and trade. Aged parchment
  with stains and foxing, sepia ink coastlines, gold-leaf lines for routes and borders, a deep
  oxblood accent for empires/armies, engraved-style labels. Maps are the hero of most frames;
  documentary portraits and paintings appear as vignetted plates. Noto Serif SC display, Noto Sans SC
  labels, JetBrains Mono for years and figures.
unit: the frame — 1920×1080 primary; 9:16 and 1:1 supported
principle: the map is the stage · gold marks what matters · every date and border is sourced

colors:
  parchment: "#EAD9B4"
  parchment-deep: "#D2BB8A"
  ink: "#3A2A1A"
  sepia: "#7A5A36"
  gold: "#C9A03C"
  oxblood: "#8E2B22"
  sea: "#B9C2A8"
  navy: "#2E3B55"

typography:
  body:       { fontFamily: "Noto Sans SC", px: 28, weight: 400, lineHeight: 1.55, color: "ink" }
  micro-label:{ fontFamily: "Noto Sans SC", px: 16, weight: 600, tracking: "0.28em", color: "sepia" }
  mono-data:  { fontFamily: "JetBrains Mono", px: 26, weight: 400, tracking: "0.04em" }
  headline-sm:{ fontFamily: "Noto Serif SC", px: 62, weight: 700, lineHeight: 1.2 }
  headline:   { fontFamily: "Noto Serif SC", px: 104, weight: 800, lineHeight: 1.1 }
  display:    { fontFamily: "Noto Serif SC", px: 176, weight: 900, lineHeight: 1.0 }

spacing:
  pad-edge: "80px"
  gap-region: "48px"

components:
  parchment:
    background: "{colors.parchment} → {colors.parchment-deep} radial vignette, seeded stains and foxing at 6–12%"
    description: "The ground on every frame."
  map-base:
    background: "Natural Earth land in {colors.parchment} with {colors.sepia} 1px coastlines, sea in {colors.sea} at 40%, graticule at 15%"
    description: "Drawn with d3-geo from assets/geo/*.js; coastlines may draw on."
  gold-route:
    stroke: "{colors.gold} 4–6px with a 1px {colors.ink} under-stroke, round caps, an arrowhead or travelling dot"
    description: "Routes, campaigns, trade lines, borders that matter — always draw on along the path."
  empire-fill:
    background: "{colors.oxblood} at 35–55% with a hatch pattern, {colors.ink} 2px edge"
    description: "Territories and armies. Expansion = the polygon morphing / revealing over time."
  plate:
    background: "a period image in public/ with a sepia grade, oval or rectangular vignette, engraved hairline frame"
    description: "Portraits/paintings from Wikimedia Commons (credited), slow Ken Burns."
  cartouche:
    background: "an ornamental label frame (hairlines + small flourishes) around a place or date"
    description: "Titles and key dates on the map."
---

# EvoFilm Atlas — Frame

## Overview

An explorer's atlas brought to life: the camera flies across a parchment map, gold routes draw
themselves, empires swell and recede, armies move as oxblood arrows, cartouches name places and
years, and period portraits appear as vignetted plates.

## The Frame

- **Maps are the stage** — most frames are a map at some zoom; zoom in to a battle, pull back to the
  continent. One continuous camera move per frame (scale + translate of the map group).
- **Depth** — parchment ground · map base · routes/territories · labels/plates on top.
- **Safe area** — nothing important below y = 900.

## Do

- Draw coastlines and routes on; let territories expand along real geography.
- Mark every date and figure from the script; say "约" for approximate borders.
- Use period images (public domain / CC) with credits for people and events.

## Don't

- No glossy UI, drop shadows, neon, or modern flat icons on the map.
- No unsourced borders presented as exact; no invented portraits of real people.
- Never render narration sentences on screen.
