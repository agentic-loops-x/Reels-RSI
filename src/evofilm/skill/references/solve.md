# Solve mode — 题目讲解 (math · physics · chemistry · 语文 · English), 小学到高中

Read for any "讲这道题 / 解题视频 / 知识点讲解 / 古诗讲解 / 笔顺" request. The film is a worked example
on a blackboard (preset `chalk`), or a notebook page (`notebook`) for younger viewers, or ink
(`ink`) for 古诗文. KaTeX formulas and stroke-order animation below were rendered and checked in a
EvoFilm snapshot test.

## Correctness first (stricter than science films)

1. **Solve it in code before writing a word of script.** Arithmetic/algebra: a Python one-liner;
   equations, geometry, physics: `uvx --with sympy python -c "…"`. Put the computation and the
   answer in BRIEF.md `## Notes`. The film's numbers come only from there.
2. **Use the method the grade is taught.** 鸡兔同笼 for 小学 = 假设法 / 画图法, not 二元一次方程;
   初中 physics = 受力分析 + 公式, not calculus. Write the grade in BRIEF.md `audience`.
3. **Show the check.** The last step substitutes the answer back into the problem (头 23+12=35 ✓,
   脚 23×2+12×4=94 ✓) and marks it in green.
4. 语文: quote the standard text (人教/部编版) exactly; 注释 and 译文 from a reliable edition, sources in BRIEF.

## Shape of a problem film (45–90 s; 9:16 suits 抖音/视频号 study accounts)

| Beat | Screen | Narration |
|---|---|---|
| 题目 hook (≤ 5 s) | the problem, short, on the board | read it, ask the question |
| 画图 picture | 线段图 / 示意图 / 受力图 / 分子模型 / 意象画面 — drawn as it is described | "我们先把它画出来" |
| 关键一步 key idea | the one move that cracks it, in colour | the insight in one sentence |
| 分步 steps | one line of working per beat, earlier lines dim | each step's reason |
| 验算 check | substitute back, ✓ in green, answer boxed | "答案对不对？代回去看看" |
| 方法 takeaway | the method name + when to use it (one line) | 变式 / 易错点 (optional) |

Storyboard `route:` values: `solve/formula`, `solve/diagram`, `solve/geometry`, `solve/physics`,
`solve/chem`, `solve/strokes`, `solve/poem`.

## Formulas — KaTeX (pinned), rendered synchronously at build time

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
…
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<!-- chemistry: <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/mhchem.min.js"></script> → \ce{2H2 + O2 -> 2H2O} -->
```
```js
katex.render("\\text{兔} = 24 \\div (4-2) = {\\color{#F4D35E}12}", el, { throwOnError: true, output: "html" });
tl.fromTo(el, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.5, ease: "power2.out" }, wordTime);
```
- Chinese inside `\text{…}` renders with the shipped Noto fonts (run `evofilm fonts` after writing).
- Colour = meaning (preset `chalk`): yellow = the unknown, pink = what changed this step, blue = givens, green = checked answer.
- To "write" a line, reveal it with a left→right `clip-path: inset(0 100% 0 0)` → `inset(0 0 0 0)` tween instead of a fade.
- Rewrite, don't morph: strike through the old line (a drawn chalk line) and write the new one below.

## Stroke order — 笔顺 (`evofilm hanzi`)

```bash
evofilm hanzi 静夜思 --project .     # → assets/hanzi.js  window.EF_HANZI[char] = {strokes, medians}; credit added
```
```js
// 1024 box, y up → draw inside <g transform="translate(0, 900) scale(1, -1)">
H.strokes.forEach((d, i) => {
  // mask path along the median, butt caps, wide enough to cover the stroke
  med.setAttribute("d", "M" + H.medians[i].map(p => p.join(" ")).join(" L"));
  med.setAttribute("stroke-width", "160"); med.setAttribute("stroke-linecap", "butt");
  const L = med.getTotalLength() + 80;
  // dash L, gap 2L, start 8 units past the end — no antialiased sliver before the stroke begins
  tl.fromTo(med, { strokeDasharray: `${L} ${2 * L}`, strokeDashoffset: L + 8 },
                 { strokeDashoffset: 0, duration: 0.32, ease: "none" }, start + i * 0.36);
});
```
Never use HanziWriter's own animator (requestAnimationFrame → breaks seek rendering; `evofilm lint` flags it).

## Diagrams by subject

- **线段图 / 应用题** — bars as rounded rects drawn on (stroke then fill), braces with labels,
  the "assume all chickens" bar morphing to the real one; numbers in JetBrains Mono.
- **几何** — compute every point in JS (no eyeballed coordinates); draw construction lines thin and
  dim, the figure thick; angle arcs + labels; 动点 problems drive a point along a path with a proxy-clock tween.
- **函数** — axes with ticks, the curve drawn on with a dot tracing it; key points (零点/顶点) pop in on their words.
- **物理** — force arrows whose length is proportional to magnitude (G vs F浮); motion via bake-then-seek
  (techniques.md); a v–t or s–t graph drawn in sync with the moving object.
- **化学** — ball-and-stick molecules (Three.js, techniques.md) or flat structural formulas; reactions
  break and re-form bonds; equations with mhchem; balance coefficients step by step in pink.
- **古诗文** — preset `ink`: one image per line (意象: 明月、床前、霜), the line written vertically in
  Noto Serif SC, key words annotated (注释) with a seal-red underline; 朗读 rate `--rate -8%`.
- **English grammar** — sentence diagrams: words as tiles, roles colour-coded, arrows for agreement.

## Voice

zh-CN-XiaoxiaoNeural (warm, teacher-like) or zh-CN-YunxiNeural; `--rate +0%` for 小学, `+6%` for 高中.
Say numbers the way a teacher does ("三十五个头"). SFX: `tick` per written step, `chime` on the
check mark, nothing louder.
