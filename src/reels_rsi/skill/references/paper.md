# Paper mode — 论文 / 文档讲解 (a PDF, an arXiv link, a report)

Read for any "explain this paper / 讲讲这篇论文 / 把这个 PDF 做成视频" request. The goal is not a summary:
**a viewer at the chosen level must actually understand the work** — be able to say what problem it
solves, what the idea is, how it works, why it works, and how far the evidence goes. Every level
answers the same eight questions a reviewer asks; the level changes the depth and the language, never
which questions get answered. Pick the level in Step 0 (`reels make --audience`), write it into
BRIEF.md `audience:`, and hold the whole reel to that one contract.

## Ingest first

```bash
reels new videos/<slug> --preset deepspace --title "…" --desc "…"
reels paper <pdf | 1706.03762 | https://arxiv.org/abs/… | report.md> --project .
```
writes `paper/SOURCE.md` (title, authors, year, citation line, abstract, section outline, figure/table
captions, the sentences with numbers), `paper/fulltext.txt`, and `assets/paper/fig-NN.png` /
`page-NN.png` (raster figures; a whole page where the figure is vector). **Read SOURCE.md completely,
then the sections of fulltext that the reel will quote** — for the eight questions below that means
introduction, method, experiments, and the discussion/limitations. Nothing enters the script that is
not in those files — no result from memory, no number rounded "to sound better".

## The eight reviewer questions (the backbone of every paper reel)

Tag every frame with `- beat:` from this vocabulary — `reels paper check --project .` verifies that all
eight questions are answered, that the core-idea block (Q3–Q5) has its share, and that the walkthrough
is long enough. Run it after STORYBOARD.md and before `reels voice`; fix the storyboard until it passes.

| # | The reviewer asks | beat | beginner 小白 answers with… | intermediate 有基础 | expert 专业人士 |
|---|---|---|---|---|---|
| 1 | **What problem, and why does it matter?** | `problem` (+ `hook`) | a situation the viewer has felt; the cost in everyday units ("每试一次要等一整天") | the task stated precisely; the cost in the paper's units | the task, the setting, the exact quantity that is hard; the cost with the paper's number |
| 2 | **What did people do before, and why is that not enough?** | `prior` | "以前的办法是 X，问题是 Y" in one breath, with the one failure that hurts | the two or three families of prior approaches and the specific failure of each | the nearest prior method by name, its mechanism in one sentence, and exactly where it breaks |
| 3 | **What is the key idea — what is new?** | `insight` | one sentence + one analogy chosen in BRIEF.md and carried through the whole reel | one sentence, precise; then the plain restatement; the delta over prior work in one clause | the idea in words first, anchored to the **nearest concept the field already knows** ("a lookup-table world model", "off-policy evaluation by replay"); then the claim as the paper states it and the delta over the nearest prior method |
| 4 | **How does it work?** | `example` (2–4 frames) + `formal` | the analogy's scene walked step by step with the real names in brackets; no equation | one concrete instance walked through on one stage, then the one equation / algorithm the idea lives in | **the same walkthrough as intermediate, in words, on one stage** — symbols appear on screen beside the objects but are not spoken; only then the equations / algorithm, every symbol pointed at the thing it was in the example |
| 5 | **Why does it work — what makes it possible, what are the assumptions?** | `why` | "它能行，是因为…" — the property of the problem, in plain words; one thing that would break it | the property that makes it possible, what each component buys, what breaks without it | assumptions, guarantees, the ablation that supports the central design choice, the alternative the authors rejected |
| 6 | **What is the evidence, and is it fair?** | `evidence` + `result` | one or two results said as comparisons ("比之前最好的高两分多"), what they were compared against | the setup in one sentence, the headline numbers with the baselines named, one cost/efficiency number | tasks, baselines, budget / compute, the key table rows, where the comparison is weaker than it looks |
| 7 | **What does it not do — the limits?** | `limit` | one honest sentence from the paper's own words | the paper's stated limits plus the one you can see in the evidence | stated limits, threats to validity, what was not compared, claimed future work |
| 8 | **So what — should you care / read it?** | `verdict` (+ `callback`) | one sentence to remember, and the analogy closed | who should use it and for what; the one-sentence takeaway | whether the claim is supported, for which settings, and what to read it for |

Order on screen: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Q3 lands by the end of the first fifth of the reel.
Q1–Q2 together take ≤ 20 %; **Q3–Q5 (the core-idea block) take ≥ 45 % (expert) / ≥ 40 % (others)**;
Q6–Q8 take the rest.

**The levels nest; they do not replace each other.** A viewer of the expert reel has not seen the beginner
one, and a video is linear: nobody can skip back to an intuition that was never given. So the expert reel
*contains* the intermediate explanation — the idea in words, the walkthrough on one stage — and then adds
the precision layer (notation, equations, assumptions, ablation, evidence detail, the exact delta over prior
work) on top of it. 先讲懂，再讲严. Precision is added after understanding, never instead of it.

## The core-idea block (Q3–Q5) — where reels go shallow

**A summary of the method is not an explanation**: "循环三步：在线探索、进模拟器池、改写策略并回放" names the
steps and teaches none of them. At every level the block has these beats:

| beat | what must happen in it | frames |
|---|---|---|
| `insight` | the one-sentence idea, then **the property of the problem that makes it possible** ("because the history is already a complete record of …, we can …"). Say it twice: once precise, once plain (也就是说…). | 1 |
| `example` | **one small concrete instance carried through 2–4 frames on one stage**: the actual objects (a node, a trace, a token, a pixel …) with real or realistic values; one step of the method applied to them; the next step; the quantities that change shown changing. The same objects stay on screen — each frame adds or highlights, never replaces. | 2–4 (expert ≥ 3) |
| `formal` | the equation / algorithm / data structure as the paper states it, each symbol pointed at the thing it was in the example. Beginner: skip (a picture of the same scene instead). | 1 |
| `why` | why it works and what it buys: the cost it removes, the guarantee it gives, **what breaks without each component** (the ablation if the paper has one), the alternative the authors rejected and why. | 1 |

Narration rules inside the block:

- **Three parts for every new concept**, the first time it appears: what it is · which thing in the example it is · why it is needed. A concept missing one of the three is cut or expanded, never left as a name.
- **One new concept per frame.** A sentence that lists three things is a table of contents — give each thing its own frame with its own cause → effect.
- **Cause before name**: show the thing happening, then give it the paper's term.
- **Say it twice**: after the precise sentence, restate it in plainer words (也就是说 / 换句话说). Every level, including expert.
- Nothing is "simply" / "just" / "直接". If a step is obvious, say why in half a sentence.
- Expert: the comparison with the nearest prior method is explicit — what they do, what this paper changes, what the change costs.
- The `example` frames speak in the present tense about the objects on screen ("这个节点的得分是 0.62，策略把它排到第二"), not in the abstract ("策略对节点打分").
- **Every `example` frame is three moves: what we want to find out in this step → what the method does → what we see.** The purpose sentence comes first; a step without a purpose is a step the viewer has to memorise.
- **Symbols go on the screen, never into the voice.** The narration says "这棵记录树", "预算偏好", "并行上限"; the screen shows T_i, ρ, W next to the object and lights the object when it is spoken. Never read a subscript, a Greek letter or "等于" chains aloud ("B i 等于六" is unparseable by ear). `reels paper check` fails a script whose narration carries notation.
- **Intuition before notation, at every level.** The first pass through the example is in words; the `formal` frame is the second pass, where the same objects get their symbols. The expert level is not exempt — it adds the second pass, it does not skip the first.
- **At most two new quantities per frame, and no frame in the block longer than ~12 s.** More frames, not denser frames.
- **One central mechanism in depth; secondary mechanisms named.** The walkthrough is the paper's central mechanism. Secondary parts (a budget sweep, a penalty term, an averaging step) each get one sentence saying what they are for — not their formula — unless the paper's claim depends on them.
- Beginner is not "less mechanism": the same steps are walked, in the analogy's scene, with the real names in small brackets (迷宫地图 ＝ 发现树). What is dropped is notation and jargon, not the steps.

Visual rules inside the block:

- The `example` frames share **one stage**: same layout, same objects, `transition_in: crossfade` (or none); the camera pushes in on the part being spoken about. The viewer builds one mental model, not three.
- Quantities change on screen as they are spoken (a counter, a bar growing, a node lighting up), not as labels placed afterwards.
- Intermediate: the real objects with light labels. Expert: the real objects with the paper's notation.

## Audience levels (the contract)

| | **beginner · 小白 / 零基础** | **intermediate · 有基础** (default) | **expert · 专业人士** |
|---|---|---|---|
| Viewer | a curious person with no background; a 中学生, a parent, a manager | studied the field or works next to it; an engineer, a grad student from a nearby area | a researcher / senior engineer in the same field deciding whether to read the paper |
| After the reel they can… | answer all eight questions in their own words, using the analogy | explain the mechanism to a colleague and say why it beats the old way | state the delta over prior work, the method precisely, and how strong the evidence is |
| Terms | ≤ 3, each introduced with a plain-words gloss ("自注意力——每个词给其他词打分"), then the gloss, not the term | by name after a one-line definition the first time | as the paper uses them, no glosses |
| Equations | none (a number line or a picture instead) | at most one, the one the idea lives in, symbols lit as spoken | 2–3, as printed, each symbol named once |
| Numbers | 1–2 headline numbers, said as comparisons | headline results with the baselines named, plus one cost/efficiency number | the key table rows, the ablation deltas, the training/compute setup if it carries the claim |
| Analogy | one, chosen in BRIEF.md, used in every Q3–Q5 frame and closed at Q8 | one, used in the mechanism frames, dropped for the results | one **from the field**: the nearest concept the reader already knows (a world model, a replay buffer, off-policy evaluation, a cache …), named in Q3 and used to carry the walkthrough; no everyday analogies |
| Visuals | metaphor scenes (a queue, a room of people, a relay), big labels; the paper's figure shown once as "它长这样" without explanation | the main figure as a **plate** (assets/paper/fig-NN.png, credited) then its core redrawn in code and animated; results as two labelled bars | figures and tables as plates with **callouts** (crop/zoom to the row or box being spoken of), the architecture redrawn faithfully, plots redrawn with the real numbers |
| Skip | notation, training details, author names beyond the citation line | hyper-parameters, ablation tables unless the ablation *is* the finding | nothing is omitted, but only the central mechanism is walked; secondary mechanisms are named with their purpose, the paper's own repetition is cut |
| Pace & length | `reels voice --rate -5%`; 80–100 s, 10–13 frames | default rate; 130–170 s, 13–18 frames | default rate (not faster — density is already higher); 240–300 s, 22–30 frames of ≤ 12 s (> 5 min → chapters) |
| Preset | `notebook` / `deepspace` | `deepspace` / `notebook` / `chalk` | `deepspace` / `chalk` |

This is why the default lengths are 90 / 150 / 270 s: eight questions with a real walkthrough do not
fit in 70 s, and the expert reel carries the intermediate explanation plus a precision layer. Whatever the level: every number as printed in SOURCE.md, the citation line once on
screen, the limit in the paper's own words.

## What the walkthrough example is, by paper type

| Paper type | The `example` instance | Preset |
|---|---|---|
| a new method / architecture (most ML, systems, algorithms) | one input going through the method step by step (one sentence through the model, one trace through the loop) — old way on the left greyed, new way on the right lit | `deepspace` (ML, physics, CS) · `notebook` (biology, economics, medicine) |
| an empirical finding / measurement | one measured case: the setup drawn, the measurement taken, the number appearing | `notebook` · `deepspace` |
| a theory / derivation | one concrete value pushed through the 2–3 steps of the argument on a board | `chalk` |
| a survey / position paper | one representative work per camp, placed on the map the survey draws | `ink` · `notebook` |

## Visual rules (outside the block)

- The paper's figure may appear as a plate *first* (route `plate`, `assets/paper/fig-NN.png`, with
  "Figure N, <paper>" small in a corner), then the code version takes over on top of it — the viewer sees
  "this is the real thing" and then "this is what it means".
- **Page renders** (`page-NN.png`) need a crop: wrap in a div with `overflow: hidden` and position the
  image so the figure fills the box (`object-fit: none; object-position: X% Y%` or a transform). Never show
  a whole page of text.
- **Numbers compare.** A result is two bars / two paths / two timers side by side (old vs new), each
  labelled with the printed value; a single big number is for the hook only.
- Equations only as the level allows; each symbol lit as it is spoken (KaTeX; chalk preset or a floating
  board in deepspace), **at ≥ 44 px at 1080p**, with a persistent symbol ↔ example legend strip across the
  `formal` frames (T_i = 这棵记录树 · ρ = 预算偏好 · W = 并行上限). Never a wall of formulas.
- Palette and type as the preset; the citation line and figure credits in the preset's label style,
  never a white box.

## Fact discipline (checked before voicing)

For every sentence of SCRIPT.md that states a result or a mechanism, be able to point at the line of
SOURCE.md or fulltext.txt it comes from; list those lines in BRIEF.md `## Notes` (a short table:
claim → source line). If a claim has no line, cut it. The credit for figures is already in CREDITS.md
(`reels paper` wrote it); keep that file in the delivery.

## Pre-render checklist (paper reels fail review on any of these)

- [ ] `reels paper check --project .` passes: all eight questions tagged and present, core share ≥ 45 % / 40 %, `example` ≥ 3 / 2 frames, no notation in the narration, no core frame over ~12 s.
- [ ] Expert: the idea and the walkthrough are first given in words (the intermediate explanation), the symbols come on a second pass; Q3 names the nearest known concept in the field.
- [ ] Every new concept in Q3–Q5 has its three parts (what · which thing in the example · why needed); no list-sentence stands in for an explanation.
- [ ] The `example` frames are one continuous stage with the same objects, and the quantities change on screen as spoken.
- [ ] The paper's main figure appears as a plate at least once (any level), with "Figure N — <short cite>" in the corner.
- [ ] Every result frame shows **both** sides with their printed numbers (baseline *and* paper) — a bar without a number is a defect.
- [ ] On-screen labels ≥ 28 px at 1080p (≥ 40 px for the hero word); token/word boxes ≥ 56 px tall.
- [ ] Term count, equation count and analogy use match the audience table.
- [ ] BRIEF.md `## Notes` has the claim → source-line table, and every spoken claim is in it.
