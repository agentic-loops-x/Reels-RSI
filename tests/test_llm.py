import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from evofilm import llm

SEEN = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append((self.path, {k.lower(): v for k, v in self.headers.items()}, body))
        if self.path.endswith("/v1/messages"):
            out = {"content": [{"type": "text", "text": 'Sure: ```json\n{"ok": true, "n": 3}\n```'}]}
        else:
            out = {"choices": [{"message": {"content": 'Here {"ok": true, "n": 4} done'}}]}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    SEEN.clear()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def png(tmp_path):
    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 16)
    return p


def test_split_and_availability(monkeypatch):
    assert llm.split("openrouter:qwen/qwen3-vl") == ("openrouter", "qwen/qwen3-vl")
    with pytest.raises(llm.LLMError):
        llm.split("nocolon")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert llm.available("deepseek:deepseek-chat") == (False, "DEEPSEEK_API_KEY not set")
    assert llm.available("ollama:qwen2.5vl")[0] is True
    assert llm.available("nope:x")[0] is False


def test_openai_compatible_with_image(server, monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", server + "/v1")
    out = llm.complete_json("openai:gpt-test", "score this", images=[png(tmp_path)], system="be strict")
    assert out == {"ok": True, "n": 4}
    path, headers, body = SEEN[-1]
    assert path == "/v1/chat/completions" and headers["authorization"] == "Bearer sk-test"
    assert body["messages"][0] == {"role": "system", "content": "be strict"}
    parts = body["messages"][1]["content"]
    assert parts[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_anthropic_native(server, monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ak-test")
    monkeypatch.setenv("EVOFILM_ANTHROPIC_BASE_URL", server)
    assert llm.complete_json("anthropic:claude-test", "hi", images=[png(tmp_path)]) == {"ok": True, "n": 3}
    path, headers, body = SEEN[-1]
    assert headers["x-api-key"] == "ak-test" and body["messages"][0]["content"][0]["type"] == "image"


def test_custom_provider_from_config(server, monkeypatch, isolated_home):
    isolated_home.mkdir(parents=True, exist_ok=True)
    (isolated_home / "config.toml").write_text(f'[providers.mylab]\nbase_url = "{server}/v1"\napi_key_env = "MYLAB_KEY"\n')
    monkeypatch.setenv("MYLAB_KEY", "k")
    assert llm.complete("mylab:m1", "hi").startswith("Here")
