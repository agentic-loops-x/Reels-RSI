# Changelog

## Unreleased — release testing

- Renamed TakeLoop → EvoFilm.
- From two from-scratch films (相遇问题, a textbook 燕尾模型 problem from a photo): 13 tool fixes —
  TTS retries, look-dev placeholders, project guard, non-fatal rules, rule false positive fixed,
  chalk caption contrast, caption band per canvas, packets list the shared kit + approved frames,
  caption-free `cover --frame`, canvas-generic frame-worker guide.
- New rule `visible-from-state` (compiled from a lesson) — found 3 latent bugs in two earlier films.
- `chalk` preset ships `assets/chalk-kit.js` (board, strokes, coords/meet/foot, regions, labels with halo).
- Solve mode: problem-from-a-photo flow.
- Round 3 (models online): nested agent CLIs no longer inherit the host Claude Code session (false
  "OAuth session expired"); `doctor` checks the standalone `claude` login; judge sheets sized per aspect
  (portrait frames were ~200 px), canvas + caption band in the judge prompt, solve-mode R3; retro prompt
  weighs evidence and refuses judge-sampling lessons; bench records quota/login failures as unscored and
  evolve refuses incomplete runs; readable SRT cues; `config set` keeps `[providers.*]`; agents get
  `evofilm` on PATH; README code-structure sections.

## 0.1.0 — 2026-10-05

First public release.
- Film pipeline as one CLI: new · voice · packets · finalize · render · cover · srt · concat · fonts ·
  captions · music · sfx · geo · commons · hanzi · image · analyze · times · hf
- Presets: deepspace · notebook · ink · atlas · chalk (new: blackboard for worked problems)
- Modes: science, history (maps, timeline overlay, Commons), solve (KaTeX, stroke order, verified answers)
- Self-improvement: run log + code history per pass, 12 rules with examples, retro → lessons →
  digest, score (deterministic + vision judge), compare, bench (8 topics), evolve (gated)
- Models: harnesses claude/codex/gemini/opencode; judge/retro on 12 provider presets + custom
