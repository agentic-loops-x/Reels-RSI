# Example RRBench task — 鸡兔同笼

A complete task in the format of [docs/benchmark.md](../../benchmark.md) §3.

```bash
RRB_OUTPUT=/path/to/output pytest docs/benchmark/example-task/tests -q      # output = video.mp4 (+ subtitles.srt)
python docs/benchmark/example-task/make_mutants.py <passing-output> <mutants-dir>   # every mutant must fail
```

In the real benchmark `quiz.jsonl`, the mutants and the oracle stay on the evaluation server; they are
public here only as an example. The on-screen answer check uses a vision model (`RRB_JUDGE`, default
`claude-cli:sonnet`) to transcribe the last frames; the pass/fail rule is in the test code.
