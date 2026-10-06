# Choosing models

Reels-RSI has three roles. Each can be a different model.

| Role | Does | Needs | Set with |
|---|---|---|---|
| **director** | research, script, storyboard, frame code, review fixes | strong coding + tool use + some vision | the agent you run it in, or `reels config set agent.harness/agent.model` for headless `make`/`bench` |
| **judge** | scores frames R1–R6 from samples | vision | `reels config set roles.judge provider:model` |
| **retro** | turns a reel's history into lessons | good reasoning, text only | `reels config set roles.retro provider:model` |

## Harnesses (director)

| Harness | Models it reaches | Status |
|---|---|---|
| Claude Code (`claude`) | Opus / Sonnet / Haiku | ✅ reels made with it |
| Codex CLI (`codex`) | GPT-5.x / codex models | untested |
| Gemini CLI (`gemini`) | Gemini 2.5 / 3 | untested |
| OpenCode (`opencode`) | DeepSeek, Qwen, Kimi, GLM, OpenRouter, Ollama, … | untested |

Inside an interactive agent, pick the model in that agent as usual. A practical mix: a strong model
directs and reviews; frames are built in parallel by cheaper sub-agents (in Claude Code, sub-agents
can run on a different model).

Expect weaker models to need more review rounds — the rules catch the mechanical mistakes, and
`reels bench` tells you how much quality you trade for cost. Please share bench results.

## Providers (judge / retro)

`anthropic:` · `openai:` (+ `OPENAI_BASE_URL` for any compatible server) · `gemini:` · `qwen:`
(DashScope) · `deepseek:` (text only) · `kimi:` · `glm:` · `doubao:` · `openrouter:` · `ollama:` ·
`claude-cli:` (your logged-in Claude Code, no API key) · `codex-cli:` · `gemini-cli:`.
Custom endpoints:

```toml
# ~/.reels/config.toml
[providers.mylab]
base_url = "https://llm.mylab.cn/v1"
api_key_env = "MYLAB_KEY"

[roles]
judge = "mylab:vl-large"
```
