import json

from reels_rsi.pipeline import sfx

SB = """---
format: 16:9
duration: 9s
---
## Frame 1 — a

- duration: 5.0s
- src: compositions/frames/01-a.html
- sfx: pop@1.0

## Frame 2 — b

- duration: 4.0s
- src: compositions/frames/02-b.html
- sfx: chime@3.9, tick@0.5
"""


def test_frame_spans():
    assert sfx.frame_spans(SB) == {1: (0.0, 5.0), 2: (5.0, 4.0)}


def test_cues_past_the_reel_are_pulled_back(tmp_path, isolated_home, capsys):
    project = tmp_path / "reel"
    project.mkdir()
    (project / "STORYBOARD.md").write_text(SB, "utf-8")
    (project / "audio_meta.json").write_text(json.dumps({"voices": []}), "utf-8")
    sfx.cmd_cues(project)
    cues = {(c["frame"], c["file"].split("/")[-1]): c for c in json.loads((project / "audio_meta.json").read_text("utf-8"))["sfx"]}
    assert cues[(1, "pop.wav")]["offset_s"] == 1.0 and cues[(2, "tick.wav")]["offset_s"] == 0.5
    chime = cues[(2, "chime.wav")]
    assert chime["offset_s"] < 3.9 and 5.0 + chime["offset_s"] + chime["duration_s"] <= 9.0 + 0.01
    assert "moved to" in capsys.readouterr().out
