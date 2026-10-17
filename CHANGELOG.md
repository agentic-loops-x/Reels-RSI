# Changelog

## Unreleased — release testing

- 2026-10-13 · Speed and papers. `reels make --output video|web|both`: `web` delivers `renders/web/`, a static
  page with the HyperFrames player (`reels web <project> [--serve --open]`, 0.1 s instead of a render).
  `--rsi off` / `--rounds N` / `--fast`: make a reel without the memory (no lessons, no score loop, no retro,
  one finalize round; `REELS_RSI=off` silences `lessons digest`). `reels paper <src> --project .` and
  `reels make --paper <src>`: a paper or document (arXiv id/URL, PDF, PDF URL, .md/.txt/.html) becomes
  `paper/SOURCE.md` (metadata, abstract, ordered section outline, figure/table captions, sentences with
  numbers), `paper/fulltext.txt`, `assets/paper/` (raster figures, page renders for vector figures) and a
  CREDITS line; new recipe `references/paper.md`; the skill routes 论文/文档 requests to it and knows fast
  mode and web delivery. The `make` prompt is assembled from blocks (`agents.prompt_blocks`).
- 2026-10-13 · Voice: Microsoft's legacy edge-tts host answers 403 since October 2026 (the first paper demo
  died on it); `reels voice` now synthesizes through `api.msedgeservices.com` (edge-tts PR #491, the host
  Edge itself uses; `REELS_EDGE_ENDPOINT=legacy` to undo) and, with `--provider auto`, falls back to macOS
  `say` (`--provider say` to choose it) with word timings estimated from the character/word count, so a
  headless run never dies on TTS. `reels doctor` checks poppler.
- 2026-10-13 · `reels make --audience beginner|intermediate|expert` (小白 · 有基础 · 专业人士; aliases accepted): one
  line in the prompt and a full contract table in `references/paper.md` (coverage, terms, equations, numbers,
  analogy, visuals, pace, default length per level) plus a pre-render checklist for paper reels (main figure as a
  plate, both numbers on every result frame, label sizes, moving mechanisms, claim → source table).

- Paper: *Reels-RSI: Program-Level Self-Improvement for Code-Rendered Explainer Videos* ([paper/](paper/README.md), v7) — arXiv bundle (`paper/arxiv/build.sh`, verified with pdflatex), `CITATION.cff`, paper section in both READMEs; the README's evolve row now states the position-bias correction and round 2.
- The benchmark design (RRBench) moved to its own project, [ExplainReel-Bench](https://github.com/agentic-loops-x/ExplainReel-Bench) — a referee must not share code with a player. `reels bench` stays as Reels-RSI's internal benchmark for `evolve`.
- Renamed TakeLoop → EvoFilm → Reels-RSI (package `reels-rsi`, command `reels`, skill `/reels`, state in `~/.reels`; an existing `~/.evofilm` and per-reel `.evofilm/` are moved automatically).
- From two from-scratch reels (相遇问题, a textbook 燕尾模型 problem from a photo): 13 tool fixes —
  TTS retries, look-dev placeholders, project guard, non-fatal rules, rule false positive fixed,
  chalk caption contrast, caption band per canvas, packets list the shared kit + approved frames,
  caption-free `cover --frame`, canvas-generic frame-worker guide.
- New rule `visible-from-state` (compiled from a lesson) — found 3 latent bugs in two earlier reels.
- `chalk` preset ships `assets/chalk-kit.js` (board, strokes, coords/meet/foot, regions, labels with halo).
- Solve mode: problem-from-a-photo flow.
- Round 3 (models online): nested agent CLIs no longer inherit the host Claude Code session (false
  "OAuth session expired"); `doctor` checks the standalone `claude` login; judge sheets sized per aspect
  (portrait frames were ~200 px), canvas + caption band in the judge prompt, solve-mode R3; retro prompt
  weighs evidence and refuses judge-sampling lessons; bench records quota/login failures as unscored and
  evolve refuses incomplete runs; readable SRT cues; `config set` keeps `[providers.*]`; agents get
  `reels` on PATH; README code-structure sections.
- Round 4: first headless benchmark reel (sonnet, 28.5 s, composite 76.8); bench writes its summary as it
  goes, survives scoring crashes, `bench rescore`; lessons take `when` conditions (preset / aspect /
  mode) and packets get only the lessons that apply to the reel; `lessons digest --project`.
- Round 5: evolve judged by blind pairwise votes with side-by-side images; bench/evolve resume after
  quota stops; the skill now actually ships in the wheel (a symlink dropped it); first real evolve round
  (11–1 train, 8–4 holdout); `ChalkKit.board` sized to the canvas (found by the evolve proposer).

- Reels in Japanese, Korean, Spanish and French (`langs.py`; fonts download on first use) and
  `reels dub`: one reel into another language — narration, captions and on-screen text, each line voiced
  to the original timing. Rules now lint a code view of each frame (code shown on screen as content no
  longer trips them). A launch reel made with Reels-RSI heads the README.

## 0.1.0 — 2026-10-05

First public release.
- Reel pipeline as one CLI: new · voice · packets · finalize · render · cover · srt · concat · fonts ·
  captions · music · sfx · geo · commons · hanzi · image · analyze · times · hf
- Presets: deepspace · notebook · ink · atlas · chalk (new: blackboard for worked problems)
- Modes: science, history (maps, timeline overlay, Commons), solve (KaTeX, stroke order, verified answers)
- Self-improvement: run log + code history per pass, 12 rules with examples, retro → lessons →
  digest, score (deterministic + vision judge), compare, bench (8 topics), evolve (gated)
- Models: harnesses claude/codex/gemini/opencode; judge/retro on 12 provider presets + custom
- 2026-10-14 · Depth. Paper reels are built on the eight reviewer questions (problem · prior work · key idea · how ·
  why · evidence · limits · so what) at every audience level; the core-idea block (idea → worked example on one
  stage → formal → why) must be ≥ 45 % (expert) / 40 % of the reel; every storyboard frame carries `- beat:` and
  `reels paper check --project .` fails the storyboard otherwise. Default paper lengths 90 / 150 / 210 s. arXiv
  metadata falls back to the abs page when the API rate-limits (429); running page headers are no longer sections;
  `Figure N |` captions are recognised.
- 2026-10-14 · A figure is matched to its caption's page or the next one, never the page before — the first
  raster image of a paper is usually the title-page logo (the expert Dream-RSI reel showed a Google logo as
  "Figure 1"); title-page images are now listed as "probably a logo", not as figures.
- 2026-10-14 · "Why is the expert reel harder to follow than the beginner one?" The levels now nest instead of
  replacing each other: the expert reel carries the intermediate explanation (the idea in words anchored to the
  nearest concept the field knows, the walkthrough of one central mechanism on one stage) and adds a precision
  layer on top. Notation goes on screen, never into the voice (`reels paper check` fails a script that reads
  isolated letters / Greek aloud: > 0.6 per 100 characters or ≥ 4 in a frame); every `example` frame is
  purpose → action → what we see; ≤ 2 new quantities and ~12 s per core frame (warned); secondary mechanisms
  are named with their purpose only; expert narration back to the default rate; default expert length 270 s.
