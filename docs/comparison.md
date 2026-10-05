# EvoFilm and other tools (as of October 2026)

Code-rendered video with LLM agents is a busy space. What EvoFilm adds, to the best of our knowledge:

| | EvoFilm | HyperFrames (HeyGen) | OpenMontage | Vox-Director | Story-to-Handdrawn-Video | MathLens / Manim skills |
|---|---|---|---|---|---|---|
| Scope | narrated explainers: science, history, school problems | general HTML→video framework + workflows | broad production system, many pipelines | one paper-collage style | Chinese stories → hand-drawn, silent | math explanations |
| Self-improvement loop (rules, lessons, bench, evolve) | **yes** | no | no | no | no | no |
| Model choice | any harness + any `provider:model` for judge/retro | agent of your choice | — | Claude | Claude | varies |
| Chinese narration with word-timed captions | **yes** | English-first | partial | yes | no voice | yes |
| History mode (maps + accuracy rules, timeline overlay, credited archives) | **yes** | no | — | no | no | no |
| School problem mode (KaTeX, stroke order, verified answers) | **yes** | no | — | no | no | math only |
| Free by default | yes | yes | — | — | — | yes |

EvoFilm builds on HyperFrames (rendering, check, vendored workflow scripts) rather than competing
with it. If you need product launches, beat-synced music videos or talking-head overlays, use the
HyperFrames workflows directly — EvoFilm's fonts/captions commands work there too.

"—" = not verified by us. Corrections welcome.
