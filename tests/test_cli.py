import subprocess
import sys

import pytest

from evofilm.cli import TABLE


@pytest.mark.parametrize("cmd", sorted(TABLE))
def test_every_command_has_help(cmd):
    r = subprocess.run([sys.executable, "-m", "evofilm", cmd, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]


def test_bench_dry_run_and_topics():
    r = subprocess.run([sys.executable, "-m", "evofilm", "bench", "run", "--dry-run", "--topics", "sci-rainbow"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "彩虹" in r.stdout and "SKILL.md" in r.stdout
    r = subprocess.run([sys.executable, "-m", "evofilm", "evolve", "--dry-run"], capture_output=True, text=True)
    assert r.returncode == 0 and "holdout" in r.stdout


def test_config_set_keeps_custom_providers(isolated_home):
    import tomllib
    from evofilm import config
    isolated_home.mkdir(parents=True, exist_ok=True)
    (isolated_home / "config.toml").write_text('[providers.mylab]\nbase_url = "https://x/v1"\napi_key_env = "K"\n')
    config.set_value("roles.judge", "mylab:vl")
    data = tomllib.loads((isolated_home / "config.toml").read_text())
    assert data["providers"]["mylab"]["base_url"] == "https://x/v1" and data["roles"]["judge"] == "mylab:vl"
