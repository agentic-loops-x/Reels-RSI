# Reels-RSI: Program-Level Self-Improvement for Code-Rendered Explainer Videos

**Agentic Loops X** · preprint, October 2026 · [PDF (v7)](versions/v7/main.pdf) · arXiv: *submitted, identifier pending* ·
code, rules and lessons: the repository you are in.

## Abstract

Explainer videos — a worked geometry problem, why the sky is blue, how a dynasty fell — are usually one
more target for pixel video generation. We argue they are a different kind of artifact: a *program*
(script, storyboard and per-frame animation code) that a deterministic renderer turns into frames. A
program can be read, diffed, tested and audited; pixels can only be watched. Reels-RSI is an
open-source reel director for any agent harness; its self-improvement happens at the program level
rather than in weights or prompts. Every revision pass is logged with a code snapshot; a retrospective
pairs each check finding with the diff that fixed it and proposes lessons; a lesson that a static check
can catch is *compiled into a rule* with a must-fail and a must-pass example, so the memory is
unit-tested; and a rule learned today runs over everything made before it. A bounded, benchmark-gated
step lets an agent rewrite the director's playbook, kept only when blind pairwise judgments on held-out
topics prefer it; nothing enters memory without a human decision. Across 111 reels — a field study, two
playbook evolutions, a 2×2 memory ablation, a weaker director, a 48-reel learning curve and a
judge-reliability study — we find that the rule learned in the field caught four latent defects in
frames authored before it existed and none after; that rules are an audit for a strong director (eight
unguarded reels, no violation) and a guard for a weaker one (thirty violations unguarded versus five);
that lessons shorten revision loops but do not compound or move the judge; and that the first rewrite's
11–1 verdict was a position bias in our vote design (judges pick the second-shown reel 62–81 % of the
time), masking scripts that traded thirteen facts for craft. We document four failure modes of the
preference signal, which check caught each, and the fixes. Code, rules, lessons and data are public.

## The experiments at a glance

| Experiment (paper §) | Reels | What it shows |
|---|---|---|
| Release-testing field study + evolve round 1 (§5.1–5.6) | 23 + 16 | the retroactive audit finds 4 latent defects; the 11–1 pairwise verdict was position bias |
| Judge reliability (§5.9) | 170 judge calls, 3 models | absolute rubric stable (SD 1.3) but insensitive; second-shown reel picked 62–81 % |
| 2×2 memory ablation (§5.7) | 16 | a strong director leaves no violations with rules off; lessons are invisible to the judge |
| Weaker director (§5.7) | 8 | 30 violations unguarded vs 5 guarded |
| Learning curve, two arms (§5.8) | 48 | auto-accepted lessons cut passes (2.62 vs 3.21, p = 0.07) but neither compound nor move the judge |
| Evolve round 2 under the corrected gate (§5.6) | 16 | accepted by the gate (4–0 train from the disadvantaged slot, 2–2 holdout), left unapplied |

Metered cost of the 105 headless reels: $82.72. Judge, retro and proposer calls ran on a Claude
subscription through the Claude Code CLI.

## What is here

| path | contents |
|---|---|
| `main.tex`, `refs.bib`, `figures/` | the paper's source (compile with `tectonic main.tex`; arXiv compiles it with pdflatex) |
| `data/` | every number in the paper: judge-reliability votes, ablation and learning-curve rows, fact-coverage readings, the scripts that produced them ([data/README.md](data/README.md)) |
| `versions/` | one frozen copy per iteration (`v1` … `v7`), each with PDF, source, figures and data; [versions/INDEX.md](versions/INDEX.md) says what changed |
| `arxiv/` | `build.sh` makes the arXiv source bundle (adds `\pdfoutput=1`, bundles `main.bbl` and only the figures used) and `--verify` compiles it with pdflatex in a TeX Live container; [SUBMISSION.md](arxiv/SUBMISSION.md) holds the form metadata |

The reels themselves (videos, frame code, run logs) are not in the repository; the evolve reports and
side-by-side images are summarised in [docs/rsi.md](../docs/rsi.md).

## Cite

```bibtex
@misc{reelsrsi2026,
  title  = {Reels-RSI: Program-Level Self-Improvement for Code-Rendered Explainer Videos},
  author = {{Agentic Loops X}},
  year   = {2026},
  note   = {Preprint. Code and data: https://github.com/agentic-loops-x/Reels-RSI}
}
```

The arXiv identifier will be added here, in the root README and in `CITATION.cff` once the submission
is announced.
