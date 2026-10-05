import pytest

from evofilm.rsi import lessons, lint


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


def test_rule_lesson_already_built_in(isolated_home):
    p = lessons.add("A tween that starts visible must not render before its cue", "rule", "frame")
    lessons.accept(p.stem, rule_dir=str(lint.BUILTIN / "visible-from-state"))
    assert lessons.all_lessons("accepted")[0][2]["rule"] == "builtin:visible-from-state"
    assert not (isolated_home / "rules").exists()      # nothing copied, so the rule never runs twice


def test_user_rule_replaces_builtin_of_same_name(isolated_home):
    lint.cmd_rules(["new", "caption-band"])
    dirs = [d for d in lint.rule_dirs() if d.name == "caption-band"]
    assert dirs == [isolated_home / "rules" / "caption-band"]
