# Advanced techniques — what the standout videos do that templates don't

## Simulations: bake, then seek
Anything stateful (physics, flocking, fluid, a falling jelly) cannot be integrated frame-to-frame
in a seekable render. Bake it: at build time, step the simulation at a fixed dt for the whole
duration (seeded), store positions per step in arrays, then draw step `Math.floor(t / dt)` (lerp
to the next step) inside the timeline proxy. Seeking to any t is then exact and parallel-safe.
```js
const DT = 1 / 60, STEPS = Math.ceil(D / DT) + 1, frames = [];
let state = init(seed); for (let i = 0; i < STEPS; i++) { frames.push(snapshot(state)); state = step(state, DT); }
function draw(t) { const i = Math.min(STEPS - 2, Math.floor(t / DT)); render(lerp(frames[i], frames[i + 1], t / DT - i)); }
```
Keep bakes small (≤ a few MB of numbers) — bake at 30–60 Hz, not more.

## Characters: SVG rigs
A character is a tree of `<g>` groups (body → upper arm → forearm → hand), each with its pivot as
its `transform-origin` (`svgOrigin` in GSAP, from AND to). Walk/idle cycles are sine functions of t
on joint angles inside one proxy `onUpdate` (stepped at 12 fps for a hand-made feel). Two-bone IK
for a foot or hand target: with bone lengths a, b and target distance d,
`elbow = acos((a² + d² − b²) / (2ad))` offset from the target angle. Mouth/eyes: swap
pre-drawn shapes on a stepped schedule (blinks every 2.5–4 s from a seeded table). Wordless stories
(the "Pip" six-act short) live on a rig, a consistent palette and acting beats, not on dialogue.

## Infinite zoom (room → cell → atom)
Each scale is a group nested inside a small region of the previous one; one camera tween scales
the world by 10–100× per segment (exponential: tween `log(scale)` linearly via a proxy). Every
handoff shares a shape, color or motion vector with the next scale. Fade the outer level only
after the inner level fills the frame; motion blur on the fastest part sells speed.

## One continuous take
See styles.md → Apple-keynote. Technically: one frame (or several frames whose boundary states are
pixel-identical with `cut` transitions) driven by a single camera state object tweened leg by leg.

## Loops (social, banners)
First and last frame identical: drive everything from `phase = t / D` with periodic functions, or
end each tween where it started. Verify by snapshotting t=0 and t=D−1/30 and diffing.

## Music-driven cutting
When a music track drives the edit (MV, beat-synced promo), route to the HyperFrames
`/music-to-video` workflow. Inside a EvoFilm project, `npx hyperframes beats` (via `evofilm hf`) writes
`beats/<audio>.json`; snap frame durations and SFX cues to the beat grid, cut on downbeats, put
the biggest visual change on the drop. Mix SFX below the music at their measured peaks.

## Real footage + code (B-roll, documentaries)
Talking-head → line-art B-roll, documentary with real clips: the clip is a muted `<video class=
"clip">` (direct child of `#root`, never nested in a timed element) with code layers above it.
Captions on existing footage → `/embedded-captions`; designed overlays on interviews →
`/talking-head-recut`; cutting raw takes by transcript → video-use (not installed; needs an
ElevenLabs Scribe key).

## Long-form (> 3 minutes)
Split into chapters (each its own EvoFilm project, 60–180 s, shared preset/voice/music mood),
render each, then `evofilm concat final.mp4 ch01 ch02 …` (joins video and SRTs).
A chapter card overlay at each chapter start keeps viewers oriented.

## Interactive labs → video
The most-viewed explainers were interactive web labs (a camera lens you can pull apart). For video,
script the "user": a visible cursor drags the control on its spoken cue while the lab responds —
the `cursor-ui-demo` / `panel-edit-live-sync` blueprints in hyperframes-animation.
