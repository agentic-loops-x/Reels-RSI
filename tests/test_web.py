import json

from reels_rsi.pipeline import web

INDEX = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="45.5" data-width="1080" data-height="1920">
      <div id="el-01" data-composition-src="compositions/frames/01-a.html" data-start="0" data-duration="5"></div>
      <audio id="el-01-voice" src="assets/voice/01.wav" data-start="0" data-duration="5"></audio>
    </div>
  </body>
</html>
"""


def fake_project(tmp_path):
    p = tmp_path / "reel"
    (p / "compositions" / "frames").mkdir(parents=True)
    (p / "assets" / "voice").mkdir(parents=True)
    (p / "assets" / "music").mkdir()
    (p / ".reels").mkdir()
    (p / "hyperframes.json").write_text("{}")
    (p / "index.html").write_text(INDEX, "utf-8")
    (p / "compositions" / "frames" / "01-a.html").write_text("<template></template>", "utf-8")
    (p / "compositions" / "frames" / "01-a.html.map").write_text("x")
    (p / "assets" / "voice" / "01.wav").write_bytes(b"RIFF")
    (p / "assets" / "music" / "raw.wav").write_bytes(b"RIFF")
    (p / ".reels" / "project.json").write_text(json.dumps({"title": "浮力"}), "utf-8")
    return p


def test_export_builds_a_static_player_folder(tmp_path, monkeypatch):
    pkg = tmp_path / "pkg" / "dist"
    pkg.mkdir(parents=True)
    (pkg / "hyperframes-player.global.js").write_text("player")
    (pkg / "hyperframe.runtime.iife.js").write_text("runtime")
    monkeypatch.setattr(web, "hf_package_dir", lambda version: pkg.parent)
    project = fake_project(tmp_path)
    out, size = web.export(project)
    assert out == project / "renders" / "web" and size > 0
    assert (out / "player.js").read_text() == "player" and (out / "runtime.js").read_text() == "runtime"
    comp = (out / "composition" / "index.html").read_text("utf-8")
    assert '<script src="../runtime.js"></script>' in comp and comp.index("runtime.js") < comp.index("<body>")
    assert (out / "composition" / "compositions" / "frames" / "01-a.html").exists()
    assert not (out / "composition" / "compositions" / "frames" / "01-a.html.map").exists()
    assert (out / "composition" / "assets" / "voice" / "01.wav").exists()
    assert not (out / "composition" / "assets" / "music").exists()          # the user's raw track stays home
    page = (out / "index.html").read_text("utf-8")
    assert "<title>浮力</title>" in page and 'src="composition/index.html"' in page and "aspect-ratio: 1080 / 1920" in page
    assert "46 s" in page
    runs = (project / ".reels" / "runs.jsonl").read_text("utf-8")
    assert '"event": "web"' in runs
    web.export(project)                                                       # re-export replaces, never nests
    assert not (out / "renders").exists()


def test_canvas_and_duration_defaults():
    assert web.canvas_of("<div id=\"root\">") == (1920, 1080) and web.duration_of("") == 0.0
    assert web.canvas_of(INDEX) == (1080, 1920) and web.duration_of(INDEX) == 45.5
