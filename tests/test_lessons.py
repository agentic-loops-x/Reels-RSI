import pytest

from takeloop.rsi import lessons, lint


def test_add_dedupe_accept_digest():
    p = lessons.add("Map labels must stay above y=900, because captions cover the band", "doc", "frame")
    assert p and p.parent.name == "inbox"
    assert lessons.add("map labels must stay above y=900 because captions cover that band", "doc", "frame") is None
    lessons.add("字幕再大一点", "taste", "all")
    assert lessons.digest("frame") == ""          # nothing accepted yet
    for st, path, meta, body in lessons.all_lessons("inbox"):
        lessons.accept(meta["id"])
    d = lessons.digest("frame")
    assert "y=900" in d and "字幕再大一点" in d and "taste" in d


def test_reject_moves_file():
    p = lessons.add("Never open with a definition, because hooks need tension", "doc", "director")
    lessons.reject(p.stem, "already in the skill")
    assert lessons.all_lessons("rejected")[0][2]["reason"] == "already in the skill"


def test_rule_lesson_needs_a_passing_rule(isolated_home, tmp_path):
    p = lessons.add("Flag the word FORBIDDEN in frames", "rule", "frame")
    with pytest.raises(SystemExit):
        lessons.accept(p.stem)                    # no --rule-dir
    lint.cmd_rules(["new", "forbidden-word"])
    d = isolated_home / "rules" / "forbidden-word"
    (d / "rule.py").write_text((d / "rule.py").read_text().replace("TODO-pattern", "FORBIDDEN"))
    (d / "bad.html").write_text("<p>FORBIDDEN</p>")
    (d / "good.html").write_text("<p>fine</p>")
    lessons.accept(p.stem, rule_dir=str(d))
    assert lessons.all_lessons("accepted")[0][2]["kind"] == "rule"


def test_export_excludes_taste_and_paths(tmp_path):
    for text, kind in (("Keep one hero per frame, because the eye needs a winner", "doc"), ("我喜欢暖色", "taste")):
        p = lessons.add(text, kind, "all", source="/Users/me/secret-project")
        lessons.accept(p.stem)
    lessons.export(tmp_path / "out")
    files = list((tmp_path / "out" / "lessons").glob("*.md"))
    assert len(files) == 1 and "secret-project" not in files[0].read_text()
