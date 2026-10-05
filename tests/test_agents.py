from evofilm import agents


def test_child_env_drops_host_session_but_keeps_user_auth(monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "1")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_SCOPES", "user:inference")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "user-token")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    env = agents.child_env({"EVOFILM_X": "1"})
    for k in ("CLAUDECODE", "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_OAUTH_SCOPES", "CLAUDE_CODE_SESSION_ID"):
        assert k not in env
    for k in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR", "ANTHROPIC_API_KEY", "EVOFILM_X", "PATH"):
        assert k in env


def test_command_shapes():
    assert agents.command("claude", "opus", "hi")[:2] == ["claude", "-p"]
    assert agents.command("opencode", "deepseek/deepseek-chat", "hi") == ["opencode", "run", "-m", "deepseek/deepseek-chat", "hi"]


def test_child_env_filters_a_passed_copy_of_environ(monkeypatch):
    import os
    monkeypatch.setenv("CLAUDECODE", "1")
    assert "CLAUDECODE" not in agents.child_env({**os.environ, "EVOFILM_SKILL_DIR": "/s"})
