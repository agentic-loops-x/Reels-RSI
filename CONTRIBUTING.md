# Contributing

The most valuable contributions are **rules** and **bench results**.

- **A rule** — a mistake you saw an agent make that can be detected in a frame's HTML/JS:
  `reels rules new <id>`, write `rule.py`, `bad.html`, `good.html`, run `reels rules test <id>`,
  then copy the folder to `src/reels_rsi/rsi/rules/<id>/` and open a PR. Make sure it stays quiet on
  real reels (`reels lint --project <your reel>`).
- **Lessons** — `reels lessons export out/` and propose the doc lessons as edits to the skill
  references they belong to.
- **Bench results** — `reels bench run --split all --yes` with your harness/model, attach
  `reels bench report --md` output to an issue.

Dev setup: `uv venv && uv pip install -e ".[dev]" && pytest`. Keep the CLI stdlib-only beyond the
listed dependencies, and keep the deterministic pipeline model-free.
