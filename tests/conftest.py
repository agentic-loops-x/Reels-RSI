import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Every test gets its own ~/.evofilm so lessons/rules never leak between tests or into yours."""
    monkeypatch.setenv("EVOFILM_HOME", str(tmp_path / "home"))
    for k in ("EVOFILM_JUDGE", "EVOFILM_RETRO", "EVOFILM_HARNESS", "EVOFILM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    return tmp_path / "home"
