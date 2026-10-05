"""Headless agent harnesses: hand the skill to any agent CLI and let it direct a film.

EvoFilm does not reimplement an agent. Directing a film means reading files, writing HTML,
running commands and looking at snapshots — Claude Code, Codex CLI, Gemini CLI and OpenCode all
do that already, each with its own model menu (OpenCode reaches DeepSeek, Qwen, Kimi, GLM and
local models). We pass them the same prompt and the same skill folder.

Verified: claude. The others follow each CLI's documented non-interactive mode. [untested]
"""

import json
import shutil
import subprocess
import time
from pathlib import Path

from evofilm import paths


def command(harness, model, prompt):
    if harness == "claude":
        cmd = ["claude", "-p", prompt, "--permission-mode", "bypassPermissions", "--output-format", "json"]
        return cmd + (["--model", model] if model else [])
    if harness == "codex":
        return ["codex", "exec", "--full-auto", "--skip-git-repo-check"] + (["--model", model] if model else []) + [prompt]
    if harness == "gemini":
        return ["gemini", "--yolo"] + (["-m", model] if model else []) + ["-p", prompt]
    if harness == "opencode":
        return ["opencode", "run"] + (["-m", model] if model else []) + [prompt]
    raise SystemExit(f"✗ unknown harness {harness!r} (claude | codex | gemini | opencode)")


def render_prompt(name, **kw):
    text = (paths.PROMPTS / f"{name}.md").read_text("utf-8")
    for k, v in kw.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def run(harness, model, prompt, cwd, log_path=None, env=None, timeout=7200):
    """Run one headless agent session. Returns {ok, seconds, cost_usd, turns, tail}."""
    if not shutil.which(harness):
        raise SystemExit(f"✗ `{harness}` is not installed / not on PATH")
    t0 = time.time()
    try:
        r = subprocess.run(command(harness, model, prompt), cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, env=env)
        out, err, code = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, code = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout", 124
    res = {"ok": code == 0, "seconds": round(time.time() - t0, 1), "cost_usd": None, "turns": None,
           "harness": harness, "model": model}
    if harness == "claude":
        try:
            j = json.loads(out)
            res.update(cost_usd=j.get("total_cost_usd"), turns=j.get("num_turns"), ok=not j.get("is_error", False))
            out = j.get("result", out)
        except ValueError:
            pass
    res["tail"] = (out or "")[-1500:] + (f"\n[stderr] {err[-800:]}" if err and code else "")
    if log_path:
        Path(log_path).write_text(f"$ {harness} ({model})\n\n{out}\n\n[stderr]\n{err}", "utf-8")
    return res
