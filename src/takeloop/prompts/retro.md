You improve TakeLoop, an AI film director, by learning from one finished film. Below is the
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
- Skip anything listed under "Already known".

Return JSON: {"lessons": [{"kind": "...", "scope": "...", "text": "...", "evidence": "pass/diff/feedback it comes from"}]}

---

{{evidence}}
