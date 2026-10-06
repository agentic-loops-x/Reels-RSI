# RRBench — a benchmark for agents that make explainer reels

**Status: design (v0.1 draft).** The current `reels bench` (8 topics, one judge score) is the seed;
this document is what it grows into. 中文版：[benchmark.zh-CN.md](benchmark.zh-CN.md).

RRBench asks one question: **given a topic or a problem, can an AI system produce a short reel that
is correct, actually teaches, and is well made — and does the system get better with experience?**

## 1. Why another benchmark

| Benchmark | Measures | Gap for explainer reels |
|---|---|---|
| [VBench / VBench-2.0](https://vchitect.github.io/VBench-2.0-project/) | pixel realism; physics and commonsense faithfulness of generated clips (5 categories, 18 dimensions) | a beautiful clip can teach the wrong thing; no narration, no correctness of an argument |
| [TheoremExplainBench](https://tiger-ai-lab.github.io/TheoremExplainAgent/) | 240 theorems, Manim videos, 5 LLM-judged dimensions (accuracy & depth, visual relevance, logical flow, element layout, visual consistency) | judged only by a model; nothing is verified by execution |
| [Code2Video / MMMC](https://github.com/showlab/Code2Video) | 456 3Blue1Brown-style topics; **TeachQuiz** — does a model that has "unlearned" a concept recover it by watching? | strong idea; single pipeline style, English, no outcome tests |
| [Paper2Video](https://showlab.github.io/Paper2Video/) | paper → talk video; **PresentArena** (pairwise vs human talks), **PresentQuiz** | slides + talking head, not explainer animation |
| [Teaching Monster Challenge](https://arxiv.org/html/2608.08852) | lesson videos for a learner persona; LLM-judge → crowd Elo arena → expert panel | finding that matters: the LLM judge screened weak entries but **ranked the top systems at ρ = −0.17 against the crowd**; about 1 video in 6 still had a critical factual error |
| [Terminal-Bench](https://www.tbench.ai/) | agents in Docker; instruction + environment + **tests on the final state** + reference solution + time limit; harness-agnostic (Harbor), audited trajectories | the evaluation style we want, for a different task |
| [SWE-bench Verified](https://www.swebench.com/) / [DeepSWE](https://www.together.ai/blog/deepswe) | resolved rate by execution; Pass@1 vs verifier-selected best-of-n (DeepSWE: 42.2 % → 59 % with 16 rollouts and hybrid verifiers); training environments (R2E-Gym) kept apart from the test set | the reporting discipline we want |

Nobody verifies explainer reels by execution, and nobody measures whether a reel-making system
improves with experience. RRBench does both.

## 2. Principles (and where each comes from)

1. **Outcome tests on the final artifact** (Terminal-Bench). A task passes only if checks on the
   rendered MP4 pass: it renders, the answer is right and visible, the required facts are said, no
   known misconception appears. The checks never look at how the agent got there.
2. **System-agnostic contract.** Input: a task instruction (+ optional image or reference video).
   Output: `/output/video.mp4` (+ optional `subtitles.srt`, `project/`). Any agent harness, any
   pipeline — even a pixel video model — can enter. Reels-RSI is one entrant, not the referee.
3. **Learning is measured, not assumed** (TeachQuiz, PresentQuiz). Hidden quizzes per task, answered
   by a student model that sees only the reel.
4. **Pairwise, panel and human-checked craft judgments** (Teaching Monster, PresentArena, Chatbot
   Arena). Absolute 1–5 scores saturate at the top; blind pairwise votes with the order swapped,
   from judges of several model families, become an Elo with bootstrap intervals, and a human-rated
   slice reports judge–human agreement every release.
5. **Decomposed diagnostics, validated against people** (VBench). Rubric dimensions explain *why*
   a system wins; they are reported, never summed into the headline.
6. **Train ≠ test; report Pass@1 and the TTS track separately** (SWE-bench, DeepSWE). Self-improving
   systems learn on a train pool and are measured on tasks they never saw.
7. **A self-improvement track.** The first benchmark to score the *slope*: how much a system gains
   from its own past reels.
8. **Every test is tested.** Each task ships an oracle reel that passes and mutant reels that must
   fail (the same "bad / good example" discipline as Reels-RSI rules).

## 3. A task

```
tasks/solve-chicken-rabbit/
├── task.toml            instruction, genre, language, aspect, length window, audience, inputs
├── facts.toml           verified facts: the answer, required claims, forbidden misconceptions, sources
├── tests/               outcome checks on /output (pytest)
│   └── test_outcome.py
├── quiz.jsonl           hidden — 5–8 multiple-choice questions for the student model
├── oracle/              a reel that passes every test (proves the task is solvable and the tests sound)
├── mutants/             reels that must fail: wrong answer, answer never shown, misconception said, 40 % over length
└── reference.mp4        optional — a strong human or best-known reel, the arena anchor
```

`task.toml`:

```toml
id = "solve-chicken-rabbit"
genre = "solve"                     # solve · science · history · language · story
language = "zh"                     # zh · en · zh-en
aspect = "9:16"
length = [45, 75]                   # seconds; outside → gate fails
audience = "小学五年级，会乘除法，没学过方程"
difficulty = "medium"
inputs = []                         # e.g. ["problem.jpg"] for photo tasks, ["style.mp4"] for "make it look like this"
time_limit_min = 60
instruction = """
做一个讲解视频：鸡兔同笼，共有 35 个头、94 只脚。鸡和兔各有几只？
用画图或假设法讲给五年级学生听，不用方程。结尾要验算。
"""
```

`facts.toml`:

```toml
sources = ["人教版五年级上册·数学广角"]

[answer]
chickens = 23
rabbits = 12

[required]            # each must be spoken (ASR, Chinese numerals normalized) or shown (OCR / VLM)
assume_all_chickens = '70'                              # 35 × 2
feet_gap = '24'                                         # 94 − 70
per_swap = '(24.{0,8}(除以|÷|/)\s*2)|((多|补)(两|2)只)'
check = '(代回去|验算|检查|核对).{0,20}94'

[forbidden]           # known misconceptions or off-audience methods — any hit fails the gate
equation = '(设\s*[xX])|(方程)'
```

The tests read the reel, not the project: `ffprobe` (duration, audio stream, resolution), ASR
(word timestamps), OCR / a VLM on sampled frames (is "23" and "12" on screen in the last 25 %?),
caption-band and clipping checks on the frames, and the `facts.toml` matchers. Ambiguous matches go to
an LLM matcher with the exact facts — a yes/no with quoted evidence, logged.

## 4. The suite

v1 target: **240 tasks** — 120 test, 60 train (for self-improving systems), 60 private holdout
refreshed every release (contamination guard).

| Family | Share | What makes it hard | Verifiable core |
|---|---|---|---|
| Solve — math, physics, chemistry (小学 → 高中) | 35 % | multi-step reasoning, geometry figures, 9:16 boards | the answer, the steps, the check |
| Solve from a photo | 10 % | read a real textbook photo; build the figure from given lengths, not pixels | transcription + answer |
| Science mechanisms | 20 % | show cause → effect, not labels; 3D, simulation | required causal claims, no misconceptions |
| History & geography | 15 % | maps, dates, sequence, period-correct geography | dates, order of events, places on the map |
| Language & literature (古诗, stroke order, English) | 10 % | mood and accuracy together | text fidelity, stroke order, pronunciation |
| Style transfer ("make it look like this") | 5 % | match pacing/palette of a reference without copying | measured shot length, palette distance |
| Long form (3–5 min, chapters) | 5 % | coherence over many frames | chapter structure, cross-references |

Every family is spread over languages (zh 50 %, en 30 %, zh-en 20 %), aspects (16:9, 9:16) and three
difficulty tiers (30 s single idea · 60–90 s multi-step · photo / bilingual / long).

## 5. Scoring

### Layer 1 — Gates → **Resolved %** (the headline)
A reel resolves the task when every test passes: renders · length window · audio present ·
answer correct and visible · required facts present · no forbidden claim · nothing clipped or in the
caption band · no blank or frozen stretch > 3 s. Reported as **Pass@1** (one attempt), plus Pass@k.

### Layer 2 — ReelQuiz → **Learning gain**
A fixed student model answers the hidden quiz twice: without the reel, then with only the reel
(frames + audio transcript). Gain = accuracy(with) − accuracy(without), averaged over tasks.
Strong models already know K-12 answers, so (a) the student is deliberately small and frozen per
release, (b) questions favour *this reel's* method and steps ("which auxiliary line was drawn?",
"what did the reel assume first?") and transfer variants with new numbers, and (c) the no-reel
baseline is published so a saturated quiz is visible.

### Layer 3 — Arena → **Craft Elo**
For each task, reels from different systems (and the reference) are compared blind in pairs by a
panel of vision judges from ≥ 2 model families; each pair is judged twice with the order swapped.
Bradley–Terry Elo with 90 % bootstrap intervals. Each release, ~10 % of pairs go to human raters
(teachers for solve, general viewers for science and history); the leaderboard prints judge–human
agreement and flags the column if it falls below τ = 0.4.

### Layer 4 — Diagnostics (reported, not ranked)
Six rubric dimensions per reel (hero richness, mechanism shown, camera & eye guidance, pacing,
composition, consistency), plus TheoremExplainBench-style accuracy/depth and logical flow;
deterministic signals (lint findings, A/V sync error, caption-band violations); **cost**: wall time,
tokens, dollars, finalize passes.

### Leaderboard

| system (harness + model) | Resolved@1 | Pass@3 | Learning gain | Craft Elo (90 % CI) | $ / reel | min / reel |
|---|---|---|---|---|---|---|

A separate **TTS track** allows n attempts with the system's own verifier choosing one reel
(DeepSWE-style); it is never mixed with Pass@1.

## 6. The self-improvement track (RSI)

The question no video benchmark asks: *does the system get better by itself?*

1. **Before**: the system makes the 60-task eval slice with an empty memory → Resolved₀, Elo₀.
2. **Experience**: it works through the 60 train tasks in a fixed order, keeping whatever it learns
   (lessons, rules, skill edits, fine-tunes — its choice). It may see its own test results and judge
   notes for *train* tasks only. Human gates are disabled or logged as interventions.
3. **After**: the same eval slice again → Resolved₁, Elo₁ (old vs new reels judged head to head).
4. **Ablation**: the same run with learning switched off controls for run-to-run noise.
5. **Retention**: re-run 10 early train tasks at the end — gains must not be bought by forgetting.

Reported: **ΔResolved**, **ΔElo** (with intervals), cost of the experience phase, number of human
interventions, and the learning curve over the 60 train tasks.

## 7. Integrity

- **Validated tasks**: the oracle passes, every mutant fails, two reviewers sign off facts and
  sources; a task whose tests a reviewer can beat with a wrong reel is fixed or dropped.
- **Contamination**: quizzes, mutants and the private holdout never leave the evaluation server;
  canary strings in public task files; the holdout is replaced every release.
- **Anti-gaming**: tests read the final MP4 only; judges never see system names; judge models rotate
  per release; tasks forbid writing to `/tests`.
- **Reproducibility**: pinned Docker images (Chrome, FFmpeg, fonts, Node), cached TTS, seeds; every
  run publishes its trajectory and project folder, as Terminal-Bench does.
- **Safety**: agents run in disposable containers with network limited to declared services (TTS,
  model APIs, Wikimedia, Natural Earth).

## 8. From today's `reels bench` to RRBench

| Today | RRBench |
|---|---|
| 8 topics in `topics.toml` | 240 task folders (§3) |
| composite = 0.6 judge + 0.4 lint | gates → Resolved; quiz → gain; arena → Elo; rubric = diagnostics |
| one judge model | judge panel + human slice + agreement |
| `evolve` uses train/holdout | the RSI track (§6), open to any system |
| Reels-RSI only | any harness or pipeline via the output contract |

Roadmap: **v0.1** convert the 8 topics, write gates + quiz for the 4 solve/science ones, run on
Reels-RSI with two models · **v0.2** 60 tasks, judge panel, first human slice · **v1.0** 240 tasks,
public leaderboard, RSI track, external submissions.

## 9. Open questions

- Learning gain with a small student vs a human pilot study (Code2Video found aesthetics and learning
  correlate at r = 0.97 — worth re-testing on Chinese K-12).
- TTS: the free Edge voice is an unofficial endpoint; the harness needs a licensed or local fallback.
- Weighting families: should the headline be per-family macro-average so solve tasks don't dominate?

## 10. A worked example — and what it already taught

[`benchmark/example-task/`](benchmark/example-task/) is a complete task (鸡兔同笼, 16:9, 30 s):
`task.toml`, `facts.toml`, a hidden-style `quiz.jsonl`, 13 outcome tests and `make_mutants.py`.
Run against the two reels the first evolve round made for this topic:

| reel | gates passed | resolved |
|---|---|---|
| baseline skill | 12 / 13 — the last quarter never states 兔 12 on screen (only inside `23×2+12×4`) | ✗ |
| evolved skill | 13 / 13 — ends on "鸡 23 兔 12" and the check | ✓ |
| mutant: wrong answer said | caught by 3 tests | ✗ |
| mutant: sets up an equation | caught (`forbidden.equation`) | ✗ |
| mutant: last 40 % frozen, answer never shown | caught by 2 tests | ✗ |
| mutant: 2× too long | caught (`length_window`) | ✗ |

Building it changed the design in three places:

1. **Model-assisted gates transcribe; code decides.** Asked "is the answer visible?", the vision
   model said yes, then no, on the same borderline frame. Asked to transcribe the on-screen text, it
   was stable — and the decision became a rule anyone can audit against the quoted text.
2. **Mutants find holes in the tests.** The first freeze check let "last 40 % frozen" through (FFmpeg
   reports no duration for a freeze that runs to the end), and the wrong-count pattern missed
   "兔就是十三只". Both were found only because the mutant had to fail.
3. **Gates and the arena agreed here** — the reel the pairwise judge preferred is also the only one
   that resolves — but they measure different things, which is why both are reported.
