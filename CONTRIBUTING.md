# Contributing

The most valuable contributions are **rules** and **bench results**.

- **A rule** — a mistake you saw an agent make that can be detected in a frame's HTML/JS:
  `evofilm rules new <id>`, write `rule.py`, `bad.html`, `good.html`, run `evofilm rules test <id>`,
  then copy the folder to `src/evofilm/rsi/rules/<id>/` and open a PR. Make sure it stays quiet on
  real films (`evofilm lint --project <your film>`).
- **Lessons** — `evofilm lessons export out/` and propose the doc lessons as edits to the skill
  references they belong to.
- **Bench results** — `evofilm bench run --split all --yes` with your harness/model, attach
  `evofilm bench report --md` output to an issue.

Dev setup: `uv venv && uv pip install -e ".[dev]" && pytest`. Keep the CLI stdlib-only beyond the
listed dependencies, and keep the deterministic pipeline model-free.
