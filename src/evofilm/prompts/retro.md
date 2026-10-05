You improve EvoFilm, an AI film director, by learning from one finished film. Below is the
evidence: what the automatic checks caught on each pass and what got fixed, how the frame code
changed from first draft to final, what the viewer said, and the judge's notes.

Propose at most 5 lessons that would make the NEXT film (any topic) better or cheaper to make.

Rules for a good lesson:
- General, not about this topic. "Map labels must stay above y=900" yes; "the Yuan border is at 39°N" no.
- One or two sentences, imperative, with the reason ("…, because …").
- Prefer lessons backed by a FIXED issue or a viewer complaint — each one cost a review round.
- kind:
  - "rule" only if a mistake is detectable by reading the HTML/JS text (a regex/parse check would catch it);
  - "taste" only for the viewer's own preferences;
  - "kit" for a reusable component worth extracting;
  - otherwise "doc".
- scope: director (script, storyboard, pacing) · frame (building frames) · history · solve · script · style · all.
- Weigh the evidence: a FIXED check finding or the viewer's words are facts; the judge's notes are one
  model's opinion from small downscaled stills — its pixel sizes, proportions and "wrong aspect" claims are
  often mistaken. Never infer a render or tooling bug from a judge note alone, and say "judge:" in the
  evidence when a lesson rests only on it.
- Write about what the viewer sees, never about how the judge samples ("make the 30 % sample differ" is
  teaching to the test; "spread the build across the frame's narration" is the lesson).
- Skip anything listed under "Already known".

Return JSON: {"lessons": [{"kind": "...", "scope": "...", "text": "...", "evidence": "pass/diff/feedback it comes from"}]}

---

{{evidence}}
