from types import SimpleNamespace

import pytest

from reels_rsi.rsi import lint

RULES = lint.load_rules()


@pytest.mark.parametrize("rule", RULES, ids=[r.RULE["id"] for r in RULES])
def test_rule_passes_its_examples(rule):
    for name, ok, detail in lint.test_rule(rule):
        assert ok, f"{rule.RULE['id']}/{name}: {detail}"


def doc(text, kind="kit", rel="assets/kit.js"):
    return SimpleNamespace(text=text, kind=kind, rel=rel, path=None)


def test_polygon_reverse_regression():
    """The Yuan reel's real bug: a clockwise ring followed by .reverse()."""
    ring = "const TERRITORY = [[73, 39], [95, 53], [132, 51], [140, 47], [120, 25], [100, 21], [80, 30], [73, 39]]"
    use = "\nconst path = d3.geoPath(proj);\npath({ type: \"Polygon\", coordinates: [TERRITORY] });"
    assert not lint.lint_docs([doc(ring + ";" + use)])
    hits = lint.lint_docs([doc(ring + ".reverse();" + use)])
    assert [h.rule for h in hits] == ["polygon-winding"]


def test_loop_parameters_are_not_repeated_targets():
    text = """<template><div id="root" data-composition-id="f01"></div><script>
    const tl = gsap.timeline({ paused: true });
    dots.forEach(function (c, i) { tl.fromTo(c, { opacity: 0 }, { opacity: 1, duration: 1 }, i); });
    more.forEach(function (c, i) { tl.fromTo(c, { opacity: 0 }, { opacity: 1, duration: 1 }, 3 + i); });
    window.__timelines["f01"] = tl;</script></template>"""
    assert not [h for h in lint.lint_docs([doc(text, "frame", "f01.html")]) if h.rule == "repeat-fromto"]


def test_user_rule_scaffold_loads(isolated_home):
    lint.cmd_rules(["new", "my-rule", "--lesson", "test lesson"])
    d = isolated_home / "rules" / "my-rule"
    assert (d / "rule.py").exists() and (d / "bad.html").exists()
    assert "my-rule" in [r.RULE["id"] for r in lint.load_rules()]


def test_broken_user_rule_is_skipped_not_fatal(isolated_home, capsys):
    d = isolated_home / "rules" / "broken"
    d.mkdir(parents=True)
    (d / "rule.py").write_text("RULE = {'id': 'broken'\n")          # syntax error
    ids = [r.RULE["id"] for r in lint.load_rules()]
    assert "broken" not in ids and "polygon-winding" in ids
    assert "failed to load" in capsys.readouterr().err


def test_screen_shapes_are_not_maps():
    car = "const outline = wobble([[-62, -22], [-62, -60], [52, -66], [62, -22], [-62, -22]], 2, 21);"
    assert not lint.lint_docs([doc(car)])


def test_code_shown_on_screen_is_not_linted():
    from types import SimpleNamespace
    html = ('<template><div class="pane">tl.fromTo(c, { opacity: 0.9 }, { opacity: 0 }, at);</div>\n'
            '<script>const tl = gsap.timeline({ paused: true }); window.__timelines["x"] = tl;</script></template>')
    view = lint.code_view(html)
    assert "opacity: 0.9" not in view and "gsap.timeline" in view and view.count("\n") == html.count("\n")
    rule = next(r for r in lint.load_rules() if r.RULE["id"] == "visible-from-state")
    assert rule.check(SimpleNamespace(text=view, raw=html, rel="f.html", kind="frame")) == []
