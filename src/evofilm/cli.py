"""evofilm — the command line. `evofilm <command> --help` for any command."""

import importlib
import sys

from evofilm import __version__

# command → (module, function, one-line help); grouped for the help screen
COMMANDS = {
    "start": [
        ("setup", "evofilm.env", "cmd_setup", "one-time: fonts, SFX library, HyperFrames CLI"),
        ("install", "evofilm.env", "cmd_install", "add the skill to Claude Code / Codex / other agents"),
        ("doctor", "evofilm.env", "cmd_doctor", "check the environment, agents and models"),
        ("config", "evofilm.config", "cmd_config", "choose models: agent harness, judge, retro"),
        ("make", "evofilm.env", "cmd_make", "one sentence → rendered film, via any agent CLI"),
    ],
    "film": [
        ("new", "evofilm.project", "cmd_new", "scaffold a project from a preset"),
        ("voice", "evofilm.pipeline.tts", "main", "narration + word timings + music bed"),
        ("packets", "evofilm.project", "cmd_packets", "per-frame briefs for parallel frame workers"),
        ("finalize", "evofilm.project", "cmd_finalize", "fonts → captions → sfx → assemble → checks → snapshots"),
        ("render", "evofilm.project", "cmd_render", "render the MP4"),
        ("cover", "evofilm.pipeline.cover", "main", "cover / thumbnail"),
        ("srt", "evofilm.pipeline.srt", "main", "export subtitles (zh / en / bilingual)"),
        ("concat", "evofilm.project", "cmd_concat", "join chapter projects into one long film"),
    ],
    "assets": [
        ("fonts", "evofilm.pipeline.fonts", "main", "subset CJK fonts to the film's characters"),
        ("captions", "evofilm.pipeline.captions_cjk", "main", "karaoke captions (CJK-aware, bilingual)"),
        ("music", "evofilm.pipeline.music", "main", "procedural cut-aware music bed"),
        ("sfx", "evofilm.pipeline.sfx", "main", "procedural SFX library / storyboard cues"),
        ("geo", "evofilm.pipeline.geo", "main", "Natural Earth map layers for d3-geo"),
        ("commons", "evofilm.pipeline.commons", "main", "public-domain / CC images from Wikimedia, credited"),
        ("hanzi", "evofilm.pipeline.hanzi", "main", "stroke-order data for Chinese characters (笔顺)"),
        ("image", "evofilm.pipeline.gen_image", "main", "generated illustration layer (needs an image API key)"),
        ("analyze", "evofilm.project", "cmd_analyze", "study a reference video's pacing and look"),
        ("times", "evofilm.pipeline.frame_times", "main", "frame windows / review timestamps"),
        ("hf", "evofilm.project", "cmd_hf", "run the project-pinned HyperFrames CLI"),
    ],
    "self-improvement": [
        ("lint", "evofilm.rsi.lint", "cmd_lint", "check frames against every learned rule"),
        ("rules", "evofilm.rsi.lint", "cmd_rules", "list / test / scaffold rules"),
        ("feedback", "evofilm.rsi.lessons", "cmd_feedback", "record what the viewer said"),
        ("retro", "evofilm.rsi.retro", "cmd_retro", "turn a film's history into proposed lessons"),
        ("lessons", "evofilm.rsi.lessons", "cmd_lessons", "review, accept, reject, export lessons"),
        ("score", "evofilm.rsi.score", "cmd_score", "deterministic checks + vision judge (R1–R6)"),
        ("compare", "evofilm.rsi.score", "cmd_compare", "blind A/B between two versions of a film"),
        ("bench", "evofilm.rsi.bench", "cmd_bench", "EvoFilm Bench: fixed topics, any model, a leaderboard"),
        ("evolve", "evofilm.rsi.evolve", "cmd_evolve", "benchmark-gated rewrite of the skill itself"),
    ],
}
TABLE = {name: (mod, fn) for group in COMMANDS.values() for name, mod, fn, _ in group}


def usage():
    out = [f"evofilm {__version__} — an AI film director that evolves with every film\n",
           "usage: evofilm <command> [args]   ·   evofilm <command> --help\n"]
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
    sys.argv[0] = f"evofilm {cmd}"          # argparse's default prog → "usage: evofilm voice …"
    getattr(importlib.import_module(mod), fn)(sys.argv[2:])


if __name__ == "__main__":
    main()
