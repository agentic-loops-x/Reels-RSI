"""reels — the command line. `reels <command> --help` for any command."""

import importlib
import sys

from reels_rsi import __version__

# command → (module, function, one-line help); grouped for the help screen
COMMANDS = {
    "start": [
        ("setup", "reels_rsi.env", "cmd_setup", "one-time: fonts, SFX library, HyperFrames CLI"),
        ("install", "reels_rsi.env", "cmd_install", "add the skill to Claude Code / Codex / other agents"),
        ("doctor", "reels_rsi.env", "cmd_doctor", "check the environment, agents and models"),
        ("config", "reels_rsi.config", "cmd_config", "choose models: agent harness, judge, retro"),
        ("make", "reels_rsi.env", "cmd_make", "one sentence → rendered film, via any agent CLI"),
    ],
    "film": [
        ("new", "reels_rsi.project", "cmd_new", "scaffold a project from a preset"),
        ("voice", "reels_rsi.pipeline.tts", "main", "narration + word timings + music bed"),
        ("packets", "reels_rsi.project", "cmd_packets", "per-frame briefs for parallel frame workers"),
        ("finalize", "reels_rsi.project", "cmd_finalize", "fonts → captions → sfx → assemble → checks → snapshots"),
        ("render", "reels_rsi.project", "cmd_render", "render the MP4"),
        ("cover", "reels_rsi.pipeline.cover", "main", "cover / thumbnail"),
        ("srt", "reels_rsi.pipeline.srt", "main", "export subtitles (zh / en / bilingual)"),
        ("concat", "reels_rsi.project", "cmd_concat", "join chapter projects into one long film"),
    ],
    "assets": [
        ("fonts", "reels_rsi.pipeline.fonts", "main", "subset CJK fonts to the film's characters"),
        ("captions", "reels_rsi.pipeline.captions_cjk", "main", "karaoke captions (CJK-aware, bilingual)"),
        ("music", "reels_rsi.pipeline.music", "main", "procedural cut-aware music bed"),
        ("sfx", "reels_rsi.pipeline.sfx", "main", "procedural SFX library / storyboard cues"),
        ("geo", "reels_rsi.pipeline.geo", "main", "Natural Earth map layers for d3-geo"),
        ("commons", "reels_rsi.pipeline.commons", "main", "public-domain / CC images from Wikimedia, credited"),
        ("hanzi", "reels_rsi.pipeline.hanzi", "main", "stroke-order data for Chinese characters (笔顺)"),
        ("image", "reels_rsi.pipeline.gen_image", "main", "generated illustration layer (needs an image API key)"),
        ("analyze", "reels_rsi.project", "cmd_analyze", "study a reference video's pacing and look"),
        ("times", "reels_rsi.pipeline.frame_times", "main", "frame windows / review timestamps"),
        ("hf", "reels_rsi.project", "cmd_hf", "run the project-pinned HyperFrames CLI"),
    ],
    "self-improvement": [
        ("lint", "reels_rsi.rsi.lint", "cmd_lint", "check frames against every learned rule"),
        ("rules", "reels_rsi.rsi.lint", "cmd_rules", "list / test / scaffold rules"),
        ("feedback", "reels_rsi.rsi.lessons", "cmd_feedback", "record what the viewer said"),
        ("retro", "reels_rsi.rsi.retro", "cmd_retro", "turn a film's history into proposed lessons"),
        ("lessons", "reels_rsi.rsi.lessons", "cmd_lessons", "review, accept, reject, export lessons"),
        ("score", "reels_rsi.rsi.score", "cmd_score", "deterministic checks + vision judge (R1–R6)"),
        ("compare", "reels_rsi.rsi.score", "cmd_compare", "blind A/B between two versions of a film"),
        ("bench", "reels_rsi.rsi.bench", "cmd_bench", "Reels-RSI Bench: fixed topics, any model, a leaderboard"),
        ("evolve", "reels_rsi.rsi.evolve", "cmd_evolve", "benchmark-gated rewrite of the skill itself"),
    ],
}
TABLE = {name: (mod, fn) for group in COMMANDS.values() for name, mod, fn, _ in group}


def usage():
    out = [f"reels {__version__} — an AI film director that evolves with every film\n",
           "usage: reels <command> [args]   ·   reels <command> --help\n"]
    for group, items in COMMANDS.items():
        out.append(f"{group}:")
        out += [f"  {name:10} {desc}" for name, _, _, desc in items]
        out.append("")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(usage())
        return
    if sys.argv[1] in ("-V", "--version"):
        print(__version__)
        return
    cmd = sys.argv[1]
    if cmd not in TABLE:
        sys.exit(f"✗ unknown command {cmd!r}\n\n{usage()}")
    mod, fn = TABLE[cmd]
    sys.argv[0] = f"reels {cmd}"          # argparse's default prog → "usage: reels voice …"
    getattr(importlib.import_module(mod), fn)(sys.argv[2:])


if __name__ == "__main__":
    main()
