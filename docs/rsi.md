# Self-improvement in TakeLoop

"Recursive self-improvement" in 2026 practice means an agent improving its own prompts, skills,
memory and tools — not its weights. TakeLoop applies that to one craft, making films, and keeps it
**measurable** (every change is scored) and **gated** (you approve what sticks).

## Why video is a good fit

Making a film is already a loop: draft → look → find problems → fix. A director model makes the
same classes of mistakes across films (an origin that drifts, a border drawn the wrong way round,
text under the captions). Each fix is cheap to observe — the checks log it and the code diff shows it —
so the loop has a natural training signal without any labelling.

## The four layers

### L0 — in-film review
`takeloop finalize` runs HyperFrames' check (lint, runtime errors, layout overlap, contrast) and every
TakeLoop rule, then logs the pass to `<project>/.takeloop/runs.jsonl` and snapshots the code to
`.takeloop/history/NNN/`. `takeloop score` adds a deterministic score (render ok, errors, warnings,
duration vs target, shot length) and, when a judge model is configured, a vision judge that scores
every frame on the quality bar's R1–R6 from 30/60/92 % samples. `composite = 0.6·judge + 0.4·deterministic`.

### L1 — cross-film memory
`takeloop retro <project>` builds `evidence.md`:
- issues per pass, marked NEW / FIXED;
- **the diff between the pass that had an issue and the pass that fixed it**, so every lesson has its cause next to it;
- your feedback (`takeloop feedback`) and the judge's notes;
- everything already known, so nothing is proposed twice.

A retro model (any `provider:model`) — or the directing agent itself — proposes ≤ 5 general lessons
into `~/.takeloop/lessons/inbox/`. You accept or reject (`takeloop lessons`). Accepted lessons are
injected into `takeloop packets` (every frame worker reads them) and `takeloop lessons digest`
(the director reads them at Step 0). Taste lessons ("字幕再大一点") build a personal profile and are
never exported.

### L2 — lessons become rules
A rule is a folder: `rule.py` (a `check(doc)` over the frame's HTML/JS text) + `bad.*` (must fire) +
`good.*` (must not). `takeloop rules test` proves every rule; `takeloop lessons accept --rule-dir`
refuses a rule that fails its own examples. Rules run on every finalize, so a lesson stops depending
on the model remembering it — the most model-independent form of improvement.

The 12 built-in rules each come from a real mistake while building the first films:
dasharray-attr · svgorigin-one-sided · negative-zindex · nondeterminism · repeat-fromto ·
chained-no-position · round-cap-mask · polygon-winding · cjk-font · caption-band ·
timeline-registration · unpinned-cdn.

### L3 — the skill evolves itself
`takeloop bench run` makes the 8 fixed topics (science, history, solve, English; train/holdout) with a
given harness, model and skill directory, then scores them. `takeloop evolve`:

1. baseline = current skill on the train topics
2. an agent reads the baseline's judge notes and findings plus the lesson inbox and makes ≤ 3 edits
   to a **copy** of the skill, explaining each in `CHANGES.md`
3. the copy makes the same train films; it must beat the baseline mean by a margin, lose no topic by
   more than 10 points, and render at least as many films
4. both versions make the holdout films; the candidate must not be worse there
5. `report.md` + `skill.patch`; nothing changes until `takeloop evolve apply <id>`

## Safeguards

| Risk | Guard |
|---|---|
| judge-pleasing ("reward hacking") | holdout topics the proposer never sees · deterministic score is 40 % · blind A/B (`takeloop compare`) · human apply |
| skill bloat / drift | ≤ 3 edits per round, ≤ ~60 lines, CHANGES.md with evidence, patch reviewed before apply |
| noisy single runs | margin + per-topic regression limit; re-run the bench before applying big changes |
| cost | bench defaults to 30 s films and draft quality; `--dry-run` everywhere; `--yes` required |
| unsafe agent actions | headless sessions run with full tool permissions — run bench/evolve in a container or a throwaway user |

## Community self-improvement

`takeloop lessons export <dir>` bundles your accepted doc lessons and rules (taste and local paths
removed) for a pull request. Upstream rules then protect every user and every model.
