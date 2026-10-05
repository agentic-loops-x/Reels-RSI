import json

from evofilm import project
from evofilm.pipeline import music, srt, tts
from evofilm.rsi import retro, runlog, score

STORYBOARD = """---
format: 9:16
duration: 20s
music: 历史 纪录
---

## Video direction
ink, slow push-ins

## Frame 1 — Hook
- scene: a crack runs through the map
- voiceover: 元朝为什么灭亡
- duration: 4s
- src: compositions/frames/01-hook.html

## Frame 2 — Flood
- scene: the river floods
- voiceover: 黄河决堤
- duration: 6s
- src: compositions/frames/02-flood.html
"""


def test_script_parsing_and_punct():
    lines = tts.parse_script("## Line 1 — hook (Frame 1)\n\n    元朝为什么，\n    灭亡？\n")
    assert lines == [(1, "元朝为什么，灭亡？")]
    words = tts.attach_punct([{"text": "元朝"}, {"text": "灭亡"}], "元朝，灭亡？")
    assert [w["text"] for w in words] == ["元朝，", "灭亡？"]


def test_sync_durations(tmp_path):
    sb = tmp_path / "STORYBOARD.md"
    sb.write_text(STORYBOARD)
    tts.sync_durations(sb, [{"frame": 1, "duration_s": 3.21}, {"frame": 2, "duration_s": 7.5}])
    assert "- duration: 3.21s" in sb.read_text() and "- duration: 7.5s" in sb.read_text()


def test_storyboard_helpers():
    assert music.detect_mood(STORYBOARD) == "cinematic"
    assert music.frame_starts(STORYBOARD) == ([0.0, 4.0], 10.0)
    frames = list(project.split_frames(STORYBOARD))
    assert [(n, fid) for n, fid, _ in frames] == [(1, "01-hook"), (2, "02-flood")]
    assert project.canvas(STORYBOARD) == "1080x1920"


def test_srt_shift_and_timestamps():
    assert srt.ts(3661.5) == "01:01:01,500"
    text, nxt = project.shift_srt("1\n00:00:01,000 --> 00:00:02,000\n你好\n", 10.0, 5)
    assert text.startswith("5\n00:00:11,000 --> 00:00:12,000\n你好") and nxt == 6


def fake_project(tmp_path, passes):
    p = tmp_path / "film"
    (p / "compositions/frames").mkdir(parents=True)
    (p / "STORYBOARD.md").write_text(STORYBOARD)
    for n, (html, rules) in enumerate(passes, 1):
        (p / "compositions/frames/01-hook.html").write_text(html)
        runlog.snapshot(p, n)
        runlog.append(p, {"event": "finalize", "n": n, "hf_ok": True, "hf_errors": 0, "hf_warnings": 0, "hf_findings": [],
                          "rules": rules, "frames": 2})
    return p


def test_retro_pairs_fix_with_diff(tmp_path):
    bug = [{"rule": "negative-zindex", "severity": "error", "file": "compositions/frames/01-hook.html", "line": 3, "message": "", "fix": ""}]
    p = fake_project(tmp_path, [("z-index: -1;", bug), ("z-index: 0;", [])])
    runlog.append(p, {"event": "feedback", "text": "太快了", "approve": False, "frame": None})
    ev = retro.evidence(p).read_text()
    assert "FIXED rule/negative-zindex" in ev
    assert "-z-index: -1;" in ev and "+z-index: 0;" in ev and "fixed: rule/negative-zindex" in ev
    assert "太快了" in ev


def test_deterministic_score(tmp_path):
    p = fake_project(tmp_path, [("ok", [])])
    runlog.append(p, {"event": "render", "ok": True, "duration_s": 10.0})
    m, s = score.deterministic(p)
    assert m["rendered"] and m["avg_shot_s"] == 5.0 and m["duration_err"] == 0.5
    assert s == 90.0   # −10 for missing the 20 s target by 50 %
    assert score.judge_score({"frames": [{"R1": 5, "R2": 4, "R3": 3, "R4": 4, "R5": 5, "R6": 3}]}) == 80.0


def test_require_project_fails_fast(tmp_path):
    import pytest
    with pytest.raises(SystemExit) as e:
        project.require_project(tmp_path)
    assert "not an EvoFilm project" in str(e.value)
    assert not any(tmp_path.iterdir())          # nothing created


def test_placeholders_keep_unbuilt_frames_on_the_timeline(tmp_path):
    p = tmp_path / "film"
    (p / "compositions/frames").mkdir(parents=True)
    (p / "STORYBOARD.md").write_text(STORYBOARD)
    (p / "compositions/frames/01-hook.html").write_text("<template>real</template>")
    assert project.placeholders(p) == ["02-flood"]
    ph = p / "compositions/frames/02-flood.html"
    assert project.is_placeholder(ph) and 'data-duration="6"' in ph.read_text() and 'data-width="1080"' in ph.read_text()
    assert 'id="ph-02-flood"' in ph.read_text()               # ids must not start with a digit
    assert project.placeholders(p) == []                       # idempotent, never overwrites


def test_band_top_follows_canvas():
    assert project.band_top("format: 1080x1920") == 1600 and project.band_top("format: 1920x1080") == 900


def test_chalk_preset_ships_its_kit(tmp_path):
    assert project.copy_preset_kit("chalk", tmp_path) == ["chalk-kit.js"]
    assert "window.ChalkKit" in (tmp_path / "assets" / "chalk-kit.js").read_text()
    assert project.copy_preset_kit("ink", tmp_path / "x") == []


def test_packets_list_kit_and_approved_frames(tmp_path):
    p = tmp_path / "film"
    (p / "compositions/frames").mkdir(parents=True)
    (p / "assets").mkdir()
    (p / "assets/film-kit.js").write_text("window.FilmKit = {};")
    sb = STORYBOARD.replace("- src: compositions/frames/01-hook.html", "- status: animated\n- src: compositions/frames/01-hook.html")
    (p / "STORYBOARD.md").write_text(sb)
    (p / "hyperframes.json").write_text("{}")
    (p / "compositions/frames/01-hook.html").write_text("<template>real</template>")
    project.cmd_packets(["--project", str(p)])
    role = (p / ".evofilm/packets/_role.md").read_text()
    assert "film-kit.js" in role and "01-hook.html" in role and "02-flood.html" not in role
    assert "y > 1600" in role                       # 9:16 caption band from the canvas


def test_judge_layout_and_mode():
    from evofilm.rsi import score
    assert score.layout_for(1080, 1920)[1] == 2 and score.layout_for(1920, 1080)[1] == 4
    sb = "- route: solve/geometry · svg\n- route: solve/formula\n- route: kinetic-type\n"
    assert score.film_mode(sb) == "solve"
    assert "Guiding the eye" in score.rubric("solve") and "Camera & life" in score.rubric("explain")
    assert score.film_mode("- route: science/sim\n") == "explain"


def test_bench_infra_errors_are_not_scores():
    from evofilm.rsi import bench
    assert bench.infra_error("You've hit your session limit · resets 10pm")
    assert bench.infra_error("Failed to authenticate: OAuth session expired")
    assert bench.infra_error("frame 03 failed lint: contrast") is None
    rows = [{"composite": 80.0}, {"composite": None, "status": "infra-error"}]
    assert bench.mean(rows) == 80.0
