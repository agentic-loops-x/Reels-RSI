"""Headless agent harnesses: hand the skill to any agent CLI and let it direct a reel.

Reels-RSI does not reimplement an agent. Directing a reel means reading files, writing HTML,
running commands and looking at snapshots — Claude Code, Codex CLI, Gemini CLI and OpenCode all
do that already, each with its own model menu (OpenCode reaches DeepSeek, Qwen, Kimi, GLM and
local models). We pass them the same prompt and the same skill folder.

Verified: claude. The others follow each CLI's documented non-interactive mode. [untested]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from reels_rsi import paths

# Variables a running Claude Code / desktop-app session sets for its own children. A nested `claude`
# that inherits them tries to borrow the host's login and fails ("OAuth session expired") even when
# the user's own CLI login is fine — so they are removed before any agent CLI is spawned.
# User settings such as CLAUDE_CODE_OAUTH_TOKEN, CLAUDE_CONFIG_DIR or ANTHROPIC_API_KEY are kept.
HOST_VARS = re.compile(r"^(CLAUDECODE|CLAUDE_PID|CLAUDE_EFFORT|CLAUDE_AGENT_SDK_\w+|CLAUDE_PREVIEW_\w+|"
                       r"CLAUDE_CODE_(ENTRYPOINT|SESSION_\w+|CHILD_SESSION|HOST_\w+|SDK_\w+|MESSAGING_\w+|"
                       r"OAUTH_SCOPES|EXECPATH|DESKTOP_\w+|ORGANIZATION_UUID|ACCOUNT_UUID|USER_EMAIL|EMIT_\w+|"
                       r"TERMINAL_\w+|REPORT_FINDINGS|EAGER_FLUSH|ENABLE_ASK_USER_QUESTION_TOOL|"
                       r"ENABLE_SDK_FILE_CHECKPOINTING|DISABLE_TERMINAL_TITLE|DISABLE_CRON))$")


def child_env(extra=None):
    """The environment for a spawned agent CLI: ours minus the host session's markers."""
    merged = {**os.environ, **(extra or {})}      # callers often pass a copy of os.environ — filter after merging
    env = {k: v for k, v in merged.items() if not HOST_VARS.match(k)}
    here = Path(sys.executable).parent             # the agent runs `reels …` — make it the same install as ours
    if (here / "reels").exists() and str(here) not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = str(here) + os.pathsep + env.get("PATH", "")
    return env


def claude_login():
    """(logged_in, detail) for the standalone `claude` CLI — the desktop app's login does not count."""
    if not shutil.which("claude"):
        return False, "`claude` not on PATH"
    try:
        r = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=30, env=child_env())
        j = json.loads(r.stdout)
    except (subprocess.SubprocessError, ValueError, OSError):
        return True, "login status unknown (older claude without `auth status`)"
    if j.get("loggedIn"):
        return True, j.get("authMethod", "logged in")
    return False, "the standalone `claude` CLI is not logged in — run `claude` in a terminal and type /login"


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


# Who the reel is for. One line the director reads; the full contract per level (what to cover, what to skip,
# terms, equations, numbers, visuals, pace) is in skill/references/paper.md "Audience levels" — it applies
# to every explainer, not only papers. Default lengths are for paper reels (`reels make --paper`).
AUDIENCES = {
    "beginner": {"zh": "小白 / 零基础", "line": "beginner (小白, no background): answer all eight reviewer questions (problem · prior · "
                 "idea · how · why · evidence · limits · so-what) in plain words with ONE everyday analogy carried through; walk the "
                 "mechanism step by step inside the analogy's scene (≥ 2 `example` frames, real names in brackets) — drop jargon and "
                 "notation, never the steps; ≤ 3 terms each glossed, no equations, 1–2 numbers said as comparisons; "
                 "`reels voice --rate -5%`", "length": 90},
    "intermediate": {"zh": "有基础", "line": "intermediate (有基础: knows the basics): answer all eight reviewer questions; walk one "
                     "concrete instance through the method on one stage (≥ 2 `example` frames), then the one equation the idea lives in; "
                     "terms by name after a one-line definition; prior approaches and where each fails; headline results with the "
                     "baselines named plus one cost number; the main figure as a plate then redrawn", "length": 150},
    "expert": {"zh": "专业人士", "line": "expert (专业人士, same field): answer all eight reviewer questions at review depth, but NESTED on the "
               "intermediate explanation — first the idea in words anchored to the nearest concept the field knows (a world model, "
               "a replay buffer, off-policy evaluation …) and the walkthrough of ONE central mechanism on one stage in plain words "
               "(≥ 3 `example` frames, each: what we want to find out → what the method does → what we see), THEN the precision "
               "layer: the equations with every symbol tied to the example, assumptions + the ablation behind the central choice, "
               "tasks/baselines/budget and where the comparison is weak, the exact delta over the nearest prior method, stated "
               "limits; symbols on screen never in the voice, ≤ 2 new quantities per frame, frames ≤ 12 s, secondary mechanisms "
               "named with their purpose only; default narration rate",
               "length": 270},
}
AUDIENCE_ALIASES = {"beginner": "beginner", "novice": "beginner", "小白": "beginner", "零基础": "beginner", "入门": "beginner",
                    "intermediate": "intermediate", "general": "intermediate", "有基础": "intermediate", "进阶": "intermediate",
                    "expert": "expert", "pro": "expert", "professional": "expert", "专业": "expert", "专业人士": "expert", "专家": "expert"}


def audience_of(name):
    key = AUDIENCE_ALIASES.get((name or "").strip().lower()) or AUDIENCE_ALIASES.get((name or "").strip())
    if not key:
        raise SystemExit(f"✗ audience {name!r} — beginner | intermediate | expert (小白 · 有基础 · 专业人士)")
    return key


def prompt_blocks(proj, quality="high", rsi=True, rounds=None, output="video", paper=None, paper_title="", skill=None,
                  audience="intermediate"):
    """The optional parts of prompts/make.md: how much review (RSI on/off), what to deliver (video / web /
    both), the audience, and the source material for a paper reel. `rounds` = finalize→review rounds at most."""
    rounds = rounds or (3 if rsi else 1)
    skill = skill or paths.skill_dir()
    aud = AUDIENCES[audience_of(audience)]
    audience_line = aud["line"] + f" — contract: {skill}/references/paper.md (Audience levels)"
    deliver = {"video": f"Finish with `reels render {proj} --quality {quality}`.",
               "web": f"Finish with `reels web {proj}` — the reel as a browser-playable page in renders/web/ (no MP4 render).",
               "both": f"Finish with `reels render {proj} --quality {quality}` and then `reels web {proj}` (a browser-playable page too)."}[output]
    reply = {"video": "the video path", "web": "the web folder (renders/web)", "both": "the video path and the web folder"}[output]
    if rsi:
        review = (f"   Review: after the frames, `reels finalize` → fix every error and warning → score the contact sheet on R1–R6 "
                  f"(`reels score` when a judge is configured) → fix → finalize again; at most {rounds} round(s).")
        learn = (f"Then `reels retro {proj} --evidence-only` and file at most 3 lessons with `reels lessons add` "
                 "(only things a future reel would get wrong too — not facts about this topic).")
    else:
        review = (f"   Fast mode — RSI off: do not run `reels lessons digest` or `reels score`; run `reels finalize` once, fix only "
                  f"the errors it reports (warnings may stay), finalize again; at most {rounds} round(s) in total, then deliver.")
        learn = "No retrospective, no lessons (RSI off)."
    source = ""
    if paper:
        source = (f"\n   Source material — this reel explains a paper/document{(': ' + paper_title) if paper_title else ''}.\n"
                  f"   Right after `reels new`, run `reels paper {paper} --project {proj}` (already ingested — it copies from the\n"
                  f"   cache): paper/SOURCE.md (read all of it first), paper/fulltext.txt (quote from it), assets/paper/*.png\n"
                  f"   (figures and page renders — plates for the frames). Recipe: {skill}/references/paper.md — the reel answers\n"
                  f"   the eight reviewer questions and the core-idea block (Q3–Q5: insight → worked example → formal → why) is at\n"
                  f"   least 40–45 % of it. Tag every storyboard frame with `- beat:`; after STORYBOARD.md run\n"
                  f"   `reels paper check --project {proj}` and fix the storyboard until it passes, before `reels voice`.\n"
                  f"   Every claim and number in the script comes from those files; never invent a result.")
    return {"review": review, "deliver": deliver, "learn": learn, "reply": reply, "source": source, "audience": audience_line}


def run(harness, model, prompt, cwd, log_path=None, env=None, timeout=7200):
    """Run one headless agent session. Returns {ok, seconds, cost_usd, turns, tail}."""
    if not shutil.which(harness):
        raise SystemExit(f"✗ `{harness}` is not installed / not on PATH")
    if harness == "claude":
        good, why = claude_login()
        if not good:
            raise SystemExit(f"✗ {why}")
    t0 = time.time()
    try:
        r = subprocess.run(command(harness, model, prompt), cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, env=child_env(env))
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
