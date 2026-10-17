"""Paper / document → the source digest an explainer reel is scripted from.

    reels paper <source> --project <dir>        source = PDF path · arXiv id or URL · PDF URL · .md / .txt / .html / web page
    reels paper <source> --show                 print the digest, write nothing into a project

Written into the project (the director reads SOURCE.md first, fulltext for the parts it quotes):
  paper/SOURCE.md          title, authors, year, citation line, abstract, section outline, figure and table
                           captions, sentences with the numbers worth quoting, how to use all of it
  paper/fulltext.txt       the whole text (capped at FULLTEXT_CAP characters)
  assets/paper/fig-NN.png  raster figures from the PDF (≥ MIN_FIG px) — plates for the frames
  assets/paper/page-NN.png the page of every figure/table caption that had no raster image (vector figures)
  CREDITS.md               a line crediting the paper for the figures shown

Every source is ingested once into ~/.reels/papers/<key>/ (the download, the text, the figures); `reels make
--paper` ingests before the agent starts and the agent's `reels paper … --project` copies from the cache.
Needs poppler (`pdftotext`, `pdfimages`, `pdftoppm`): macOS `brew install poppler` · Ubuntu `apt install poppler-utils`.
"""

import argparse
import hashlib
import html.parser
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from reels_rsi import paths

FULLTEXT_CAP = 120_000          # characters of fulltext.txt — a 15-page paper is ~40k; books are cut
MIN_FIG = (400, 300)            # smaller raster images are logos, icons, equation fragments
MAX_FIGS = 8
MAX_PAGES = 6                   # page renders for captions without a raster figure
ARXIV_API = "https://export.arxiv.org/api/query?id_list={id}"
ARXIV_ID = re.compile(r"(?:arxiv\.org/(?:abs|pdf|html)/)?(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}))(?P<v>v\d+)?(?:\.pdf)?/?$", re.I)
HEADING_INLINE = re.compile(r"^(?P<num>\d{1,2}(?:\.\d{1,2}){0,2})\.?\s+(?P<title>[A-Z][^\n]{2,80})$")
HEADING_NUM = re.compile(r"^(?P<num>\d{1,2}(?:\.\d{1,2}){0,2})\.?$")
HEADING_WORDS = ("Abstract", "Introduction", "Background", "Related Work", "Preliminaries", "Method", "Methods", "Approach",
                 "Experiments", "Results", "Discussion", "Conclusion", "Conclusions", "Limitations", "Acknowledgements",
                 "Acknowledgments", "References", "Appendix")
HEADING_WORD = re.compile(r"^(?P<title>(?:" + "|".join(w + "|" + w.upper() for w in HEADING_WORDS) + r")(?:\s+(?:and|&)\s+[A-Z][\w-]*|\s+[A-Z][\w-]*){0,3})$")
CAPTION = re.compile(r"^(?P<kind>Figure|Fig\.|Table)\s*(?P<n>\d+)\s*[.:|]\s*(?P<text>\S[^\n]*)$")
CITE = re.compile(r"\[\d+(?:\s*[,–-]\s*\d+)*\]|\bsections?\s+\d+(?:\.\d+)*|\bfigures?\s+\d+|\btables?\s+\d+", re.I)
NUMBER_SENTENCE = re.compile(r"\d")
UNIT_HINT = re.compile(r"(%|×|\bx\b|BLEU|accurac|F1|\bAUC|error|GPU|TPU|hour|day|param|million|billion|\bM\b|\bB\b|"
                       r"points?|dB|nm|ms|\bs\b|speed|faster|fewer|larger|smaller|increase|decrease|reduc|improv)", re.I)


# ── sources ──────────────────────────────────────────────────────────────────
def arxiv_id(src):
    """'1706.03762' · 'https://arxiv.org/abs/1706.03762v7' · 'arxiv.org/pdf/1706.03762.pdf' → '1706.03762' (no version)."""
    s = src.strip()
    s = re.sub(r"^(https?://)?(www\.)?", "", s)
    s = re.sub(r"^arxiv:", "", s, flags=re.I)
    if s.startswith("arxiv.org/") or re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", s) or re.fullmatch(r"[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?", s):
        m = ARXIV_ID.search(s)
        if m:
            return m.group("id")
    return None


def source_key(src):
    """A stable folder name for the cache: the arXiv id, or a hash of the path/URL."""
    aid = arxiv_id(src)
    if aid:
        return "arxiv-" + aid.replace("/", "-")
    p = Path(src).expanduser()
    base = str(p.resolve()) if p.exists() else src
    return re.sub(r"[^\w.-]+", "-", Path(base).stem)[:40].strip("-") + "-" + hashlib.sha1(base.encode()).hexdigest()[:8]


def fetch(url, dst, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "reels-rsi/0.1 (+https://github.com/agentic-loops-x/Reels-RSI)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    Path(dst).write_bytes(data)
    return data


def arxiv_meta_page(aid):
    """Fallback when the API is rate-limited (HTTP 429): the abs page's citation_* meta tags."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = fetch(f"https://arxiv.org/abs/{aid}", Path(tmp) / "abs.html", timeout=60).decode("utf-8", "replace")
    tags = {}
    for k, v in re.findall(r'<meta name="(citation_[a-z_]+|description)" content="([^"]*)"', raw):
        tags.setdefault(k, []).append(html.unescape(v))
    one = lambda k: (tags.get(k) or [""])[0].strip()
    abstract = re.search(r'<blockquote class="abstract[^"]*">\s*<span class="descriptor">Abstract:</span>(.*?)</blockquote>', raw, re.S)
    authors = [", ".join(reversed([p.strip() for p in a.split(",", 1)])).replace(", ", " ") if "," in a else a for a in tags.get("citation_author", [])]
    if not one("citation_title"):
        raise SystemExit(f"✗ arXiv knows no paper {aid}")
    return {"title": re.sub(r"\s+", " ", one("citation_title")), "authors": authors,
            "abstract": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", abstract.group(1))).strip() if abstract else one("description"),
            "year": (one("citation_date") or one("citation_online_date"))[:4], "categories": [], "comment": "", "journal": "",
            "doi": "", "arxiv": aid, "url": f"https://arxiv.org/abs/{aid}"}


def arxiv_meta(aid):
    """Title, authors, abstract, year, categories from the arXiv API (Atom); the abs page when the API refuses."""
    xml = None
    for wait in (0, 4, 10):
        time.sleep(wait)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                xml = fetch(ARXIV_API.format(id=aid), Path(tmp) / "meta.xml", timeout=60).decode("utf-8", "replace")
            break
        except (OSError, ValueError):       # HTTPError 429 · timeouts · resets
            continue
    if xml is None:
        return arxiv_meta_page(aid)
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    entry = ET.fromstring(xml).find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None:
        raise SystemExit(f"✗ arXiv knows no paper {aid}")
    text = lambda tag: re.sub(r"\s+", " ", (entry.findtext(tag, "", ns) or "")).strip()
    published = text("a:published")
    return {"title": text("a:title"), "abstract": text("a:summary"), "year": published[:4],
            "authors": [re.sub(r"\s+", " ", a.findtext("a:name", "", ns)).strip() for a in entry.findall("a:author", ns)],
            "categories": [c.get("term") for c in entry.findall("a:category", ns)],
            "comment": text("x:comment"), "journal": text("x:journal_ref"), "doi": text("x:doi"),
            "arxiv": aid, "url": f"https://arxiv.org/abs/{aid}"}


class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article", "pre", "blockquote"}

    def __init__(self):
        super().__init__()
        self.out, self.skip, self.title, self._in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.skip:
            self.out.append(data)


def html_text(raw):
    p = _Text()
    p.feed(raw)
    text = re.sub(r"[ \t]+", " ", "".join(p.out))
    return p.title.strip(), re.sub(r"\n\s*\n+", "\n\n", text).strip()


# ── PDF ──────────────────────────────────────────────────────────────────────
def need(tool, what):
    if not shutil.which(tool):
        raise SystemExit(f"✗ `{tool}` (poppler) is needed to {what} — macOS: brew install poppler · Ubuntu: apt install poppler-utils")


def pdf_text(pdf):
    """Reading-order text, pages separated by form feeds (pdftotext; pypdf when poppler is missing)."""
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    try:
        import pypdf  # noqa: F401 — optional
        return "\f".join((p.extract_text() or "") for p in pypdf.PdfReader(str(pdf)).pages)
    except ImportError:
        need("pdftotext", "read a PDF (or `pip install pypdf`)")
    raise SystemExit(f"✗ no text in {pdf} — a scanned PDF needs OCR first")


def pdf_pages(pdf):
    if not shutil.which("pdfinfo"):
        return 0
    r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
    return int(m.group(1)) if m else 0


def pdf_figures(pdf, out_dir, limit=MAX_FIGS, min_px=MIN_FIG):
    """Raster figures as PNG: [{path, page, w, h}] — the big ones, in page order, at most `limit`."""
    out_dir = Path(out_dir)
    if not shutil.which("pdfimages"):
        return []
    r = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True)
    rows = []
    for line in r.stdout.splitlines()[2:]:
        f = line.split()
        if len(f) < 5 or f[2] != "image":
            continue
        page, num, w, h = int(f[0]), int(f[1]), int(f[3]), int(f[4])
        if w >= min_px[0] and h >= min_px[1] and 0.2 <= w / h <= 6:
            rows.append((page, num, w, h))
    if not rows:
        return []
    rows = rows[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    figs = []
    with tempfile.TemporaryDirectory() as tmp:
        for page in sorted({p for p, *_ in rows}):
            subprocess.run(["pdfimages", "-png", "-p", "-f", str(page), "-l", str(page), str(pdf), f"{tmp}/img"],
                           capture_output=True)
        for i, (page, num, w, h) in enumerate(rows, 1):
            src = Path(tmp) / f"img-{page:03d}-{num:03d}.png"
            if not src.exists():
                continue
            dst = out_dir / f"fig-{i:02d}.png"
            shutil.copyfile(src, dst)
            figs.append({"path": dst.name, "page": page, "w": w, "h": h})
    return figs


def render_pages(pdf, pages, out_dir, width=1400):
    """PNG of whole pages (vector figures live only there): page-NN.png."""
    out_dir = Path(out_dir)
    if not pages or not shutil.which("pdftoppm"):
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for p in pages:
        subprocess.run(["pdftoppm", "-png", "-r", "150", "-scale-to-x", str(width), "-scale-to-y", "-1",
                        "-f", str(p), "-l", str(p), "-singlefile", str(pdf), str(out_dir / f"page-{p:02d}")], capture_output=True)
        if (out_dir / f"page-{p:02d}.png").exists():
            made.append({"path": f"page-{p:02d}.png", "page": p})
    return made


# ── text analysis ────────────────────────────────────────────────────────────
def page_of(text, pos):
    return text.count("\f", 0, pos) + 1


def caption_pages(text, pos):
    """The page a caption's figure/table is on: its own page, plus the next one when the caption sits in the
    bottom third of the page text — LaTeX floats placed at the top of the next page come out that way in
    pdftotext (Table 2 of 1706.03762 reads on p. 7, is drawn on p. 8)."""
    page = page_of(text, pos)
    start = text.rfind("\f", 0, pos) + 1
    end = text.find("\f", pos)
    end = len(text) if end < 0 else end
    frac = (pos - start) / max(end - start, 1)
    return [page, page + 1] if frac > 0.66 and end < len(text) else [page]


def _next_number(num, state):
    """Numbered headings must come in order (1, 2, 2.1, 2.2, 3 …); table rows like '28.4 EN-FR' or '4.33 BLEU'
    and repeated numbers (a figure label '3 Scaled …' inside section 3) are not headings."""
    parts = [int(x) for x in num.split(".")]
    if len(parts) > 3 or parts[0] == 0:
        return False
    top, sub, subsub = state
    nxt = lambda cur, n: n in (cur + 1, cur + 2)          # one heading may have been lost in the extraction
    if len(parts) == 1:
        ok = nxt(top, parts[0])
        if ok:
            state[:] = [parts[0], 0, 0]
        return ok
    a, b = parts[0], parts[1]
    if len(parts) == 2:
        ok = (a == top and nxt(sub, b)) or (nxt(top, a) and b == 1)
        if ok:
            state[:] = [a, b, 0]
        return ok
    c = parts[2]
    ok = (a == top and b == sub and nxt(subsub, c)) or (a == top and nxt(sub, b) and c == 1)
    if ok:
        state[:] = [a, b, c]
    return ok


def _titlish(s):
    return 2 <= len(s) <= 80 and s[0].isupper() and len(s.split()) <= 10 and not s.endswith((".", ",", ";", ":")) \
        and "[" not in s and len(re.findall(r"\d+(?:\.\d+)?", s)) <= 1


def sections(text):
    """[(number, title, char offset)] — '3.2 Attention' on one line, or '3.2' on its own line and the title on
    the next (how pdftotext lays out most LaTeX papers), plus unnumbered Abstract/Conclusion-style headings."""
    lines = text.split("\n")
    offsets, pos = [], 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    # a running page header ("2 Dream-RSI: Recursive Self-Improvement …") repeats on every page — never a section
    seen_titles = {}
    for ln in lines:
        m = HEADING_INLINE.match(ln.strip())
        if m:
            seen_titles[m.group("title").strip()] = seen_titles.get(m.group("title").strip(), 0) + 1
    out, state, i = [], [0, 0, 0], 0
    while i < len(lines):
        line = lines[i].strip()
        m = HEADING_INLINE.match(line)
        if m and seen_titles.get(m.group("title").strip(), 0) < 2 and _titlish(m.group("title").strip()) \
                and _next_number(m.group("num"), state):
            out.append((m.group("num"), m.group("title").strip(), offsets[i]))
        elif HEADING_NUM.match(line):
            j = i + 1
            while j < len(lines) and j <= i + 2 and not lines[j].strip():
                j += 1
            if j < len(lines) and _titlish(lines[j].strip()) and sum(l.strip() == lines[j].strip() for l in lines) < 2 \
                    and _next_number(line.rstrip("."), state):
                out.append((line.rstrip("."), lines[j].strip(), offsets[i]))
                i = j
        else:
            m = HEADING_WORD.match(line)
            if m and line.lower() not in {t.lower() for _, t, _ in out}:
                out.append(("", line, offsets[i]))
        i += 1
    return out


def captions(text):
    """Figure/table captions: [(kind, n, caption, page)] — a caption continues on the next line until a blank."""
    out, lines, pos = [], text.split("\n"), 0
    seen = set()
    for i, raw in enumerate(lines):
        m = CAPTION.match(raw.strip())
        if m:
            kind = "Figure" if m.group("kind").startswith("Fig") else "Table"
            key = (kind, int(m.group("n")))
            cap = m.group("text").strip()
            j = i + 1
            # continue onto the next lines until the caption closes with a period (pdftotext seldom leaves a
            # blank line between a caption and the paragraph or table after it)
            while j < len(lines) and lines[j].strip() and len(cap) < 400 and not cap.endswith((".", ".)", "]")) \
                    and not CAPTION.match(lines[j].strip()):
                cap += " " + lines[j].strip()
                j += 1
            if key not in seen:
                seen.add(key)
                out.append((kind, key[1], re.sub(r"\s+", " ", cap), page_of(text, pos), caption_pages(text, pos)))
        pos += len(raw) + 1
    return out


def number_sentences(text, limit=14):
    """Sentences that carry a number with a unit-like hint — the facts a script may quote verbatim."""
    flat = re.sub(r"\s+", " ", text.replace("\f", " "))
    out, seen = [], set()
    for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", flat):
        s = s.strip()
        bare = CITE.sub("", s)                      # digits inside [12], "section 3.2", "Figure 2" do not count
        if 40 <= len(s) <= 320 and NUMBER_SENTENCE.search(bare) and UNIT_HINT.search(bare):
            if re.search(r"\b(19|20)\d{2}\b", bare) and not NUMBER_SENTENCE.search(re.sub(r"\b(19|20)\d{2}\b", "", bare)):
                continue      # a year alone is not a result
            k = s[:60].lower()
            if k not in seen:
                seen.add(k)
                out.append(s)
        if len(out) >= limit:
            break
    return out


def abstract_of(text, meta):
    if meta.get("abstract"):
        return meta["abstract"]
    m = re.search(r"^\s*Abstract\s*\.?\s*$\n+(.*?)(?=\n\s*\n\s*(?:1\s|Introduction|\d\s+Introduction))", text, re.S | re.M | re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:2500]
    return re.sub(r"\s+", " ", text[:1500]).strip()


def title_of(text, meta, fallback):
    """The first title-like line of the text; a short line ending in ':' is the first half of a two-line title."""
    if meta.get("title"):
        return meta["title"]
    lines = [l.strip() for l in text.split("\n")[:40]]
    for i, s in enumerate(lines):
        if not s or re.search(r"@|arXiv|http|^\d", s) or not s[0].isupper():
            continue
        if s.endswith(":") and i + 2 < len(lines):
            nxt = next((x for x in lines[i + 1:i + 3] if x), "")
            if nxt and nxt[0].isupper():
                return f"{s} {nxt}"
        if 12 <= len(s) <= 160:
            return s
    return fallback


# ── digest ───────────────────────────────────────────────────────────────────
def outline(text, secs, per=320):
    rows = []
    for k, (num, title, pos) in enumerate(secs):
        end = secs[k + 1][2] if k + 1 < len(secs) else len(text)
        body = re.sub(r"\s+", " ", text[pos:end]).strip()
        body = body[len(num):].strip() if num and body.startswith(num) else body
        body = body[len(title):].strip() if body.startswith(title) else body
        words = len(body.split())
        rows.append(f"- **{(num + ' ') if num else ''}{title}** (p. {page_of(text, pos)}, ~{words} words) — {body[:per]}{'…' if len(body) > per else ''}")
    return "\n".join(rows)


def citation(meta, title):
    authors = meta.get("authors") or []
    year = meta.get("year") or ""
    where = f"arXiv:{meta['arxiv']}" if meta.get("arxiv") else (meta.get("url") or meta.get("file") or "")
    if authors:
        first = authors[0].split()[-1]
        who = first + (" et al." if len(authors) > 2 else (" & " + authors[1].split()[-1] if len(authors) == 2 else ""))
        head = f"{who}{(', ' + year) if year else ''} — "
    else:
        head = ""
    return f"{head}“{title}”{(' (' + year + ')') if year and not authors else ''}{(' (' + where + ')') if where else ''}"


def year_of(text):
    """The first plausible year on the first page (local PDFs carry no metadata)."""
    m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", text.split("\f")[0][:4000])
    return m.group(1) if m else ""


def digest(meta, text, figs, pages, caps, title):
    secs = sections(text)
    nums = number_sentences(text)
    unclaimed = {f["path"]: f["page"] for f in figs}
    page_by_page = {p["page"]: p["path"] for p in pages}
    cap_rows = []
    for kind, n, cap, page, pgs in caps:
        # a figure sits on its caption's page or (a float) at the top of the next one — never on the page before:
        # the raster image before a "Figure 1" caption is the affiliation logo on page 1
        mine = [p for p, pg in unclaimed.items() if pg in pgs] or (
            [p for p, pg in unclaimed.items() if pg == page + 1][:1] if kind == "Figure" else [])
        for p in mine:
            unclaimed.pop(p)
        renders = [page_by_page[p] for p in pgs if p in page_by_page]
        where = ", ".join(f"assets/paper/{p}" for p in mine) or \
                (", ".join(f"assets/paper/{r}" for r in renders) + " (whole page" + (" — the caption is at the foot of the first, the "
                 "figure/table may be at the top of the second" if len(renders) > 1 else "") + " — crop/zoom in the frame)"
                 if renders else "not extracted")
        pages_label = f"p. {pgs[0]}–{pgs[-1]}" if len(pgs) > 1 else f"p. {page}"
        cap_rows.append(f"- **{kind} {n}** ({pages_label}): {cap[:300]}{'…' if len(cap) > 300 else ''}\n  → {where}")
    if unclaimed:
        cap_rows.append("- other images in the PDF, not a captioned figure: " + ", ".join(
            f"assets/paper/{p} (p. {pg}{' — on the title page: probably a logo or banner, do not show it as a figure' if pg == 1 else ''})"
            for p, pg in unclaimed.items()))
    words = len(text.split())
    lines = [f"# Source: {title}\n",
             f"- authors: {', '.join(meta.get('authors') or []) or 'unknown'}",
             f"- year: {meta.get('year') or 'unknown'}" + (f" · {', '.join(meta['categories'])}" if meta.get("categories") else "")
             + (f" · {meta['journal']}" if meta.get("journal") else ""),
             f"- source: {meta.get('url') or meta.get('file') or ''}",
             f"- cite on screen: {citation(meta, title)}",
             f"- size: {meta.get('pages') or '?'} pages · ~{words} words · figures extracted: {len(figs)} · page renders: {len(pages)} (assets/paper/)",
             "", "## Abstract", "", abstract_of(text, meta), "",
             "## Outline (first words of every section)", "", outline(text, secs) or "(no numbered sections found — read paper/fulltext.txt)", "",
             "## Figures and tables", "", "\n".join(cap_rows) or "(no captions found)", "",
             "## Sentences with numbers worth quoting (verbatim)", "", "\n".join(f"- {s}" for s in nums) or "(none found)", "",
             "## How to use this", "",
             "- Every claim, number and name in the script comes from this file or paper/fulltext.txt — nothing else. "
             "Quote results with the paper's own units; say 论文称 / \"the paper reports\" for its claims.",
             "- The reel is not a summary in paper order: find the one idea (why it works), teach that with an analogy, "
             "then show the strongest result. Recipe: references/paper.md.",
             "- A figure image is a plate (`route: plate`): show it, then redraw the part that matters in code on top of it. "
             "Page renders need a crop (object-fit / clip) to the figure.",
             "- Show the citation line once on screen (frame 1 corner or the closing frame)."]
    return "\n".join(lines) + "\n"


# ── ingest (cache) · install (project) ───────────────────────────────────────
def ingest(src, cache=None, quiet=False):
    """Download/read the source once into ~/.reels/papers/<key>/ and build the digest. Returns the cache dir."""
    root = Path(cache) if cache else paths.papers()
    key = source_key(src)
    d = root / key
    if (d / "SOURCE.md").exists() and (d / "fulltext.txt").exists():
        return d
    d.mkdir(parents=True, exist_ok=True)
    meta, text, pdf = {"source": src}, "", None
    say = (lambda *a: None) if quiet else (lambda *a: print(*a, flush=True))
    aid = arxiv_id(src)
    local = Path(src).expanduser()
    if aid:
        say(f"  arXiv {aid}: metadata …")
        meta.update(arxiv_meta(aid))
        pdf = d / f"{aid.replace('/', '-')}.pdf"
        if not pdf.exists():
            say(f"  arXiv {aid}: downloading the PDF …")
            fetch(f"https://arxiv.org/pdf/{aid}", pdf, timeout=300)
    elif local.exists():
        meta["file"] = str(local.resolve())
        if local.suffix.lower() == ".pdf":
            pdf = local
        elif local.suffix.lower() in (".html", ".htm"):
            meta["title"], text = html_text(local.read_text("utf-8", "replace"))
        else:
            text = local.read_text("utf-8", "replace")
            m = re.search(r"^#\s+(.+)$", text, re.M)
            meta["title"] = m.group(1).strip() if m else local.stem.replace("-", " ").replace("_", " ")
    elif re.match(r"^https?://", src):
        meta["url"] = src
        say("  downloading …")
        tmp = d / "download.bin"
        data = fetch(src, tmp, timeout=300)
        if data[:5] == b"%PDF-" or src.lower().endswith(".pdf"):
            pdf = tmp.with_suffix(".pdf")
            tmp.rename(pdf)
        else:
            meta["title"], text = html_text(data.decode("utf-8", "replace"))
            tmp.unlink()
    else:
        raise SystemExit(f"✗ {src}: not a file, an arXiv id/URL or a URL")
    figs, pages = [], []
    if pdf:
        text = pdf_text(pdf)
        meta["pages"] = pdf_pages(pdf)
        say(f"  text: {meta['pages']} pages, {len(text.split())} words")
        figs = pdf_figures(pdf, d / "figures")
        caps = captions(text)
        covered = {f["page"] for f in figs}
        want = []
        for kind, n, cap, page, pgs in caps:
            for p in pgs:
                if p not in covered and p not in want:
                    want.append(p)
        pages = render_pages(pdf, want[:MAX_PAGES + 2], d / "figures")
        say(f"  figures: {len(figs)} raster, {len(pages)} page renders for vector figures")
    else:
        caps = captions(text)
    if len(text) > FULLTEXT_CAP:
        text = text[:FULLTEXT_CAP] + f"\n\n[… cut at {FULLTEXT_CAP} characters]"
    title = title_of(text, meta, local.stem if local.exists() else src)
    meta["title"] = title
    if not meta.get("year"):
        meta["year"] = year_of(text)
    (d / "fulltext.txt").write_text(text, "utf-8")
    (d / "meta.json").write_text(json.dumps({**meta, "figures": figs, "page_renders": pages}, ensure_ascii=False, indent=2), "utf-8")
    (d / "SOURCE.md").write_text(digest(meta, text, figs, pages, caps, title), "utf-8")
    return d


def meta_of(cache_dir):
    return json.loads((Path(cache_dir) / "meta.json").read_text("utf-8"))


def install(cache_dir, project):
    """Copy the digest, full text and figures into a reel project; credit the paper."""
    cache_dir, project = Path(cache_dir), Path(project).resolve()
    (project / "paper").mkdir(parents=True, exist_ok=True)
    for name in ("SOURCE.md", "fulltext.txt"):
        shutil.copyfile(cache_dir / name, project / "paper" / name)
    n = 0
    if (cache_dir / "figures").is_dir():
        (project / "assets" / "paper").mkdir(parents=True, exist_ok=True)
        for f in sorted((cache_dir / "figures").glob("*.png")):
            shutil.copyfile(f, project / "assets" / "paper" / f.name)
            n += 1
    meta = meta_of(cache_dir)
    line = f"- Figures and quotations from {citation(meta, meta.get('title', ''))}, reproduced for commentary and teaching.\n"
    credits = project / "CREDITS.md"
    prior = credits.read_text("utf-8") if credits.exists() else "# Credits\n\n"
    if line not in prior:
        credits.write_text(prior.rstrip("\n") + "\n" + line, "utf-8")
    return n


# ── check: does the storyboard answer the eight reviewer questions, with the core-idea block deep enough? ──
BEATS = ("hook", "problem", "prior", "insight", "example", "formal", "why", "evidence", "result", "limit", "verdict", "callback")
QUESTIONS = (("Q1 problem", ("problem",)), ("Q2 prior work", ("prior",)), ("Q3 key idea", ("insight",)),
             ("Q4 how it works", ("example", "formal")), ("Q5 why it works", ("why",)), ("Q6 evidence", ("evidence", "result")),
             ("Q7 limits", ("limit",)), ("Q8 so what", ("verdict", "callback")))
CORE = ("insight", "example", "formal", "why")
LEVELS = {
    "beginner": {"share": 0.40, "min": {"problem": 1, "insight": 1, "example": 2, "why": 1, "result": 1, "limit": 1, "verdict": 1}, "q": 8,
                 "optional": ("prior", "formal", "evidence")},
    "intermediate": {"share": 0.40, "min": {"problem": 1, "prior": 1, "insight": 1, "example": 2, "formal": 1, "why": 1, "result": 1, "limit": 1, "verdict": 1}, "q": 8,
                     "optional": ("evidence",)},
    "expert": {"share": 0.45, "min": {"problem": 1, "prior": 1, "insight": 1, "example": 3, "formal": 1, "why": 1, "evidence": 1, "result": 1, "limit": 1, "verdict": 1}, "q": 8,
               "optional": ()},
}


def beats_of(storyboard):
    """[(frame number, beat, duration_s)] from `- beat:` / `- duration:` per frame."""
    from reels_rsi.project import split_frames
    rows = []
    for num, fid, block in split_frames(storyboard):
        b = re.search(r"^-\s+beat:\s*([A-Za-z_-]+)", block, re.M)
        d = re.search(r"^-\s+duration:\s*([\d.]+)", block, re.M)
        rows.append((num, (b.group(1).lower() if b else ""), float(d.group(1)) if d else 0.0))
    return rows


def audience_of_project(project):
    m = re.search(r"^audience:\s*(.+)$", (Path(project) / "BRIEF.md").read_text("utf-8"), re.M) if (Path(project) / "BRIEF.md").exists() else None
    if m:
        from reels_rsi.agents import AUDIENCE_ALIASES
        for k, v in AUDIENCE_ALIASES.items():
            if k.lower() in m.group(1).lower():
                return v
    return "intermediate"

NOTATION = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z](?![A-Za-z0-9_])|[α-ωΑ-Ω]")
NOTATION_SKIP = {"a", "A", "I"}            # English articles / pronoun
NOTATION_PER_100 = 0.6                      # spoken notation tokens per 100 characters, over the whole script
NOTATION_PER_FRAME = 4
CORE_FRAME_MAX_S = 13.0


def notation_in_voice(script_text):
    """[(frame, hits, chars, tokens)] — notation a listener cannot parse by ear: isolated Latin letters
    ('T i', 'B i 等于六', 'W'), Greek letters (ρ, λ). Symbols belong on the screen, next to the object."""
    from reels_rsi.pipeline.tts import parse_script
    out = []
    for frame, text in parse_script(script_text):
        toks = [t for t in NOTATION.findall(text) if t not in NOTATION_SKIP]
        out.append((frame, len(toks), len(text), toks))
    return out


def check(project, audience=None):
    """Report + verdict. Returns (ok, lines)."""
    project = Path(project).resolve()
    sb = (project / "STORYBOARD.md").read_text("utf-8")
    level = audience or audience_of_project(project)
    rule = LEVELS[level]
    rows = beats_of(sb)
    total = sum(d for _, _, d in rows) or 1.0
    count, secs = {}, {}
    for _, b, d in rows:
        count[b] = count.get(b, 0) + 1
        secs[b] = secs.get(b, 0.0) + d
    out, problems = [f"reels paper check · audience {level} · {len(rows)} frames · {total:.0f}s"], []
    untagged = [n for n, b, _ in rows if b not in BEATS]
    if untagged:
        problems.append(f"frames without a valid `- beat:` ({', '.join(BEATS)}): {', '.join(map(str, untagged))}")
    for q, beats in QUESTIONS:
        n = sum(count.get(b, 0) for b in beats)
        s = sum(secs.get(b, 0.0) for b in beats)
        out.append(f"  {'✓' if n else '✗'} {q:16} {n} frame(s) · {s:5.1f}s · beats {'/'.join(beats)}")
        if not n and not all(b in rule["optional"] for b in beats):
            problems.append(f"{q} is not answered (no frame tagged {' / '.join(beats)})")
    for b, need in rule["min"].items():
        if count.get(b, 0) < need:
            problems.append(f"`{b}` needs ≥ {need} frame(s) at {level}, has {count.get(b, 0)}")
    core = sum(secs.get(b, 0.0) for b in CORE)
    share = core / total
    out.append(f"  core-idea block (insight+example+formal+why): {core:.0f}s = {share:.0%} of the reel (need ≥ {rule['share']:.0%})")
    if share < rule["share"]:
        problems.append(f"core-idea block is {share:.0%} of the reel — {level} needs ≥ {rule['share']:.0%}: lengthen the walkthrough "
                        "(more `example` frames on one stage) and `why`, not the results")
    ex = [i for i, (_, b, _) in enumerate(rows) if b == "example"]
    if ex and ex != list(range(ex[0], ex[0] + len(ex))):
        problems.append("`example` frames are not consecutive (frames "
                        + ", ".join(str(rows[i][0]) for i in ex) + ") — the walkthrough is one stage, in one run")
    stages = ("problem", "insight", "result", "limit")
    order = [b for _, b, _ in rows if b in stages]
    high = -1
    for b in order:
        if stages.index(b) < high:
            problems.append("order: problem → insight → result → limit (a reviewer's order), not " + " → ".join(order))
            break
        high = max(high, stages.index(b))
    script = project / "SCRIPT.md"
    if script.exists():
        rows_n = notation_in_voice(script.read_text("utf-8"))
        hits, chars = sum(r[1] for r in rows_n), sum(r[2] for r in rows_n) or 1
        per100 = hits * 100 / chars
        worst = sorted((r for r in rows_n if r[1]), key=lambda r: -r[1])[:3]
        out.append(f"  notation spoken aloud: {hits} token(s) in {chars} characters = {per100:.2f} per 100 (limit {NOTATION_PER_100})"
                   + ("" if not worst else " · worst: " + ", ".join(f"frame {f} ({n}: {' '.join(t[:6])})" for f, n, _, t in worst)))
        if per100 > NOTATION_PER_100 or any(r[1] >= NOTATION_PER_FRAME for r in rows_n):
            problems.append("the narration reads notation aloud (isolated letters / Greek) — say what the thing is (这棵记录树, 预算偏好, "
                            "并行上限) and put the symbol on screen next to it; keep ≤ "
                            f"{NOTATION_PER_100} per 100 characters and < {NOTATION_PER_FRAME} per frame")
    else:
        out.append("  (SCRIPT.md not written yet — the notation-in-voice check will run once it exists)")
    long = [(n, d) for n, b, d in rows if b in CORE and d > CORE_FRAME_MAX_S]
    if long:
        out.append("  ⚠ core-block frames over ~12 s (split them — more frames, not denser frames): "
                   + ", ".join(f"frame {n} {d:.0f}s" for n, d in long))
    if problems:
        out.append("✗ fix before `reels voice`:")
        out += [f"  - {p}" for p in problems]
    else:
        out.append("✓ all eight questions answered, core block deep enough — go on to `reels voice`")
    return not problems, out


def main(argv=None):
    if argv and argv[0] == "check":
        ap = argparse.ArgumentParser(prog="reels paper check", description="Does STORYBOARD.md answer the eight reviewer questions "
                                     "with a deep enough core-idea block? (reads `- beat:` tags and BRIEF.md `audience:`)")
        ap.add_argument("check")
        ap.add_argument("--project", default=".")
        ap.add_argument("--audience", default=None, choices=list(LEVELS))
        a = ap.parse_args(argv)
        ok, lines = check(a.project, a.audience)
        print("\n".join(lines))
        sys.exit(0 if ok else 1)
    ap = argparse.ArgumentParser(prog="reels paper", description="Digest a paper or document into a reel project: "
                                 "paper/SOURCE.md + paper/fulltext.txt + assets/paper/*.png (figures). "
                                 "`reels paper check --project .` verifies the storyboard answers the eight reviewer questions.")
    ap.add_argument("source", help="PDF path · arXiv id or URL · PDF URL · .md / .txt / .html · web page URL")
    ap.add_argument("--project", default=None, help="reel project to write into (default: the current directory)")
    ap.add_argument("--show", action="store_true", help="print the digest only")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and ingest again")
    a = ap.parse_args(argv)
    if a.refresh:
        shutil.rmtree(paths.papers() / source_key(a.source), ignore_errors=True)
    d = ingest(a.source)
    if a.show:
        print((d / "SOURCE.md").read_text("utf-8"))
        return
    project = Path(a.project or ".").resolve()
    if not (project / "hyperframes.json").exists():
        sys.exit(f"✗ {project} is not a reel project — `reels new` first, or `reels paper … --show`")
    n = install(d, project)
    meta = meta_of(d)
    print(f"✓ {meta.get('title', '')[:80]}\n  → {project / 'paper' / 'SOURCE.md'} · fulltext.txt · {n} image(s) in assets/paper/ · CREDITS.md\n"
          f"  cache: {d}")
