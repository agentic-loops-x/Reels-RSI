import shutil
from pathlib import Path

import pytest

from reels_rsi.pipeline import paper

RAW = """Attention Is All You Need

Ashish Vaswani
Google Brain

Abstract
We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.
Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the
existing best results by over 2 BLEU.

1

Introduction

Recurrent neural networks have been firmly established as state of the art approaches.
Figure 1: The Transformer - model architecture.
\x0c2.1

Attention

An attention function can be described as mapping a query and a set of key-value pairs to an output.
Table 1: Maximum path lengths, per-layer complexity and minimum number of sequential operations
for different layer types.
3 Why Self-Attention
In this section we compare various aspects of self-attention layers to the recurrent layers.
28.4 EN-FR
4.33 BLEU (dev)
3 Scaled Dot-Product Attention
\x0c4

Conclusion

In this work, we presented the Transformer. Training took 3.5 days on eight GPUs [12].
References
[1] Jimmy Lei Ba. Layer normalization. 2016.
"""


def test_arxiv_id_forms():
    for s in ("1706.03762", "1706.03762v7", "arXiv:1706.03762", "https://arxiv.org/abs/1706.03762v7",
              "arxiv.org/pdf/1706.03762.pdf", "https://arxiv.org/html/1706.03762", "hep-th/9901001"):
        assert paper.arxiv_id(s) in ("1706.03762", "hep-th/9901001"), s
    for s in ("paper.pdf", "https://example.com/x.pdf", "notes.md", "2017"):
        assert paper.arxiv_id(s) is None, s
    assert paper.source_key("https://arxiv.org/abs/1706.03762") == "arxiv-1706.03762"


def test_sections_captions_numbers_pages():
    secs = paper.sections(RAW)
    assert [(n, t) for n, t, _ in secs] == [("", "Abstract"), ("1", "Introduction"), ("2.1", "Attention"),
                                            ("3", "Why Self-Attention"), ("4", "Conclusion"), ("", "References")]
    assert RAW[secs[1][2]:].startswith("1\n\nIntroduction")                            # offsets point at the heading
    ordered = paper.sections("1\n\nIntroduction\n\n2\n\nModel\n\n2.1\n\nEncoder\n\n2.2 Decoder\n\n3 Results\n\n2.3 Fake\n\n5 Appendix Notes\n")
    assert [n for n, _, _ in ordered] == ["1", "2", "2.1", "2.2", "3", "5"]            # 2.3 out of order; 5 = one heading lost
    caps = paper.captions(RAW)
    assert [(k, n, pg) for k, n, _, pg, _ in caps] == [("Figure", 1, 1), ("Table", 1, 2)]
    assert caps[1][2].startswith("Maximum path lengths") and caps[1][2].endswith("layer types.")   # continuation line joined
    assert caps[0][4] == [1, 2]            # caption at the foot of page 1 → the figure may be drawn on page 2
    assert caps[1][4] == [2]
    assert paper.caption_pages("a\nb\nc\n\x0cd\n", 0) == [1]
    nums = paper.number_sentences(RAW)
    assert any("28.4 BLEU" in s for s in nums) and any("3.5 days" in s for s in nums)
    assert not any("Layer normalization" in s for s in nums)          # a year alone is not a result


def test_digest_and_install_from_markdown(tmp_path):
    doc = tmp_path / "notes.md"
    doc.write_text("# Why ships float\n\nA ship displaces 50,000 tonnes of water, 10% more than its mass.\n\n"
                   "## Method\n\nWe measured it.\n", "utf-8")
    cache = paper.ingest(str(doc), cache=tmp_path / "cache", quiet=True)
    assert (cache / "SOURCE.md").exists() and (cache / "fulltext.txt").exists()
    src = (cache / "SOURCE.md").read_text("utf-8")
    assert src.startswith("# Source: Why ships float") and "50,000 tonnes" in src and "## How to use this" in src
    assert paper.ingest(str(doc), cache=tmp_path / "cache", quiet=True) == cache      # cached, no re-ingest
    project = tmp_path / "reel"
    project.mkdir()
    (project / "hyperframes.json").write_text("{}")
    n = paper.install(cache, project)
    assert n == 0 and (project / "paper" / "SOURCE.md").exists() and (project / "paper" / "fulltext.txt").exists()
    credits = (project / "CREDITS.md").read_text("utf-8")
    assert "Why ships float" in credits
    paper.install(cache, project)
    assert (project / "CREDITS.md").read_text("utf-8") == credits      # credit line written once


def test_html_text_strips_chrome():
    title, text = paper.html_text("<html><head><title>T</title><style>x{}</style></head><body><nav>menu</nav>"
                                  "<p>Hello <b>world</b>.</p><script>var a=1</script><p>Bye.</p></body></html>")
    assert title == "T" and "menu" not in text and "var a" not in text and "Hello world." in text and "Bye." in text


def test_citation_forms():
    assert paper.citation({"authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"], "year": "2017", "arxiv": "1706.03762"},
                          "Attention Is All You Need") == "Vaswani et al., 2017 — “Attention Is All You Need” (arXiv:1706.03762)"
    assert paper.citation({"authors": ["Ada Lovelace", "Charles Babbage"], "year": "1843"}, "Notes").startswith("Lovelace & Babbage, 1843")


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="poppler not installed")
def test_real_pdf_ingest(tmp_path):
    pdf = Path(__file__).resolve().parents[1] / "paper" / "main.pdf"
    if not pdf.exists():
        pytest.skip("repo paper PDF not present")
    cache = paper.ingest(str(pdf), cache=tmp_path / "cache", quiet=True)
    src = (cache / "SOURCE.md").read_text("utf-8")
    assert "Reels-RSI" in src and "Introduction" in src and "## Figures and tables" in src
    meta = paper.meta_of(cache)
    assert meta["pages"] > 5 and isinstance(meta["figures"], list) and meta["year"] == "2026"
    for f in meta["figures"]:
        assert (cache / "figures" / f["path"]).exists() and f["w"] >= paper.MIN_FIG[0]
    assert "cite on screen: “Reels-RSI" in src and "(2026)" in src


def test_arxiv_meta_falls_back_to_the_abs_page(monkeypatch):
    page = ('<meta name="citation_title" content="Dream-RSI: Recursive Self-Improvement"/>'
            '<meta name="citation_author" content="Zheng, Tong"/><meta name="citation_author" content="Wu, Xidong"/>'
            '<meta name="citation_date" content="2026/09/14"/>'
            '<blockquote class="abstract mathjax"><span class="descriptor">Abstract:</span>We study <b>RSI</b>.</blockquote>')

    def fake_fetch(url, dst, timeout=120):
        if "api/query" in url:
            raise OSError("HTTP Error 429")
        return page.encode()
    monkeypatch.setattr(paper, "fetch", fake_fetch)
    monkeypatch.setattr(paper.time, "sleep", lambda s: None)
    m = paper.arxiv_meta("2609.14858")
    assert m["title"].startswith("Dream-RSI") and m["year"] == "2026" and m["authors"] == ["Tong Zheng", "Xidong Wu"]
    assert m["abstract"] == "We study RSI." and m["url"].endswith("2609.14858")


def test_running_headers_are_not_sections_and_pipe_captions_count():
    txt = ("1. Introduction\nbody\n2 Paper Title: A Long Running Header\nmore\n2. Motivation\nbody\n"
           "3 Paper Title: A Long Running Header\nx\n3. Method\ny\nFigure 2 | Replay simulator. A policy explores.\n")
    assert [(n, t) for n, t, _ in paper.sections(txt)] == [("1", "Introduction"), ("2", "Motivation"), ("3", "Method")]
    assert [(k, n) for k, n, *_ in paper.captions(txt)] == [("Figure", 2)]


def test_header_on_its_own_line_after_a_page_number_is_not_a_section():
    txt = "1. Introduction\nbody\n\x0c2\nPaper Title Running Header\nmore\n2. Motivation\nbody\n\x0c3\nPaper Title Running Header\nx\n3. Method\ny\n"
    assert [(n, t) for n, t, _ in paper.sections(txt)] == [("1", "Introduction"), ("2", "Motivation"), ("3", "Method")]


SB_SHALLOW = """---
format: 16:9
---
## Frame 1 — hook
- beat: hook
- duration: 8s
## Frame 2 — idea
- beat: insight
- duration: 10s
## Frame 3 — loop
- beat: example
- duration: 10s
## Frame 4 — results
- beat: result
- duration: 40s
## Frame 5 — limit
- beat: limit
- duration: 8s
"""

SB_DEEP = SB_SHALLOW.replace("## Frame 3 — loop\n- beat: example\n- duration: 10s\n",
                             "## Frame 3 — step 1\n- beat: example\n- duration: 12s\n## Frame 4a — step 2\n- beat: example\n- duration: 12s\n"
                             "## Frame 4b — step 3\n- beat: example\n- duration: 12s\n## Frame 4c — formal\n- beat: formal\n- duration: 10s\n"
                             "## Frame 4d — why\n- beat: why\n- duration: 12s\n## Frame 4e — prior\n- beat: problem\n- duration: 6s\n").replace(
                             "## Frame 1 — hook\n- beat: hook\n", "## Frame 1 — hook\n- beat: problem\n")


def test_paper_check_rejects_a_shallow_storyboard_and_passes_a_deep_one(tmp_path):
    project = tmp_path / "reel"
    project.mkdir()
    (project / "BRIEF.md").write_text("---\naudience: 专业人士\n---\n", "utf-8")
    (project / "STORYBOARD.md").write_text(SB_SHALLOW, "utf-8")
    ok, lines = paper.check(project)
    text = "\n".join(lines)
    assert not ok and "audience expert" in text
    assert "Q2 prior work is not answered" in text and "`example` needs ≥ 3" in text and "core-idea block is 26%" in text
    (project / "STORYBOARD.md").write_text(SB_DEEP, "utf-8")
    ok, lines = paper.check(project, audience="intermediate")
    assert not ok and any("order:" in l for l in lines)          # a `problem` frame after the example beats is out of order
    deep = SB_DEEP.replace("## Frame 4e — prior\n- beat: problem\n- duration: 6s\n", "").replace(
        "## Frame 2 — idea\n", "## Frame 1b — prior\n- beat: prior\n- duration: 6s\n## Frame 2 — idea\n") + "## Frame 9 — verdict\n- beat: verdict\n- duration: 6s\n"
    (project / "STORYBOARD.md").write_text(deep, "utf-8")
    ok, lines = paper.check(project, audience="intermediate")
    assert ok, "\n".join(lines)
    assert paper.audience_of_project(project) == "expert"


def test_figures_never_match_a_caption_on_the_page_before():
    figs = [{"path": "fig-01.png", "page": 1, "w": 900, "h": 300}]
    caps = [("Figure", 1, "Overview.", 2, [2])]
    src = paper.digest({"title": "T"}, "x\n\x0cFigure 1: Overview.\n", figs, [{"path": "page-02.png", "page": 2}], caps, "T")
    assert "→ assets/paper/page-02.png" in src and "probably a logo" in src and "Figure 1** (p. 2)" in src


def test_notation_in_voice_counts_letters_and_greek_but_not_articles():
    script = ("# S\n\n## Line 1 — a (Frame 1)\n\n    取一棵记录好的树 T i，根 r 分数为零。B i 等于六，λ 乘平均轮数。\n\n"
              "## Line 2 — b (Frame 2)\n\n    这棵记录树里，每个节点是一次尝试，带一个分数。\n\n"
              "## Line 3 — c (Frame 3)\n\n    I think a tree is a record of attempts.\n")
    rows = paper.notation_in_voice(script)
    assert [(f, n) for f, n, _, _ in rows] == [(1, 6), (2, 0), (3, 0)]
    assert rows[0][3] == ["T", "i", "r", "B", "i", "λ"]


def test_paper_check_fails_on_spoken_notation(tmp_path):
    project = tmp_path / "reel"
    project.mkdir()
    (project / "BRIEF.md").write_text("---\naudience: expert\n---\n", "utf-8")
    deep = SB_DEEP.replace("## Frame 4e — prior\n- beat: problem\n- duration: 6s\n", "").replace(
        "## Frame 2 — idea\n", "## Frame 1b — prior\n- beat: prior\n- duration: 6s\n## Frame 2 — idea\n") + \
        "## Frame 9 — evidence\n- beat: evidence\n- duration: 6s\n## Frame 10 — verdict\n- beat: verdict\n- duration: 6s\n"
    (project / "STORYBOARD.md").write_text(deep, "utf-8")
    (project / "SCRIPT.md").write_text("## Line 1 — x (Frame 1)\n\n    树 T i 的根 r，分数 s v，并行 W 等于二，ρ 取五档，λ 惩罚。\n", "utf-8")
    ok, lines = paper.check(project)
    assert not ok and any("reads notation aloud" in l for l in lines)
    (project / "SCRIPT.md").write_text("## Line 1 — x (Frame 1)\n\n    这棵记录树的根没有分数，每个节点带一个分数，并行上限是二。\n", "utf-8")
    ok, lines = paper.check(project)
    assert ok, "\n".join(lines)
