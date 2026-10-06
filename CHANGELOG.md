# Changelog

## Unreleased — release testing

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

## 0.1.0 — 2026-10-05

First public release.
- Reel pipeline as one CLI: new · voice · packets · finalize · render · cover · srt · concat · fonts ·
  captions · music · sfx · geo · commons · hanzi · image · analyze · times · hf
- Presets: deepspace · notebook · ink · atlas · chalk (new: blackboard for worked problems)
- Modes: science, history (maps, timeline overlay, Commons), solve (KaTeX, stroke order, verified answers)
- Self-improvement: run log + code history per pass, 12 rules with examples, retro → lessons →
  digest, score (deterministic + vision judge), compare, bench (8 topics), evolve (gated)
- Models: harnesses claude/codex/gemini/opencode; judge/retro on 12 provider presets + custom
