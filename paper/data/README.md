# Data behind the paper

| file | what |
|---|---|
| `fact-coverage.md` | the 8 topics' baseline vs evolved scripts, facts dropped/added, read by hand |
| `judge-reliability.json` | 3× absolute re-scores of the 16 evolve-round reels (sonnet); pairwise votes: sonnet ×3 repeats, haiku, opus — per vote pick, order and reason |
| `ablation-2x2.json` | rules {on,off} × lessons {on,off} on the 4 train topics: violations in the final output (all 13 rules run offline), passes, renderer findings, cost, judge |
| `ablation-pairwise.json` | position-balanced pairwise votes between ablation conditions (4 votes/topic) |
| `director-haiku.json` | the 4 train topics under claude-cli:haiku, rules on and off: firings, violations left, renderer errors |
| `*.py` | the scripts that produced and summarised them (paths assume the authors' machine; adjust `RUNS`/`HOMES`) |

Reels (videos, frame code, run logs) are not in the repository; the evolve report and side-by-side
images are in `~/.reels/evolve/20261006-001942/` on the authors' machine and summarised in `docs/rsi.md`.
| `learning-curve.json`, `learning-curve-topics.txt`, `run_curve.sh`, `curve_analysis.py` | 24 new topics made twice (lessons auto-accepted vs none): passes, renderer findings at first and last pass, rule firings |
| `learning-curve-lessons/` | the 51 lessons the auto-accept arm had accumulated after reel 24 (as filed by the agents; not curated) |
