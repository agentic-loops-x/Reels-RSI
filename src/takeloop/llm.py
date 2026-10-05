"""Any model, one call: complete(spec, prompt, images) → text.

A model is named `provider:model`:

  anthropic:claude-sonnet-5-5     ANTHROPIC_API_KEY  (native Messages API)
  openai:gpt-5.1                  OPENAI_API_KEY     (+ OPENAI_BASE_URL for any compatible server)
  gemini:gemini-2.5-pro           GEMINI_API_KEY     (Google's OpenAI-compatible endpoint)
  deepseek:deepseek-chat          DEEPSEEK_API_KEY   (text only — not a judge)
  qwen:qwen-vl-max                DASHSCOPE_API_KEY  (阿里云百炼 compatible mode)
  kimi:kimi-latest                MOONSHOT_API_KEY
  glm:glm-4.5v                    ZHIPUAI_API_KEY
  doubao:<endpoint-id>            ARK_API_KEY        (火山方舟)
  openrouter:<vendor/model>       OPENROUTER_API_KEY (hundreds of models behind one key)
  ollama:qwen2.5vl                local, no key      (http://localhost:11434)
  claude-cli:sonnet               your logged-in Claude Code (`claude -p`) — no API key needed
  codex-cli:<model> · gemini-cli:<model>   the other agent CLIs, same idea          [untested]

Custom OpenAI-compatible providers go in ~/.takeloop/config.toml:
  [providers.mylab]
  base_url = "https://llm.mylab.cn/v1"
  api_key_env = "MYLAB_KEY"
Stdlib only (urllib) — no SDKs to install.
"""

import base64
import json
import mimetypes
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

OPENAI_COMPAT = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY"),
    "kimi": ("https://api.moonshot.cn/v1", "MOONSHOT_API_KEY"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4", "ZHIPUAI_API_KEY"),
    "doubao": ("https://ark.cn-beijing.volces.com/api/v3", "ARK_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "ollama": ("http://localhost:11434/v1", None),
}
CLI = {"claude-cli": "claude", "codex-cli": "codex", "gemini-cli": "gemini"}


class LLMError(RuntimeError):
    pass


def split(spec):
    if ":" not in spec:
        raise LLMError(f"model spec must be provider:model, got {spec!r}")
    provider, model = spec.split(":", 1)
    return provider.strip().lower(), model.strip()


def providers():
    from takeloop import config
    table = dict(OPENAI_COMPAT)
    for name, p in (config.load().get("providers") or {}).items():
        table[name] = (p["base_url"], p.get("api_key_env"))
    return table


def available(spec) -> tuple[bool, str]:
    """Can this spec be called right now? (ok, why-not)"""
    try:
        provider, _ = split(spec)
    except LLMError as e:
        return False, str(e)
    if provider in CLI:
        return (bool(shutil.which(CLI[provider])), f"`{CLI[provider]}` not on PATH")
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY")), "ANTHROPIC_API_KEY not set"
    table = providers()
    if provider not in table:
        return False, f"unknown provider {provider!r}"
    env = table[provider][1]
    return (not env or bool(os.environ.get(env))), f"{env} not set"


def _post(url, payload, headers, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LLMError(f"{url} → HTTP {e.code}: {e.read()[:600].decode(errors='replace')}") from e


def _b64(path):
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return mime, base64.b64encode(Path(path).read_bytes()).decode()


def _anthropic(model, system, prompt, images, max_tokens):
    base = os.environ.get("TAKELOOP_ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    content = [{"type": "image", "source": {"type": "base64", "media_type": m, "data": d}} for m, d in map(_b64, images)]
    content.append({"type": "text", "text": prompt})
    data = _post(f"{base}/v1/messages", {"model": model, "max_tokens": max_tokens, "system": system or "",
                                         "messages": [{"role": "user", "content": content}]},
                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    return "".join(b.get("text", "") for b in data.get("content", []))


def _openai(provider, model, system, prompt, images, max_tokens):
    base, env = providers()[provider]
    if provider == "openai":
        base = os.environ.get("OPENAI_BASE_URL", base)
    content = [{"type": "image_url", "image_url": {"url": f"data:{m};base64,{d}"}} for m, d in map(_b64, images)]
    content.append({"type": "text", "text": prompt})
    msgs = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": content if images else prompt}]
    headers = {"Authorization": f"Bearer {os.environ[env]}"} if env else {}
    data = _post(f"{base.rstrip('/')}/chat/completions", {"model": model, "messages": msgs, "max_tokens": max_tokens}, headers)
    return data["choices"][0]["message"]["content"] or ""


def _cli(provider, model, system, prompt, images):
    """Delegate to an agent CLI the user is already logged into. Images are passed as file paths
    the agent opens with its own file-reading tool."""
    exe = CLI[provider]
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, img in enumerate(images):
            dst = Path(tmp) / f"image-{i}{Path(img).suffix}"
            shutil.copyfile(img, dst)
            files.append(dst)
        text = (system + "\n\n" if system else "") + prompt
        if files:
            text = ("First open and look at these image files with your Read tool: "
                    + ", ".join(str(f) for f in files) + "\n\n" + text)
        if provider == "claude-cli":
            cmd = [exe, "-p", text, "--model", model, "--allowedTools", "Read", "--output-format", "text"]
        elif provider == "codex-cli":
            cmd = [exe, "exec", "--model", model, "--skip-git-repo-check", text]
        else:
            cmd = [exe, "-m", model, "-p", text]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp, timeout=1800)
    if r.returncode:
        raise LLMError(f"{exe} failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[-800:]}")
    return r.stdout


def complete(spec, prompt, images=(), system="", max_tokens=4000) -> str:
    provider, model = split(spec)
    ok, why = available(spec)
    if not ok:
        raise LLMError(f"{spec}: {why}")
    if provider in CLI:
        return _cli(provider, model, system, prompt, list(images))
    if provider == "anthropic":
        return _anthropic(model, system, prompt, list(images), max_tokens)
    return _openai(provider, model, system, prompt, list(images), max_tokens)


def complete_json(spec, prompt, images=(), system="", max_tokens=4000):
    """complete() and parse the first JSON object in the reply (models wrap JSON in prose/fences)."""
    text = complete(spec, prompt + "\n\nReply with one JSON object only.", images, system, max_tokens)
    dec = json.JSONDecoder()
    for i, c in enumerate(text):
        if c == "{":
            try:
                return dec.raw_decode(text[i:])[0]
            except ValueError:
                continue
    raise LLMError(f"no JSON object in reply: {text[:300]}")
