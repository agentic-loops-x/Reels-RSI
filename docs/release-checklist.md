# Release checklist (manual verification before going public)

Tick every box on a clean setup before the first public push. ✅ = already verified during development.

## A. Install from scratch
- [x] On a machine/user without ~/.reels: `uv tool install git+<repo>` (or `uv tool install -e .` from a clone)
- [x] `reels setup` downloads fonts from Google Fonts (dev run copied them locally — the download path is unverified)
- [ ] `reels install` → skill appears in Claude Code (`/reels` shows up)
- [x] `reels doctor` all green
- [ ] CI passes on GitHub (Linux) — never run yet

## B. One reel per mode, made from zero inside an agent (`/reels …`)
| Reel | Checks |
|---|---|
| [ ] 科普 60 s, 16:9, deepspace | plan gate → look-dev gate → finalize clean → render → cover → SRT |
| [ ] 历史 60 s, ink or atlas, with a map + Commons image | maps correct, timeline overlay, CREDITS.md |
| [x] 解题, 9:16, chalk — 相遇问题 (55 s) + a real textbook problem from a photo (84 s) | answer verified in BRIEF, KaTeX, check step on screen |
| [~] English 30 s | English voice, word-gapped captions — voice → captions → SRT smoke-tested (placeholder frames) |
| [~] bilingual 中英 | `**EN:**` lines, zh-en SRT — smoke-tested (placeholder frames), captions show EN under zh |

For each: `reels voice` (real TTS run), `packets`, `finalize`, `render`, `cover` all via Reels-RSI
(✅ finalize/new/fonts/hanzi verified; voice, packets, render, cover not yet run through Reels-RSI).

## C. Self-improvement loop
- [x] Log in the standalone CLI (`claude` → /login) or set an API key; `reels doctor` now checks the login (the desktop app's login does not count)
- [x] `reels score <reel>` returns judge scores — fixed: portrait sheets were downscaled to ~200 px per frame; solve reels get an eye-guiding R3. Judge pixel/proportion claims remain unreliable (human gate)
- [x] `reels feedback` + `reels retro <reel>` — model retro proposed 5 lessons on the textbook reel (1 false, from a judge misreading → retro prompt now weighs evidence)
- [x] accept doc lessons → digest appears in `.reels/packets/_role.md` (8 accepted)
- [x] lesson compiled into a rule (`visible-from-state`) — fires on 3 real bugs in older reels
- [x] `reels bench run --topics sci-rainbow --yes` — 1st try hit the account usage limit (now recorded as infra-error); 2nd try with `--model sonnet`: 28.5 s reel, 0 check errors, composite 76.8 (scored via `bench rescore` after a sheet-grouping crash, fixed)
- [x] `reels bench report` shows it
- [x] `reels evolve --dry-run`, then one real round — accepted (pairwise 11–1 train, 8–4 holdout), paused once by quota and resumed; not applied (human gate)
- [ ] `reels make "…" --yes` headless reel completes

## D. Other models (optional for v0.1, but state the result in the README)
- [ ] one reel or bench topic with a non-Claude harness (OpenCode + DeepSeek/Qwen, or Codex)
- [ ] judge on a non-Anthropic provider (e.g. `qwen:qwen-vl-max` or `gemini:…`)

## E. Publish
- [x] repository URLs point at github.com/agentic-loops-x/Reels-RSI
- [ ] README "Status" table updated with what B–D proved
- [ ] demo video (the Yuan reel) uploaded somewhere linkable; GIF/thumbnail in README
- [ ] tag v0.1.0, optional PyPI publish (`uv build && uv publish`)
