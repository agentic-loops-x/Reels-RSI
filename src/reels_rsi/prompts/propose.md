You are improving the Reels-RSI skill — the instructions an AI agent follows to direct
code-rendered explainer films. A benchmark of films was just made with the current skill, and
scored. Your job: edit the skill so the next benchmark scores higher.

Skill to edit (a copy — edit freely): {{candidate}}
Benchmark results, judge notes and check findings for the current skill:

{{baseline}}

Lessons waiting in the inbox (proposed after past films, not yet accepted):

{{inbox}}

Make at most {{max_edits}} focused edits to {{candidate}}/SKILL.md or {{candidate}}/references/*.md:
- Target the weaknesses that recur across topics (low R-scores, repeated findings), not one-off flukes.
- Prefer concrete, checkable instructions (numbers, recipes, examples) over exhortations.
- Do not lengthen the skill by more than ~60 lines in total; delete what is obsolete.
- Do not change command names, file contracts or scripts.
- Write for what a viewer sees, never for how the judge samples: "the 30/60/92 % stills must differ" is
  teaching to the test; "keep the picture changing until the narration ends" is the instruction.
- If the evidence points at a defect in Reels-RSI's code, a preset or a kit (something an instruction can
  only work around), still add the workaround if it helps, and ALSO describe the defect in
  {{candidate}}/TOOL-BUGS.md (file, what breaks, how to reproduce) so a developer fixes the cause.

Then write {{candidate}}/CHANGES.md: one bullet per edit — what changed, which evidence motivated it,
and which R-score or finding it should move. Reply with the bullets.
