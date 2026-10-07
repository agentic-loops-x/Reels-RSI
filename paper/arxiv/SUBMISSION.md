# arXiv submission — what to paste into the form

Build the bundle first (`bash paper/arxiv/build.sh --verify`; the `--verify` step needs Docker and
compiles the bundle with pdflatex the way arXiv does). Upload `paper/arxiv/reels-rsi-arxiv.tar.gz` at
https://arxiv.org/submit (Start new submission → upload the .tar.gz as the source).

| field | value |
|---|---|
| Title | Reels-RSI: Program-Level Self-Improvement for Code-Rendered Explainer Videos |
| Authors | Agentic Loops X |
| Abstract | `paper/arxiv/stage/abstract.txt` (written by `build.sh`; 1 914 characters, limit 1 920) |
| Comments | 19 pages, 4 figures, 9 tables. Code, rules, lessons, data and evolve reports: https://github.com/agentic-loops-x/Reels-RSI |
| Primary category | cs.AI (Artificial Intelligence) |
| Cross-lists | cs.MM (Multimedia), cs.SE (Software Engineering) |
| License | CC BY 4.0 (matches the Apache-2.0 code; lets the paper be reused with attribution) |
| Report number / journal ref / DOI | leave empty |

arXiv processing notes

- The bundle's `main.tex` starts with `\pdfoutput=1`, which tells arXiv to run pdflatex (needed for the
  PNG/JPG figures). arXiv does not run BibTeX, so `main.bbl` is included; `refs.bib` is there for readers.
- Only the four figures `main.tex` includes are bundled; `main.pdf`, logs and aux files are left out.
- A first submission from a new account in cs.AI may require endorsement; arXiv shows the request
  form after the upload step if so.
- After the upload, check the processed PDF arXiv shows (19 pages, the logo in the author block on page 1,
  Figure 4 the learning curve on page 15) before pressing Submit. Announcements go out at 20:00 ET on
  weekdays; submissions made before 14:00 ET appear the same evening.

After the identifier arrives (`arXiv:2510.xxxxx`)

1. Replace "*submitted, ID pending*" in `README.md`, `README.zh-CN.md` and `paper/README.md` with the abs link.
2. Add `eprint`, `archivePrefix = {arXiv}` and `primaryClass = {cs.AI}` to the BibTeX entries in those files.
3. Add `identifiers: [{type: other, value: "arXiv:2510.xxxxx"}]` to `CITATION.cff`'s preferred citation.
4. Set the arXiv link in the GitHub repository's About box.
