# Script & storyboard — the Chinese explainer recipe

## Teaching structure (pick one) — history formats are in history.md

| Structure | Use when | Shape |
|---|---|---|
| 概念讲解 concept | one phenomenon/term ("为什么天空是蓝的") | hook → one-line answer by frame 2 → mechanism layer by layer → payoff/implication → callback |
| 过程讲解 process | a procedure or chain ("疫苗如何起作用") | hook → 3–6 ordered steps on one consistent stage → result |
| 清单 listicle | parallel items ("5 个反直觉的物理现象") | hook → N co-equal items → wrap |
| 故事 story | history, discovery, case ("青霉素的发现") | setup → tension → turn → resolution → lesson |

Never follow the source article's paragraph order. Thesis lands by frame 2; everything after is evidence.

## Hook (first 3–5 s) — pick a strategy

反问 rhetorical question · 反直觉 counterintuitive claim · 惊人数字 shocking statistic · 想象一下 imagine/scenario ·
具体画面 visceral metaphor. Never open with a definition.

## Narration rules

- Speaking rate with edge-tts: 中文 ≈ 4–4.5 字/秒 (60 s ≈ 250–270 字) · English ≈ 2.6 words/s · 日本語 ≈ 5 字/秒
  (kanji + kana) · 한국어 ≈ 4 syllables/s. Budget per frame; `reels voice` writes the real durations back.
- 1–2 short sentences per frame; break into **cues** with ，—— so each visual reveal has a word to land on.
- Concrete over abstract: name the object the viewer will see ("一束白光撞上三棱镜").
- Numbers spoken the way they are shown: on screen `450 nm`, spoken "四百五十纳米".
- Fact-check every claim and number; list sources in BRIEF.md `## Notes`.
- Write numbers/English in the script as they should be *read* (edge-tts reads "λ" badly — spell "波长").

## Frame budget

| Length | Frames | Avg frame |
|---|---|---|
| 45–60 s | 7–9 | 6–8 s |
| 60–90 s | 9–12 | 6–8 s |
| 2–3 min | 14–22 | 7–9 s |

A frame over ~10 s needs a second camera phase or an internal cut.

## STORYBOARD.md frame block (Reels-RSI fields)

```md
## Frame 4 — 撞上空气分子

- scene: 阳光粒子流从左侧涌入，穿过一片三维漂浮的氮氧分子云；蓝色光点被弹向四面八方
- voiceover: "阳光冲进大气，撞上比光波小得多的氮气和氧气分子。光被弹向四面八方——这叫瑞利散射。"
- duration: 9.4s
- transition_in: push-slide LEFT
- status: outline
- src: compositions/frames/04-scattering.html
- type: feature_showcase
- persuasion: Demonstration + causal chain
- beat: Fascination
- route: canvas-particles + three
- sfx: whoosh-soft@0.1, pop@3.2, sparkle@5.4
- blueprint: compose

narrativeRole: 给出机制：微小分子把光散射向各个方向。
keyMessage: 光撞上小分子会被散射，这叫瑞利散射。

Scene 1 (0.0–1.8s): …time-coded shot lines, each reveal cued to a spoken word…
```

`route:` names the drawing technique(s) for the worker: `svg-lines` · `canvas-particles` · `three` ·
`notebook-pen` · `ink-wash` · `map` · `plate` (period image) · `sim-baked` · `rig` · `halftone` ·
`pixel` · `blueprint` · `isometric` · `collage` · `sand` · `manim-clip` · `illustration` ·
`kinetic-type` · `footage` · `registry:<block-id>` (recipes: styles.md / history.md / techniques.md).
`sfx:` is `name@seconds-from-frame-start[@volume]`, comma-separated.

Transitions: frame 1 `cut`; then 2–3 types repeated (`crossfade`, `blur-crossfade`, `push-slide LEFT`,
`zoom-through`). Same stage across consecutive frames → same transition.

## SCRIPT.md

```md
# SCRIPT — <slug>

**Voice:** zh-CN-YunxiNeural (edge-tts)
**Voice direction:** 轻松、清晰、带一点好奇。

## Line 1 — 抬头一问 (Frame 1)

**Time:** 0 – 4s

    抬头看看天空——它为什么是蓝的？
```
Only the 4-space-indented block is spoken. Frames without narration are simply left out.

**Bilingual (中英双语) captions:** add one line under the spoken block —
`**EN:** First clause | second clause | third clause` — one English part per Chinese clause
(clauses split at ，。？！；：——). `reels captions` shows each group's English under it and
`reels srt` writes zh / en / zh-en SRTs.

**English, Japanese and Korean reels:** write SCRIPT.md — and every on-screen word — in that language;
`reels voice` detects it (Hangul → ko, kana → ja) and picks the voice (en-US-AndrewNeural,
ja-JP-KeitaNeural, ko-KR-InJoonNeural; `--voice` for another). Japanese captions are cut like Chinese
(no spaces), English and Korean by words. `reels fonts` cuts the glyphs from Noto JP / KR for ja / ko
(downloaded once) under the usual family names, so presets and skins need no change; use
`"Noto Sans SC"` / `"Noto Serif SC"` in frames as usual (or the real names `"Noto Sans KR"` …).

**Music mood** comes from the storyboard frontmatter `music:` — keywords map to ambient
(科普/calm), cinematic (历史/纪录/庄重), epic (战/史诗/激昂), upbeat (轻快/产品), or `none`.
A royalty-free track dropped into `assets/music/` overrides it.
