import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Every test gets its own ~/.takeloop so lessons/rules never leak between tests or into yours."""
    monkeypatch.setenv("TAKELOOP_HOME", str(tmp_path / "home"))
    for k in ("TAKELOOP_JUDGE", "TAKELOOP_RETRO", "TAKELOOP_HARNESS", "TAKELOOP_MODEL"):
        monkeypatch.delenv(k, raising=False)
    return tmp_path / "home"
