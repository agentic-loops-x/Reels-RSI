# Quality bar — what separates a polished explainer from an animated slide deck

Read before Step 4 (look-dev) and again at Step 7 (review). Every rule here came from comparing a
first EvoFilm film against the viral Opus-made explainers: the framework was never the bottleneck —
**the drawing, the camera and the sound were.**

## The five gaps (and the fix for each)

| Gap | Looks like | Fix |
|---|---|---|
| **Thin visuals** | flat line diagrams, a stick figure, 60% empty paper | The hero visual fills 40–60% of the frame and is *rich*: 3D (Three.js) or procedural (Canvas: particles, fields, flows) or hand-drawn texture (seeded wobbly strokes + marker fill) or generated illustration under code layers. Minimum 3 depth layers on every frame. |
| **Dead camera** | each frame is a still stage; things appear then freeze | One continuous camera move per frame (push-in / drift / parallax / orbit) on a `.world` wrapper; background layers move slower than foreground. Holds keep an ambient idle (twinkle, flow, slow rotation). |
| **Slide rhythm** | element → pause → element, same easing, same timing | Overlapping action: start the next entrance while the previous settles; vary durations; within-frame cuts (zoom-through, match cut) for long frames (>8s). |
| **Silent craft** | voice + a drone, no punctuation in sound | SFX on every reveal that matters (whoosh on camera moves, pop/tick on labels, chime on the payoff, swell into the climax, impact on a big number) and a real music bed when the user supplies one. |
| **One pass** | bugs fixed, aesthetics never revisited | Look-dev gate (2 hero frames approved before the rest) + a scored review pass (below) with at least one fix round. |

## Visual rules

1. **One idea, one hero per frame.** The hero is the thing being explained (the molecule, the wave,
   the planet), never a title card. Titles are small labels, the visual carries the frame.
2. **Show the mechanism moving.** If the narration says "light scatters", light must visibly
   travel, hit, and scatter — particles/rays in motion, not arrows on a still diagram.
3. **Density with order.** 3 depth layers: ground (star field / grid paper / gradient) · mid
   (haze, context objects, secondary diagram) · hero. Squint test: one thing wins.
4. **Real scale cues.** Numbers on screen are short (`450 nm`, `5.8×`, `1/λ⁴`) and always from the
   script; never invent figures.
5. **No narration on screen.** Captions already print the words. On-screen text = labels, numbers,
   a 2–6 character hero word at most.
6. **Banned** (they read as template/AI slop): purple-blue gradients, lens flares, RGB splits,
   neon outlines, glossy cards with drop shadows, bokeh, stock icons, bouncy elastic easing everywhere.

## Motion rules (HyperFrames "premium motion", applied)

1. Nothing fully stops — holds idle (sine drift ≤ 2%, twinkle, flowing particles).
2. The camera is an actor — one motivated move per frame (`multi-phase-camera`, `viewport-change`,
   `3d-camera-flight` rules). Push in when the idea narrows, pull back when it generalizes.
3. Overlap entrances; offsets shorter than durations.
4. Compound properties only when they say one thing (rise + fade = arrival).
5. Mass overshoots on transforms only — never on data values.
6. Depth planes move at different rates; occlusion beats blur.
7. Pace to genre: an explainer beat is 2–5 s; a frame longer than ~8 s needs an internal cut or a
   second camera phase.
8. Hand-made imperfection must be seeded (deterministic PRNG), stepped on frame-quantized holds.

Test: name what each movement means in one sentence. If you can't, cut it.

## Sound rules

- Voice is king: music bed under narration (assembler ducks it automatically); SFX volume 0.2–0.4.
- Cue SFX in the storyboard as `- sfx: whoosh@0.0, pop@2.3, chime@6.1` (seconds from frame start,
  aligned to the visual beat and the spoken word). Typical film: 1–3 SFX per frame.
- Library: whoosh · whoosh-soft · pop · tick · click · chime · swell · impact · sparkle.

## Review rubric (Step 7) — score every frame 1–5, fix anything below 4

Look at the contact sheet (30% / 60% / 92% samples per frame) and the frame's code.

| # | Criterion | 5 looks like |
|---|---|---|
| R1 | Hero richness | the hero visual is detailed, fills ~half the frame, would look good as a still |
| R2 | Mechanism shown | the narration's cause→effect is visibly happening, not just labelled |
| R3 | Camera & life | the three samples differ by camera position, not only by added elements; holds idle. **Solve films:** guiding the eye instead — the spoken step is singled out, earlier steps dim; a still board is fine |
| R4 | Pacing | reveals land on their spoken words; nothing front-loaded; no dead second >1.5 s |
| R5 | Composition | 3 depth layers, clear hierarchy, nothing in the caption band, nothing clipped |
| R6 | Consistency | palette/type from frame.md; the frame belongs to the same film as its neighbours |

A film is done when every frame scores ≥ 4 on all six, `check` passes with 0 errors / 0 warnings,
and the rendered MP4 has audible voice + music (mean volume around -20 to -26 dB).
