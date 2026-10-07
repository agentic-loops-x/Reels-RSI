#!/usr/bin/env bash
# Build the arXiv source bundle from paper/main.tex.
#   bash paper/arxiv/build.sh            -> paper/arxiv/reels-rsi-arxiv.tar.gz (+ staging dir paper/arxiv/stage/)
#   bash paper/arxiv/build.sh --verify   -> also compile the bundle with pdflatex+bibtex in a TeX Live container
# arXiv compiles with pdflatex and does not run BibTeX, so the bundle carries main.bbl and only the figures
# main.tex includes. Line 1 of the bundled main.tex is \pdfoutput=1 (arXiv's pdflatex signal); it is not in
# paper/main.tex because tectonic's XeTeX engine rejects it.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; S="$P/arxiv/stage"; OUT="$P/arxiv/reels-rsi-arxiv.tar.gz"
rm -rf "$S"; mkdir -p "$S/figures"
{ echo '\pdfoutput=1'; cat "$P/main.tex"; } > "$S/main.tex"
cp "$P/refs.bib" "$S/"
for f in $(grep -o 'figures/[A-Za-z0-9._-]*' "$P/main.tex" | sort -u); do cp "$P/$f" "$S/figures/"; done
# main.bbl from tectonic (same bib, same style); strip the \pdfoutput line for the XeTeX run
( cd "$S" && sed '1d' main.tex > _tt.tex && tectonic --keep-intermediates _tt.tex >/dev/null 2>&1 && mv _tt.bbl main.bbl && rm -f _tt.* )
# plain-text abstract for the arXiv form
python3 - "$S" <<'PY'
import re, sys
s = sys.argv[1]; t = open(f"{s}/main.tex").read()
a = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S).group(1)
a = a.replace("\\sys{}", "Reels-RSI").replace("---", " -- ").replace("2$\\times$2", "2x2").replace("\\%", "%")
a = re.sub(r"\\emph\{([^}]*)\}", r"\1", a); a = re.sub(r"\s+", " ", a).strip()
open(f"{s}/abstract.txt", "w").write(a + "\n"); print(f"abstract: {len(a)} chars (arXiv limit 1920)")
PY
( cd "$S" && tar czf "$OUT" main.tex main.bbl refs.bib figures )
echo "bundle: $OUT ($(du -h "$OUT" | cut -f1))"; tar tzf "$OUT"
if [[ "${1:-}" == "--verify" ]]; then
  docker run --rm -v "$S:/w" -w /w texlive/texlive:latest-medium bash -c \
    'pdflatex -interaction=nonstopmode main.tex >/dev/null && pdflatex -interaction=nonstopmode main.tex >/dev/null; echo "pdflatex exit $?"; grep -c "LaTeX Warning: Reference .* undefined\|Citation .* undefined" main.log || echo "0 undefined refs/citations"; pdfinfo main.pdf 2>/dev/null | grep Pages || python3 -c "print(open(\"main.pdf\",\"rb\").read(8))"'
fi
