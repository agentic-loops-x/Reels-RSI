import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Every test gets its own ~/.reels so lessons/rules never leak between tests or into yours."""
    monkeypatch.setenv("REELS_HOME", str(tmp_path / "home"))
    for k in ("REELS_JUDGE", "REELS_RETRO", "REELS_HARNESS", "REELS_MODEL"):
        monkeypatch.delenv(k, raising=False)
    return tmp_path / "home"
