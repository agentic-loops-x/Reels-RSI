# Self-improvement in EvoFilm

"Recursive self-improvement" in 2026 practice means an agent improving its own prompts, skills,
memory and tools — not its weights. EvoFilm applies that to one craft, making films, and keeps it
**measurable** (every change is scored) and **gated** (you approve what sticks).

## Why video is a good fit

Making a film is already a loop: draft → look → find problems → fix. A director model makes the
same classes of mistakes across films (an origin that drifts, a border drawn the wrong way round,
text under the captions). Each fix is cheap to observe — the checks log it and the code diff shows it —
so the loop has a natural training signal without any labelling.

## The four layers

### L0 — in-film review
`evofilm finalize` runs HyperFrames' check (lint, runtime errors, layout overlap, contrast) and every
EvoFilm rule, then logs the pass to `<project>/.evofilm/runs.jsonl` and snapshots the code to
`.evofilm/history/NNN/`. `evofilm score` adds a deterministic score (render ok, errors, warnings,
duration vs target, shot length) and, when a judge model is configured, a vision judge that scores
every frame on the quality bar's R1–R6 from 30/60/92 % samples. `composite = 0.6·judge + 0.4·deterministic`.

### L1 — cross-film memory
`evofilm retro <project>` builds `evidence.md`:
- issues per pass, marked NEW / FIXED;
- **the diff between the pass that had an issue and the pass that fixed it**, so every lesson has its cause next to it;
- your feedback (`evofilm feedback`) and the judge's notes;
- everything already known, so nothing is proposed twice.

A retro model (any `provider:model`) — or the directing agent itself — proposes ≤ 5 general lessons
into `~/.evofilm/lessons/inbox/`. You accept or reject (`evofilm lessons`). Accepted lessons are
injected into `evofilm packets` (every frame worker reads them) and `evofilm lessons digest`
(the director reads them at Step 0). Taste lessons ("字幕再大一点") build a personal profile and are
never exported.

A lesson can carry a `when` (`preset=chalk`, `aspect=9:16`, `mode=solve`): it then reaches only the
films it holds for. Without it, the first benchmark film — a 16:9 deep-space science film — was handed
"draw chalk boxes" and "use the lower half of a 9:16 canvas" (`evofilm lessons when <id> "<cond>"`).
The judge's and the retro model's words are evidence, not facts: in release testing a judge misread a
downscaled sheet as "wrong aspect" and the retro model turned that into a false lesson — the human gate
caught it, and the retro prompt now weighs check findings and viewer feedback above judge notes.

### L2 — lessons become rules
A rule is a folder: `rule.py` (a `check(doc)` over the frame's HTML/JS text) + `bad.*` (must fire) +
`good.*` (must not). `evofilm rules test` proves every rule; `evofilm lessons accept --rule-dir`
refuses a rule that fails its own examples. Rules run on every finalize, so a lesson stops depending
on the model remembering it — the most model-independent form of improvement.

The 12 built-in rules each come from a real mistake while building the first films:
dasharray-attr · svgorigin-one-sided · negative-zindex · nondeterminism · repeat-fromto ·
chained-no-position · round-cap-mask · polygon-winding · cjk-font · caption-band ·
timeline-registration · unpinned-cdn.

### L3 — the skill evolves itself
`evofilm bench run` makes the 8 fixed topics (science, history, solve, English; train/holdout) with a
given harness, model and skill directory, then scores them. `evofilm evolve`:

1. baseline = current skill on the train topics
2. an agent reads the baseline's judge notes and findings plus the lesson inbox and makes ≤ 3 edits
   to a **copy** of the skill, explaining each in `CHANGES.md`
3. the copy makes the same train topics. Per topic the judge sees **both films blind**, order swapped
   between 3 votes, and picks the better one (`evofilm compare`). The candidate must win most of the
   votes, render at least as many films and lose no topic by more than 10 composite points
4. both versions make the holdout topics; the candidate must win at least half the votes there
5. `report.md` (per topic: votes, the judge's reasons, a side-by-side image of both films) +
   `skill.patch`; nothing changes until `evofilm evolve apply <id>`

Why pairwise: the same skill making the same topic twice can differ by more than a few composite
points (the agent writes different code each time, and a 1–5 judge drifts). "Which of these two is
better?" with the order swapped is far steadier, and the position swap cancels the judge's bias for
the first or second image. A quota or login stop pauses a round instead of failing it:
`evofilm evolve --resume <id>`.

## Safeguards

| Risk | Guard |
|---|---|
| judge-pleasing ("reward hacking") | holdout topics the proposer never sees · deterministic score is 40 % · blind A/B (`evofilm compare`) · human apply |
| skill bloat / drift | ≤ 3 edits per round, ≤ ~60 lines, CHANGES.md with evidence, patch reviewed before apply |
| noisy single runs | blind pairwise votes instead of absolute score deltas · per-topic regression limit · the side-by-side images in the report for your own eye |
| cost | bench defaults to 30 s films and draft quality; `--dry-run` everywhere; `--yes` required |
| unsafe agent actions | headless sessions run with full tool permissions — run bench/evolve in a container or a throwaway user |

## Community self-improvement

`evofilm lessons export <dir>` bundles your accepted doc lessons and rules (taste and local paths
removed) for a pull request. Upstream rules then protect every user and every model.
