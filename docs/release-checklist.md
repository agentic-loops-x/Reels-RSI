# Release checklist (manual verification before going public)

Tick every box on a clean setup before the first public push. ✅ = already verified during development.

## A. Install from scratch
- [ ] On a machine/user without ~/.takeloop: `uv tool install git+<repo>` (or `uv tool install -e .` from a clone)
- [ ] `takeloop setup` downloads fonts from Google Fonts (dev run copied them locally — the download path is unverified)
- [ ] `takeloop install` → skill appears in Claude Code (`/takeloop` shows up)
- [ ] `takeloop doctor` all green
- [ ] CI passes on GitHub (Linux) — never run yet

## B. One film per mode, made from zero inside an agent (`/takeloop …`)
| Film | Checks |
|---|---|
| [ ] 科普 60 s, 16:9, deepspace | plan gate → look-dev gate → finalize clean → render → cover → SRT |
| [ ] 历史 60 s, ink or atlas, with a map + Commons image | maps correct, timeline overlay, CREDITS.md |
| [ ] 解题 45 s, 9:16, chalk (e.g. 鸡兔同笼) | answer verified in BRIEF, KaTeX, check step on screen |
| [ ] English 30 s | English voice, word-gapped captions |
| [ ] bilingual 中英 | `**EN:**` lines, zh-en SRT |

For each: `takeloop voice` (real TTS run), `packets`, `finalize`, `render`, `cover` all via TakeLoop
(✅ finalize/new/fonts/hanzi verified; voice, packets, render, cover not yet run through TakeLoop).

## C. Self-improvement loop
- [ ] Log in the standalone CLI (`claude` → /login) or set an API key; `takeloop config show` ok
- [ ] `takeloop score <film>` returns judge scores that match your own eye (check 2–3 frames)
- [ ] `takeloop feedback` + `takeloop retro <film>` proposes sensible lessons (✅ evidence-only verified)
- [ ] accept one doc lesson → it appears in the next film's `.takeloop/packets/_role.md`
- [ ] write one new rule with `takeloop rules new`, accept it, see it fire in `finalize`
- [ ] `takeloop bench run --topics sci-rainbow --yes` (one topic) completes and scores
- [ ] `takeloop bench report` shows it
- [ ] `takeloop evolve --dry-run`, then one real round when budget allows (≈ 16 short films)
- [ ] `takeloop make "…" --yes` headless film completes

## D. Other models (optional for v0.1, but state the result in the README)
- [ ] one film or bench topic with a non-Claude harness (OpenCode + DeepSeek/Qwen, or Codex)
- [ ] judge on a non-Anthropic provider (e.g. `qwen:qwen-vl-max` or `gemini:…`)

## E. Publish
- [ ] replace `OWNER` in README.md, README.zh-CN.md, install.sh, pyproject.toml URL
- [ ] README "Status" table updated with what B–D proved
- [ ] demo video (the Yuan film) uploaded somewhere linkable; GIF/thumbnail in README
- [ ] tag v0.1.0, optional PyPI publish (`uv build && uv publish`)
