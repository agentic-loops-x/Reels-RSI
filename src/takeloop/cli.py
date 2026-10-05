"""takeloop — the command line. `takeloop <command> --help` for any command."""

import importlib
import sys

from takeloop import __version__

# command → (module, function, one-line help); grouped for the help screen
COMMANDS = {
    "start": [
        ("setup", "takeloop.env", "cmd_setup", "one-time: fonts, SFX library, HyperFrames CLI"),
        ("install", "takeloop.env", "cmd_install", "add the skill to Claude Code / Codex / other agents"),
        ("doctor", "takeloop.env", "cmd_doctor", "check the environment, agents and models"),
        ("config", "takeloop.config", "cmd_config", "choose models: agent harness, judge, retro"),
        ("make", "takeloop.env", "cmd_make", "one sentence → rendered film, via any agent CLI"),
    ],
    "film": [
        ("new", "takeloop.project", "cmd_new", "scaffold a project from a preset"),
        ("voice", "takeloop.pipeline.tts", "main", "narration + word timings + music bed"),
        ("packets", "takeloop.project", "cmd_packets", "per-frame briefs for parallel frame workers"),
        ("finalize", "takeloop.project", "cmd_finalize", "fonts → captions → sfx → assemble → checks → snapshots"),
        ("render", "takeloop.project", "cmd_render", "render the MP4"),
        ("cover", "takeloop.pipeline.cover", "main", "cover / thumbnail"),
        ("srt", "takeloop.pipeline.srt", "main", "export subtitles (zh / en / bilingual)"),
        ("concat", "takeloop.project", "cmd_concat", "join chapter projects into one long film"),
    ],
    "assets": [
        ("fonts", "takeloop.pipeline.fonts", "main", "subset CJK fonts to the film's characters"),
        ("captions", "takeloop.pipeline.captions_cjk", "main", "karaoke captions (CJK-aware, bilingual)"),
        ("music", "takeloop.pipeline.music", "main", "procedural cut-aware music bed"),
        ("sfx", "takeloop.pipeline.sfx", "main", "procedural SFX library / storyboard cues"),
        ("geo", "takeloop.pipeline.geo", "main", "Natural Earth map layers for d3-geo"),
        ("commons", "takeloop.pipeline.commons", "main", "public-domain / CC images from Wikimedia, credited"),
        ("hanzi", "takeloop.pipeline.hanzi", "main", "stroke-order data for Chinese characters (笔顺)"),
        ("image", "takeloop.pipeline.gen_image", "main", "generated illustration layer (needs an image API key)"),
        ("analyze", "takeloop.project", "cmd_analyze", "study a reference video's pacing and look"),
        ("times", "takeloop.pipeline.frame_times", "main", "frame windows / review timestamps"),
        ("hf", "takeloop.project", "cmd_hf", "run the project-pinned HyperFrames CLI"),
    ],
    "self-improvement": [
        ("lint", "takeloop.rsi.lint", "cmd_lint", "check frames against every learned rule"),
        ("rules", "takeloop.rsi.lint", "cmd_rules", "list / test / scaffold rules"),
        ("feedback", "takeloop.rsi.lessons", "cmd_feedback", "record what the viewer said"),
        ("retro", "takeloop.rsi.retro", "cmd_retro", "turn a film's history into proposed lessons"),
        ("lessons", "takeloop.rsi.lessons", "cmd_lessons", "review, accept, reject, export lessons"),
        ("score", "takeloop.rsi.score", "cmd_score", "deterministic checks + vision judge (R1–R6)"),
        ("compare", "takeloop.rsi.score", "cmd_compare", "blind A/B between two versions of a film"),
        ("bench", "takeloop.rsi.bench", "cmd_bench", "TakeLoop Bench: fixed topics, any model, a leaderboard"),
        ("evolve", "takeloop.rsi.evolve", "cmd_evolve", "benchmark-gated rewrite of the skill itself"),
    ],
}
TABLE = {name: (mod, fn) for group in COMMANDS.values() for name, mod, fn, _ in group}


def usage():
    out = [f"takeloop {__version__} — an AI film director that gets better with every take\n",
           "usage: takeloop <command> [args]   ·   takeloop <command> --help\n"]
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
    getattr(importlib.import_module(mod), fn)(sys.argv[2:])


if __name__ == "__main__":
    main()
