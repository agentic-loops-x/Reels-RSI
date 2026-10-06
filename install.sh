#!/usr/bin/env bash
# One-line install:  curl -fsSL https://raw.githubusercontent.com/agentic-loops-x/Reels-RSI/main/install.sh | bash
set -euo pipefail
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
for c in node ffmpeg; do command -v "$c" >/dev/null || { echo "✗ please install $c first (macOS: brew install node ffmpeg)"; exit 1; }; done
uv tool install --force "git+https://github.com/agentic-loops-x/Reels-RSI"
reels setup
reels install
reels doctor
