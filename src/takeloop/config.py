"""Configuration: which model plays which role.

~/.takeloop/config.toml (user) and ./takeloop.toml (project, wins) — both optional:

  [agent]                 # the harness that directs films headlessly (make / bench / evolve)
  harness = "claude"      # claude | codex | gemini | opencode
  model = "opus"          # passed to the harness as-is (opus, sonnet, gpt-5.1, gemini-2.5-pro, deepseek/deepseek-chat …)

  [roles]                 # direct model calls (provider:model, see takeloop/llm.py)
  judge = "claude-cli:sonnet"   # scores contact sheets (needs vision)
  retro = "claude-cli:sonnet"   # turns a film's history into proposed lessons

Environment overrides: TAKELOOP_JUDGE, TAKELOOP_RETRO, TAKELOOP_HARNESS, TAKELOOP_MODEL.
"""

import argparse
import os
import shutil
import tomllib
from pathlib import Path

from takeloop import paths

DEFAULT_HARNESS_MODEL = {"claude": "opus", "codex": "gpt-5.1-codex", "gemini": "gemini-2.5-pro", "opencode": "anthropic/claude-sonnet-5-5"}


def load():
    cfg = {}
    for f in (paths.home() / "config.toml", Path.cwd() / "takeloop.toml"):
        if f.exists():
            for k, v in tomllib.loads(f.read_text("utf-8")).items():
                cfg[k] = {**cfg.get(k, {}), **v} if isinstance(v, dict) else v
    return cfg


def auto_judge():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic:claude-sonnet-5-5"
    if shutil.which("claude"):
        return "claude-cli:sonnet"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai:gpt-5.1"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini:gemini-2.5-flash"
    if os.environ.get("DASHSCOPE_API_KEY"):
        return "qwen:qwen-vl-max"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter:google/gemini-2.5-flash"
    return None


def role(name):
    env = os.environ.get(f"TAKELOOP_{name.upper()}")
    if env:
        return env
    spec = (load().get("roles") or {}).get(name)
    return spec or auto_judge()


def harness():
    a = load().get("agent") or {}
    h = os.environ.get("TAKELOOP_HARNESS") or a.get("harness")
    if not h:
        h = next((x for x in ("claude", "codex", "gemini", "opencode") if shutil.which(x)), "claude")
    m = os.environ.get("TAKELOOP_MODEL") or a.get("model") or DEFAULT_HARNESS_MODEL.get(h, "")
    return h, m


def set_value(key, value, project=False):
    """Set section.key in the user (or project) TOML. Minimal writer: two-level tables of strings."""
    path = Path.cwd() / "takeloop.toml" if project else paths.home() / "config.toml"
    data = tomllib.loads(path.read_text("utf-8")) if path.exists() else {}
    section, _, k = key.partition(".")
    if not k:
        raise SystemExit("✗ key must be section.name, e.g. roles.judge")
    data.setdefault(section, {})[k] = value
    lines = []
    for sec, kv in data.items():
        if not isinstance(kv, dict):
            continue
        lines.append(f"[{sec}]")
        lines += [f'{kk} = "{vv}"' for kk, vv in kv.items() if not isinstance(vv, dict)]
        lines.append("")
    path.write_text("\n".join(lines), "utf-8")
    print(f"✓ {path}: {section}.{k} = {value}")


def cmd_config(argv):
    ap = argparse.ArgumentParser(prog="takeloop config", description="Choose the models: agent harness + judge/retro roles.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    s = sub.add_parser("set"); s.add_argument("key"); s.add_argument("value"); s.add_argument("--project", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "set":
        set_value(a.key, a.value, a.project)
        return
    from takeloop import llm
    h, m = harness()
    print(f"agent  harness={h} model={m}  ({'found' if shutil.which(h) else 'NOT on PATH'})")
    for r in ("judge", "retro"):
        spec = role(r)
        ok, why = llm.available(spec) if spec else (False, "no model configured or detected")
        print(f"{r:6} {spec or '-':38} {'ok' if ok else '✗ ' + why}")
