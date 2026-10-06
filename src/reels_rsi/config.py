"""Configuration: which model plays which role.

~/.reels/config.toml (user) and ./reels.toml (project, wins) — both optional:

  [agent]                 # the harness that directs films headlessly (make / bench / evolve)
  harness = "claude"      # claude | codex | gemini | opencode
  model = "opus"          # passed to the harness as-is (opus, sonnet, gpt-5.1, gemini-2.5-pro, deepseek/deepseek-chat …)

  [roles]                 # direct model calls (provider:model, see reels_rsi/llm.py)
  judge = "claude-cli:sonnet"   # scores contact sheets (needs vision)
  retro = "claude-cli:sonnet"   # turns a film's history into proposed lessons

Environment overrides: REELS_JUDGE, REELS_RETRO, REELS_HARNESS, REELS_MODEL.
"""

import argparse
import os
import shutil
import tomllib
from pathlib import Path

from reels_rsi import paths

DEFAULT_HARNESS_MODEL = {"claude": "opus", "codex": "gpt-5.1-codex", "gemini": "gemini-2.5-pro", "opencode": "anthropic/claude-sonnet-5-5"}


def load():
    cfg = {}
    for f in (paths.home() / "config.toml", Path.cwd() / "reels.toml"):
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
    env = os.environ.get(f"REELS_{name.upper()}")
    if env:
        return env
    spec = (load().get("roles") or {}).get(name)
    return spec or auto_judge()


def harness():
    a = load().get("agent") or {}
    h = os.environ.get("REELS_HARNESS") or a.get("harness")
    if not h:
        h = next((x for x in ("claude", "codex", "gemini", "opencode") if shutil.which(x)), "claude")
    m = os.environ.get("REELS_MODEL") or a.get("model") or DEFAULT_HARNESS_MODEL.get(h, "")
    return h, m


def set_value(key, value, project=False):
    """Set section.key in the user (or project) TOML. Minimal writer: two-level tables of strings."""
    path = Path.cwd() / "reels.toml" if project else paths.home() / "config.toml"
    data = tomllib.loads(path.read_text("utf-8")) if path.exists() else {}
    section, _, k = key.partition(".")
    if not k:
        raise SystemExit("✗ key must be section.name, e.g. roles.judge")
    data.setdefault(section, {})[k] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(data), "utf-8")


def _val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_val(x) for x in v) + "]"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(data, prefix=""):
    """Minimal TOML writer for config files: tables, nested tables ([providers.mylab]), scalars, lists."""
    out = []
    for sec, kv in data.items():
        if not isinstance(kv, dict):
            continue
        name = f"{prefix}{sec}"
        scalars = {k: v for k, v in kv.items() if not isinstance(v, dict)}
        if scalars or not any(isinstance(v, dict) for v in kv.values()):
            out.append(f"[{name}]")
            out += [f"{k} = {_val(v)}" for k, v in scalars.items()]
            out.append("")
        nested = {k: v for k, v in kv.items() if isinstance(v, dict)}
        if nested:
            out.append(dump(nested, name + "."))
    return "\n".join(out)
    print(f"✓ {path}: {section}.{k} = {value}")


def cmd_config(argv):
    ap = argparse.ArgumentParser(prog="reels config", description="Choose the models: agent harness + judge/retro roles.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    s = sub.add_parser("set"); s.add_argument("key"); s.add_argument("value"); s.add_argument("--project", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "set":
        set_value(a.key, a.value, a.project)
        return
    from reels_rsi import llm
    h, m = harness()
    print(f"agent  harness={h} model={m}  ({'found' if shutil.which(h) else 'NOT on PATH'})")
    for r in ("judge", "retro"):
        spec = role(r)
        ok, why = llm.available(spec) if spec else (False, "no model configured or detected")
        print(f"{r:6} {spec or '-':38} {'ok' if ok else '✗ ' + why}")
