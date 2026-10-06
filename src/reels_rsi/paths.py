"""Where things live.

PACKAGE  the installed package (presets, vendored HyperFrames scripts, bench topics, prompts)
SKILL    the agent skill (SKILL.md + references) — $REELS_SKILL_DIR overrides it, which is how
         `reels bench --skill-dir` evaluates a candidate skill without installing it
HOME     per-user state: fonts, SFX library, geo cache, learned lessons, taste, rules, bench runs
         ($REELS_HOME, default ~/.reels)
"""

import os
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
VENDOR = PACKAGE / "vendor" / "hyperframes"
PRESETS = PACKAGE / "presets"
PROMPTS = PACKAGE / "prompts"
BENCH_TOPICS = PACKAGE / "bench" / "topics.toml"
HF_VERIFIED = "0.8.121"   # the HyperFrames CLI version this release was verified on


def skill_dir() -> Path:
    env = os.environ.get("REELS_SKILL_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if (PACKAGE / "skill" / "SKILL.md").exists():
        return PACKAGE / "skill"
    raise SystemExit("✗ reels skill directory not found (set REELS_SKILL_DIR)")


def home() -> Path:
    h = Path(os.environ.get("REELS_HOME", "~/.reels")).expanduser()
    old = Path("~/.evofilm").expanduser()              # the project was called EvoFilm before 0.1.0
    if "REELS_HOME" not in os.environ and not h.exists() and old.is_dir() and not old.is_symlink():
        old.rename(h)
        print(f"  (moved {old} → {h})", file=sys.stderr)
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
