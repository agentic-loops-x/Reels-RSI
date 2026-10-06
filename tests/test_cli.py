import subprocess
import sys

import pytest

from reels_rsi.cli import TABLE


@pytest.mark.parametrize("cmd", sorted(TABLE))
def test_every_command_has_help(cmd):
    r = subprocess.run([sys.executable, "-m", "reels_rsi", cmd, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]


def test_bench_dry_run_and_topics():
    r = subprocess.run([sys.executable, "-m", "reels_rsi", "bench", "run", "--dry-run", "--topics", "sci-rainbow"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "彩虹" in r.stdout and "SKILL.md" in r.stdout
    r = subprocess.run([sys.executable, "-m", "reels_rsi", "evolve", "--dry-run"], capture_output=True, text=True)
    assert r.returncode == 0 and "holdout" in r.stdout


def test_config_set_keeps_custom_providers(isolated_home):
    import tomllib
    from reels_rsi import config
    isolated_home.mkdir(parents=True, exist_ok=True)
    (isolated_home / "config.toml").write_text('[providers.mylab]\nbase_url = "https://x/v1"\napi_key_env = "K"\n')
    config.set_value("roles.judge", "mylab:vl")
    data = tomllib.loads((isolated_home / "config.toml").read_text())
    assert data["providers"]["mylab"]["base_url"] == "https://x/v1" and data["roles"]["judge"] == "mylab:vl"


def test_wheel_ships_the_skill(tmp_path):
    """A symlink to the skill once made hatch drop src/reels_rsi/skill from the sdist — and so the wheel."""
    import shutil, subprocess, zipfile
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    if not shutil.which("uv"):
        import pytest
        pytest.skip("uv not installed")
    subprocess.run(["uv", "build", "-q", "--out-dir", str(tmp_path)], cwd=root, check=True)
    names = zipfile.ZipFile(next(tmp_path.glob("*.whl"))).namelist()
    for need in ("reels_rsi/skill/SKILL.md", "reels_rsi/skill/references/solve.md", "reels_rsi/presets/chalk/kit/chalk-kit.js",
                 "reels_rsi/rsi/rules/visible-from-state/bad.js", "reels_rsi/vendor/hyperframes/lib/transitions.json",
                 "reels_rsi/bench/topics.toml", "reels_rsi/prompts/retro.md"):
        assert need in names, need
    assert not [n for n in names if n.endswith(".test.mjs") or "__pycache__" in n]
