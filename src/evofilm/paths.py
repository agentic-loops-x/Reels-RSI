"""Where things live.

PACKAGE  the installed package (presets, vendored HyperFrames scripts, bench topics, prompts)
SKILL    the agent skill (SKILL.md + references) — $EVOFILM_SKILL_DIR overrides it, which is how
         `evofilm bench --skill-dir` evaluates a candidate skill without installing it
HOME     per-user state: fonts, SFX library, geo cache, learned lessons, taste, rules, bench runs
         ($EVOFILM_HOME, default ~/.evofilm)
"""

import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
VENDOR = PACKAGE / "vendor" / "hyperframes"
PRESETS = PACKAGE / "presets"
PROMPTS = PACKAGE / "prompts"
BENCH_TOPICS = PACKAGE / "bench" / "topics.toml"
HF_VERIFIED = "0.8.121"   # the HyperFrames CLI version this release was verified on


def skill_dir() -> Path:
    env = os.environ.get("EVOFILM_SKILL_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if (PACKAGE / "skill" / "SKILL.md").exists():
        return PACKAGE / "skill"
    raise SystemExit("✗ evofilm skill directory not found (set EVOFILM_SKILL_DIR)")


def home() -> Path:
    h = Path(os.environ.get("EVOFILM_HOME", "~/.evofilm")).expanduser()
    h.mkdir(parents=True, exist_ok=True)
    return h


def fonts() -> Path:
    return home() / "fonts"


def sfx_lib() -> Path:
    return home() / "sfx"


def geo_cache() -> Path:
    return home() / "geo-cache"


def lessons(state: str = "accepted") -> Path:
    p = home() / "lessons" / state
    p.mkdir(parents=True, exist_ok=True)
    return p


def user_rules() -> Path:
    return home() / "rules"
