# Style library — looks that recur in popular Opus-made videos, and how to build each

Name the style in STORYBOARD `## Video direction` and implement it consistently in every frame.
A named style ("Vox paper-collage", "sand animation", "Apple-keynote one take") encodes palette
and pace better than adjectives. All recipes are deterministic (seeded PRNG, timeline-driven).

| Style | Reads as | Best for | Preset base |
|---|---|---|---|
| Line-art unfolding | a pen sketching as it talks | history sweeps, explainers | notebook |
| Ink wash 水墨 | scroll painting, literati | Chinese history/poetry | ink |
| Antique atlas | explorer's map, gold routes | wars, routes, empires | atlas |
| Deep-space glow | planetarium, documentary | physics, astronomy, tech | deepspace |
| Paper-collage (Vox) | cut paper + photo scraps + marker | explainers, journalism | notebook / biennale-yellow |
| Paper-cut / origami | layered cut paper with soft shadows | wordless stories, kids | notebook |
| Sand animation | sepia silhouettes on a light table | history montage, poetry | atlas |
| Watercolor / acrylic / oil | painted, brush texture | music videos, landscapes, emotion | any light ground |
| Halftone / risograph | print dots, 2–3 inks | music videos, posters, portraits | biennale-yellow / broadside |
| Pixel art 16-bit | game sprite, low-res | tech nostalgia, games, kids | custom palette |
| Blueprint / wireframe | engineering drawing | machines, architecture, how-it-works | cobalt-grid |
| Isometric | tidy 3D diagram | systems, cities, processes | any |
| Engraving hatch | old book plate | history, science history | atlas |
| Kinetic typography | words are the visual | hooks, quotes, promos | any |
| Apple-keynote one take | one continuous camera, no cuts | product, premium explainers | blue-professional / deepspace |

## Recipes

### Line-art unfolding
Seeded wobbly SVG paths (frame-worker.md → hand-drawn), drawn on with `strokeDashoffset` in
narration order; 3–4px ink, round caps; color fills arrive 0.2–0.4s after the line, offset 4–8px.
A slow pan across one long "page" connects frames. Text can wobble: per-character tiny rotation
stepped every 0.12s from a seeded table (boil).

### Ink wash 水墨
SVG filter on brush strokes and washes:
```html
<filter id="f03-ink"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="7"/>
  <feDisplacementMap in="SourceGraphic" scale="9"/><feGaussianBlur stdDeviation="0.6"/></filter>
```
Mountains: 3–5 ridge paths (seeded noise along x) filled ink-mist→ink-wash, more blur with
distance, parallax pan. Washes bloom: tween `r` + opacity of a filtered circle/ellipse. Seal stamp:
red square, paper-white characters, `scale 1.08→1` press. Vertical titles: `writing-mode: vertical-rl`.

### Paper-collage (Vox style)
Torn-paper shapes = polygons with seeded jagged edges + a subtle drop shadow (`filter: drop-shadow
(0 4px 0 rgba(0,0,0,.18))` — the one style where shadows are correct); photo scraps (Commons
images) with halftone or duotone grade; hand marker underlines and circles drawn on; tape strips.
Elements slide in with slight rotation and settle (overshoot ok on transforms). Camera pushes
across a corkboard/desk of pieces.

### Paper-cut / origami
3–6 flat color layers stacked with offset shadows to fake depth; layers parallax on camera moves;
folds = polygon pairs with one face darker, unfolding via `scaleX` from the crease (`svgOrigin`
on the crease line, set in from AND to).

### Sand animation
Light-table ground (warm radial glow from beneath), silhouettes in dark sepia drawn as filled
paths, a Canvas grain layer (seeded dots, 1–2px, 8–15% alpha) over everything. Transitions = the
"hand sweeps sand": a soft-edged mask wipe with grain particles streaking along the wipe edge.
Year labels hand-written style, sepia.

### Watercolor / acrylic
Per shape: 3–6 translucent polygons (alpha .08–.15) with seeded noise-displaced edges, `mix-blend-
mode: multiply`, slightly misregistered from the pen line; paper texture on top. Brush strokes
(acrylic): many thin overlapping strokes along a path with jittered width/color. p5.brush is the
library the P(doom) MV used — doable in a frame via p5 instance mode with `noLoop()` and `redraw()`
from a timeline proxy, but only if everything it paints is a pure function of t (re-seed
`randomSeed()` every redraw).

### Oil-painting look (Kuwahara)
For a Three.js or Canvas scene, add a post pass. Simplest: render the scene to a canvas, then a
second WebGL quad with a 4-sector Kuwahara fragment shader (radius 4–6px) — this is what made the
Austerlitz film read as a painting. Keep geometry simple; the filter adds the craft.

### Halftone / risograph
Canvas: sample a source (an image in `public/` or your own drawn canvas) into a grid; draw a dot
per cell with radius ∝ darkness; 2 ink colors offset 2–3px (misregistration); paper texture.
Animate the cell size or dot threshold over time for "printing in". Same-origin images only
(`public/`), and sample once at build time, not per frame.

### Pixel art 16-bit
Render into a low-res canvas (e.g. 320×180) and display it scaled with
`image-rendering: pixelated; width:1920px; height:1080px`. ≤ 24 hand-picked colors, no
anti-aliasing (`ctx.imageSmoothingEnabled = false`, integer coordinates), animation stepped at
8–12 fps (`Math.floor(t * 10) / 10` before drawing). State machines (IDLE→CHARGE→CAST→RECOVER)
for characters.

### Blueprint / wireframe
Ground #1E4A8C with a 40px white grid at 12% and a 200px grid at 22%; white 2px line art drawn on;
dimension lines with arrowheads and mono measurements; exploded views = parts translating apart
along their axes (the "camera lens cutaway" explainer with 3.2M views used exactly this).

### Isometric
SVG with iso projection `x' = (x - y) * cos30`, `y' = (x + y) * sin30 - z`; or CSS on a `.world`:
`transform: rotateX(60deg) rotateZ(-45deg)` with children extruded via stacked offsets. Build
systems block by block on the narration.

### Engraving hatch
SVG `<pattern>` of thin parallel lines (rotated 30–45°) at 2–3 densities as "tones"; shapes filled
with the pattern, ink outline; vignette. Pairs with atlas plates.

### Kinetic typography
Big words as the visual; per-character or per-word reveals (`hyperframes-animation` has 24 named
text effects — read `adapters/animate-text.md`); words swap in place on beats; scale contrast
3:1+. For Chinese, animate per character; never split a two-character word across lines.

### Apple-keynote one take
One element (a device, a shape, a card) never leaves; everything morphs from it; no cuts, fades or
blurs between ideas; the camera travels continuously (`3d-camera-flight`, `viewport-change`). In
the storyboard: all frames share one stage and use `cut` transitions placed on identical states,
or build it as a single long frame with phases.

## Registry first

Before hand-building film grain, glitch, CRT, chromatic aberration, shimmer, confetti, shader
transitions, charts, maps widgets or code windows: `npx hyperframes catalog --query "<look>" --json`.
