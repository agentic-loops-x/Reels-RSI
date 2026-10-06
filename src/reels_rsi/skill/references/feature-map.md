# Feature map — what popular AI-made videos do, and where Reels-RSI covers it

Survey (2026-10-05) of the public indexes: claudevideo.org (1,235 videos), awesome-opus-5.5-video
(1,299), awesome-claude-video, opus-video-prompts (54 with prompts), awesome-ai-motion, dev.to
"13 clips", apimaster prompt patterns, awesome-claude-video-skills (180 tool repos).
Category mix: motion graphics 352 · explainers 195 · product/ads 181 · interactive 171 ·
stories 124 · 3D scenes 85 · art 73 · music/production 54.

Status: ✅ built & verified in a render · 📘 documented recipe (agent implements per film) ·
↪ routed to an official HyperFrames workflow · ⛔ out of scope (why)

## Genres
| Capability | Example | Status |
|---|---|---|
| Science explainer with narration | camera-lens lab (3.2M), relativity in 46 s | ✅ core pipeline |
| History sweep / event / route / biography | 中华五千年, Austerlitz, Western civ (5.8M), 81 yrs Indonesia | ✅ history mode (maps, timeline overlay, Commons plates) |
| Wordless story / character short | Pip six-act, raindrop, tadpoles (ink) | 📘 techniques.md rigs + styles.md; `music:` only |
| Product launch / SaaS / app promo | inference startup, Notion launch, print app | ↪ /product-launch-video |
| Music video / lyric / beat-synced | P(doom) MV, Claude Pop (3.3M), Bitcoin MV | ↪ /music-to-video + techniques.md |
| Short motion graphics / showreel / logo | 15-s showreels, UI morph loop | ↪ /motion-graphics |
| Talking-head captions / overlays / line-art B-roll | AI-edited talking head, B-roll | ↪ /embedded-captions, /talking-head-recut; 📘 footage recipe |
| Worked problems / lessons (math, physics, chemistry, 语文, stroke order) | 鸡兔同笼, 浮力, 静夜思 | ✅ solve mode: `chalk` preset, KaTeX, `reels hanzi` (snapshot-tested) |
| Long-form (5–12 min) | Transformer lecture (12 min), AI documentary | ✅ chapters + `reels concat` |
| Interactive web labs, games | lens lab, browser games | ⛔ not video — 📘 scripted-cursor recording instead |
| Blender / After Effects / avatars | Blender windmill, AE ads, HeyGen avatars | ⛔ needs commercial/extra software or paid accounts |

## Visual techniques
| Capability | Status |
|---|---|
| Real 3D (Three.js), camera flights, planets, molecules | ✅ (smoke render) |
| Procedural particles / flows / star fields (Canvas proxy) | ✅ |
| Maps: projections, borders, routes, pins, zoom | ✅ `reels geo` + d3 (smoke render) |
| Film-wide timeline / chapter bar | ✅ overlays (smoke render) |
| Period images with credits + Ken Burns | ✅ `reels commons` (download + CREDITS.md) |
| Hand-drawn line art, ink wash, atlas, deep-space presets | ✅ 4 presets |
| Paper-collage (Vox), paper-cut/origami, sand, watercolor, oil (Kuwahara), halftone, pixel, blueprint, isometric, engraving, kinetic type, one-take | 📘 styles.md |
| Physics simulations (bake-then-seek), character rigs + IK, infinite zoom, loops | 📘 techniques.md |
| Manim formula/graph segments | ✅ setup --manim; 📘 embed recipe |
| Generated illustration layers | ✅ `reels image` (untested: needs key) |
| Shader transitions, film grain, glitch, charts (registry ~400) | ↪ `hyperframes catalog` |

## Audio
| Capability | Status |
|---|---|
| Chinese narration with word timings | ✅ edge-tts |
| English narration | ✅ auto-detected (edge en voices) |
| Premium voices | ✅ ElevenLabs hook (untested) |
| Procedural score aware of cuts (ambient/cinematic/epic/upbeat) | ✅ `reels music` |
| SFX library + storyboard cues | ✅ `reels sfx` (9 sounds) |
| Beat grid from a track | ↪ `hyperframes beats` |

## Text & delivery
| Capability | Status |
|---|---|
| CJK karaoke captions | ✅ |
| 中英双语 captions | ✅ `**EN:**` lines (smoke render) |
| SRT export (zh / en / zh-en) | ✅ `reels srt` |
| Cover / thumbnail | ✅ `reels cover` (composition or caption-free grab) |
| Vertical 9:16 / square | ✅ format field; 📘 portrait layout rules (faceless-explainer visual-design.md) |
| Reference-video style analysis | ✅ `reels analyze` |
| Plan → look-dev → review gates, rubric scoring | ✅ SKILL.md + quality-bar.md |

## Self-improvement (Reels-RSI-only)
| Capability | Status |
|---|---|
| Run log of every finalize/render (findings, snapshots of the code per pass) | ✅ `.reels/runs.jsonl` + `history/` |
| Static rules compiled from past mistakes, each proven on a bad + good example | ✅ 12 built-in, `reels rules new` for more |
| Retro: fix diffs + feedback → proposed lessons → human accept → injected into the next film | ✅ `retro` · `lessons` · `packets` digest |
| Vision judge on R1–R6, deterministic score, blind A/B | ✅ code; judge needs a model (claude-cli / any API) |
| Reels-RSI Bench (8 topics, train/holdout) + leaderboard across models | ✅ code; a full run costs ~8 films |
| Benchmark-gated rewrite of the skill (evolve) | ✅ code [untested end-to-end: needs bench budget] |
