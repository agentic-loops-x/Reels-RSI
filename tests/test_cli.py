import subprocess
import sys

import pytest

from takeloop.cli import TABLE


@pytest.mark.parametrize("cmd", sorted(TABLE))
def test_every_command_has_help(cmd):
    r = subprocess.run([sys.executable, "-m", "takeloop", cmd, "--help"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]


def test_bench_dry_run_and_topics():
    r = subprocess.run([sys.executable, "-m", "takeloop", "bench", "run", "--dry-run", "--topics", "sci-rainbow"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "彩虹" in r.stdout and "SKILL.md" in r.stdout
    r = subprocess.run([sys.executable, "-m", "takeloop", "evolve", "--dry-run"], capture_output=True, text=True)
    assert r.returncode == 0 and "holdout" in r.stdout
