You are directing a film with TakeLoop, headless. Nobody will answer questions: review gates are OFF
(直接做) — take every default the skill recommends, state them once, and keep going.

1. Read the skill: {{skill}}/SKILL.md (and the references it tells you to read).
2. Make this film:

   {{topic}}

   - target length: about {{length}} seconds
   - aspect: {{aspect}}
   - style preset: {{style}}
   - project directory: {{dir}}   (create it with `takeloop new {{dir}} …`)
3. Run every TakeLoop step with the `takeloop` command on PATH. If your harness cannot spawn
   sub-agents, build the frames yourself one by one from the packets.
4. Finish with `takeloop render {{dir}} --quality {{quality}}`, then
   `takeloop retro {{dir}} --evidence-only` and file at most 3 lessons with `takeloop lessons add`
   (only things a future film would get wrong too — not facts about this topic).
5. Reply with: the video path, its duration, and one line on what you would improve.
