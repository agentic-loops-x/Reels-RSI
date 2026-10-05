---
name: evofilm
description: "EvoFilm — an AI film director that evolves with every film. Turns a topic into a narrated, captioned, scored video rendered from code (HyperFrames: SVG/Canvas/Three.js/maps): 科普讲解、历史简介/朝代/战役/人物、题目讲解（小学到高中数学/物理/化学/语文，板书+公式+笔顺）、故事短片. Chinese-first (TTS word timing, CJK/bilingual captions, font subsetting), English too. Learns from every film: checks compiled from past mistakes, lessons, a benchmark. Use whenever the user asks for a video/视频/短片/讲解视频/历史视频/解题视频, 'like the viral AI-made explainers', or types /evofilm."
---

# EvoFilm — direct a film, then learn from it

You are the director. Every frame is a HyperFrames HTML composition rendered frame by frame by
headless Chrome — code, not a video model. All deterministic steps are `evofilm <command>`
(on PATH; `evofilm --help`). Works in any agent that can read files, write files and run
commands; sub-agents are optional.

**First run:** `evofilm doctor` — if fonts/SFX are missing run `evofilm setup`.
**Every run:** read `references/quality-bar.md` (defines done), and run
`evofilm lessons digest` — those are lessons from past films; follow them.

## Route by genre

| The user wants… | Read | Preset |
|---|---|---|
| 科普/讲解 (explain an idea or process) | script-and-storyboard.md | `deepspace` 物理/天文/科技 · `notebook` 生活/生物/地理 |
| 历史/人物/战役/朝代/文明 | history.md | `ink` 中国史/诗词 · `atlas` 世界史/航线 · `notebook` 线稿速览 |
| 题目讲解 / 知识点 / 古诗 / 笔顺 | solve.md | `chalk` 板书 · `notebook` 低龄 · `ink` 古诗文 |
| 故事短片 / 无台词 | techniques.md, styles.md | any; `music:` only, no SCRIPT.md |
| "照着这个视频的风格做" | `evofilm analyze <video>` first, then the matching row | — |
| > 3 min | chapters, each its own project → `evofilm concat` | — |
| product promo / MV / ≤15 s motion graphic / captions on footage | the matching HyperFrames workflow (`npx hyperframes skills`); ship Chinese with `evofilm fonts` + `evofilm captions` | — |

## Step 0 — Brief (one short round, recommendations first)

Ask only what the request leaves open, in one message, each with a recommended default:
题目 & 角度 (one-line thesis) · 时长 (60–90 s; ≈ 4.5–5 字/秒) · 画幅 (16:9 B站/YouTube · 9:16 抖音/视频号)
· 风格 (preset above, or a named look from styles.md) · 配音 (zh-CN-YunxiNeural 男声活泼 ·
XiaoxiaoNeural 女声温暖 · YunjianNeural 浑厚 · en-US-AndrewNeural; ElevenLabs if `ELEVENLABS_API_KEY`)
· 字幕 (中文 · 中英双语 · none) · 音乐 (user track in `assets/music/`, else a mood) · 审阅 (**yes**: plan → look-dev → final).
"直接做 / don't ask" ⇒ take every default, state them in one line, no gates.
A photo of a problem (练习册拍照) → solve.md "Problem from a photo": transcribe it and restate it at the plan gate.

## Step 1 — Research & facts

Verify every claim, number, date and name (history: two sources for contested facts; solve: compute
the answer in code). Write `BRIEF.md` (frontmatter `workflow: faceless-explainer`, `flow: automation`,
`storyboard`, `message`, `destination`, `aspect`, `language`, `audience`, `length`, `angle`, `voice`,
`style_preset`; body `## Intent`, `## Notes` with sources/computations).

## Step 2 — Project

```bash
evofilm new videos/<slug> --preset <preset> --title "<标题>" --desc "<一句话>"
```
Then write BRIEF.md and `capture/extracted/visible-text.txt` (facts) into it; every later command runs
inside the project. Maps: `evofilm geo --project . --layers countries,coastline,rivers`. Period images:
`evofilm commons search "…"` / `evofilm commons get --project . --name x "File:…"`. 笔顺: `evofilm hanzi 字 --project .`.

## Step 3 — Script & storyboard

`SCRIPT.md` (`## Line N — … (Frame N)` + indented spoken text; `**EN:**` lines for bilingual) and
`STORYBOARD.md` (frontmatter `format`, `duration`, `message`, `arc`, `audience`, `mode`, `music`; per
frame `## Frame N — title` with `scene`, `voiceover`, `duration`, `transition_in`, `status: outline`,
`src: compositions/frames/NN-name.html`, `route`, `sfx`, `keyMessage`). Details: script-and-storyboard.md.
**Gate:** present thesis, frame list (see / hear / route), length, style, voice, music — wait.

## Step 4 — Voice, timing, music

```bash
evofilm voice --project . [--voice …] [--rate +5%]
```
Voices every line, writes word timings to `audio_meta.json`, syncs real durations into the
storyboard, builds the music bed on the real cuts. Re-voice one frame: `--only 3`.

## Step 5 — Visual design

Write `## Video direction` once in STORYBOARD.md (palette roles, named style, motion grammar, rhythm,
negative list). Per frame, a time-coded shot list cued to the spoken word times: one camera move per
frame, a rich hero (quality-bar.md). Film-wide elements (year ruler, chapter bar) → an overlay
(`compositions/overlays/<name>.html`, history.md).

## Step 6 — Build frames

```bash
evofilm packets --project .     # .evofilm/packets/_role.md + one packet per frame (incl. word times + lessons)
evofilm fonts --project .
```
**6a Look-dev:** build two hero frames first (frame 1 + the most visual one) and any overlay; mark them
`animated`; `evofilm finalize .`; look at `snapshots/contact-sheet.jpg`. **Gate:** "这个画面方向对吗？"
**6b The rest:** with sub-agents, one per frame in parallel — each gets the project path, its
frame id and the approved hero frames as reference, and is told: *read `.evofilm/packets/_role.md`
and your packet, write only your frame, run `evofilm lint --frame <id>`, reply with one line.*
Without sub-agents, build them yourself in order from the same packets. Mark each `status: animated`.

## Step 7 — Finalize & review loop

```bash
evofilm finalize .
```
fonts → captions → music → SFX → assemble → overlays → transitions → HyperFrames check (lint,
runtime, layout, contrast) → **EvoFilm rules** (mistakes earlier films made) → SRT → snapshots.
Every pass is logged in `.evofilm/`. Fix every error and warning in the frame files (never the
generated index). Score each frame on R1–R6 from the contact sheet (`evofilm score .` adds a vision
judge when one is configured); anything < 4 → fix → finalize again. ≥ 1 round, ≤ 3.
Closer look: `evofilm times --project . --frame 04` → `evofilm hf --project . snapshot --at <t>`.

## Step 8 — Render & deliver

```bash
evofilm render . --quality high
evofilm cover --project . --composition    # if compositions/cover.html exists
evofilm cover --project . --frame 08       # else: the most telling frame alone, caption-free
```
Deliver `renders/video.mp4`, `renders/cover.jpg`, `renders/subtitles*.srt`, `CREDITS.md` if any;
duration; frame ids for edits; what was defaulted.

## Step 9 — Learn (always, takes a minute)

1. Record every remark the viewer made during the run, verbatim:
   `evofilm feedback --project . "字幕太小了" [--frame 04] [--approve]`.
2. `evofilm retro .` — proposes lessons from the run log, the fix diffs and the feedback into the
   inbox (with no retro model configured: `evofilm retro . --evidence-only`, read
   `.evofilm/retro/evidence.md`, and file ≤ 3 lessons yourself with
   `evofilm lessons add "…" --kind doc|rule|taste --scope frame|director|history|solve`).
   A good lesson is general ("map labels stay above y=900 because…"), never a fact about this topic.
3. Show the inbox (`evofilm lessons list --state inbox`) and ask which to keep; accept only what
   the viewer approves (`evofilm lessons accept <id>`). A `rule` lesson is accepted with a working
   check: `evofilm rules new <id>`, write `rule.py` + `bad.html` + `good.html`, `evofilm rules test <id>`,
   then `evofilm lessons accept <id> --rule-dir ~/.evofilm/rules/<id>`.
In "直接做" mode, leave proposals in the inbox and mention how many are waiting.

## Edits after delivery

Change only what was asked: copy → SCRIPT.md + `evofilm voice --only N` + frame text → finalize →
render. Visual → that frame's HTML → finalize → render. Never rebuild untouched frames.
Record the request with `evofilm feedback` — edits are the best lessons.

## Optional upgrades (auto-enabled by environment)

`ELEVENLABS_API_KEY` → ElevenLabs voices [untested] · `OPENAI_API_KEY` / `GEMINI_API_KEY` →
`evofilm image` illustration layers under code layers [untested] · a track in `assets/music/` → the bed
· a judge model (`evofilm config set roles.judge provider:model`) → `evofilm score` grades frames.

## Known traps (handled by the commands — don't undo them)

Kokoro cannot speak Mandarin → edge-tts · whisper returns a Chinese sentence as one word → TTS word
timings · stock captions join words with spaces → `evofilm captions` · the render Chrome has no CJK
fonts → `evofilm fonts` + @font-face in every frame · the assembler drops the captions track kind →
finalize re-adds it · npm can serve an unpublished CLI → projects pin their HyperFrames version.
