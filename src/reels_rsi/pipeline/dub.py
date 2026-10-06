"""Dub a finished reel into another language — narration, captions and the words on screen.

    reels dub <project> --lang en [--out DIR] [--voice …] [--translations FILE] [--model provider:model] [--render]

1. copies the project (frames, kits, storyboard; not renders, voice or run history) to <project>-<lang>
2. translates the spoken lines (SCRIPT.md) and every on-screen string in the frames and kits with one
   model call (role `retro`, or --model) — saved to <out>/.reels/dub.json; edit it and rerun with
   --translations to fix a term without asking the model again
3. voices each line fitted to the original line's duration (`reels voice --fit`), so the frames — timed
   to the original narration — stay in step; the speaking rate moves at most -20 %..+35 %
4. with --render: finalize + render

On-screen strings are found by script (CJK / Hangul runs) in text nodes and JS string literals, so the
source reel must be zh, ja or ko for automatic extraction; any source works with --translations.
Word order differs between languages, so a reveal can land a beat before or after its word — check
the contact sheet, and nudge cues in the frame if one matters.
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from reels_rsi import config, langs, llm

SKIP = {"renders", "snapshots", ".reels", "node_modules"}      # .hyperframes holds the preset's caption skin — keep it
REGEN = {"audio_meta.json", "caption_groups.json", "caption-overrides.json", "index.html"}
SRC_CHARS = r"[぀-ヿ㐀-鿿가-힣！-～]"
FEMALE_NAMES = ("Xiaoxiao", "Xiaoyi", "Xiaohan", "Ava", "Emma", "Aria", "Jenny", "Nanami", "SunHi", "Dalia",
                "Elvira", "Ximena", "Denise", "Eloise", "Vivienne")


def copy_project(src, out):
    if out.exists():
        sys.exit(f"✗ {out} exists — remove it or pass --out")
    def ignore(d, names):
        top = Path(d) == src
        return [n for n in names if (top and (n in SKIP or n in REGEN)) or
                (Path(d) == src / "assets" and n == "voice") or
                (Path(d) == src / "compositions" and n == "captions.html")]
    shutil.copytree(src, out, ignore=ignore)
    meta = src / ".reels" / "project.json"
    if meta.exists():
        (out / ".reels").mkdir(exist_ok=True)
        shutil.copyfile(meta, out / ".reels" / "project.json")


def script_lines(script):
    """{frame: spoken text} from SCRIPT.md (the 4-space-indented block under each '## Line … (Frame N)')."""
    out = {}
    for m in re.finditer(r"^## Line .*?\(Frame (\d+)\)\n(.*?)(?=^## |\Z)", script, re.M | re.S):
        spoken = " ".join(l[4:].strip() for l in m.group(2).splitlines() if l.startswith("    ") and l.strip())
        if spoken:
            out[int(m.group(1))] = spoken
    return out


def screen_strings(project, context=False):
    """Source-language strings drawn on screen: HTML text nodes and JS string literals in frames, overlays,
    kits. With context=True: {string: the whole line it sits in, tags stripped} — a fragment such as
    "的一半" after a formula only translates right when the model sees "S△AMN = S△ANB 的一半"."""
    found, where = set(), {}
    files = [*project.glob("compositions/frames/*.html"), *project.glob("compositions/overlays/*.html"),
             *project.glob("assets/*.js")]
    for f in files:
        text = re.sub(r"<style>.*?</style>", "", f.read_text("utf-8"), flags=re.S)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
        for seg in re.findall(r">([^<>]+)<", text) + re.findall(r"""(["'`])((?:(?!\1).)*?)\1""", text):
            s = (seg[1] if isinstance(seg, tuple) else seg).strip()
            if re.search(SRC_CHARS, s) and len(s) < 120:
                found.add(s)
        if context:
            for line in text.splitlines():
                plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", line)).strip()
                for s in found:
                    if s in line and s not in where and plain != s:
                        where[s] = plain[:140]
    ordered = sorted(found, key=len, reverse=True)
    return {s: where.get(s, "") for s in ordered} if context else ordered


PROMPT = """You are dubbing a short narrated lesson video into {lang_name} ({lang}).
Audience: {audience}.

Translate:
1. "lines" — the narration, one entry per frame. Natural teacher speech in {lang_name}, the same meaning
   and order of ideas, about the same length (each line is voiced into the original line's time; a much
   longer line gets sped up). Say numbers and formulas the way a teacher would say them aloud in {lang_name}.
   Keep point and shape names exactly (A, B, C, AMN, ANB …).
2. "strings" — words drawn on screen. Each one is replaced IN PLACE: the rest of its line (shown in
   brackets) stays as it is, so the translation must read correctly in that exact position — when the
   word order of {lang_name} differs, use notation instead (e.g. "S△AMN = S△ANB × ½"). Short, the
   conventional notation of {lang_name} school maths (units as cm², "S△ABC" stays). Keep every symbol,
   letter and number; translate only words. Never longer than needed — they must fit where the original sat.
   Never translate a string to nothing: a measure word or unit (份 "part", 块 "piece" …) carries meaning —
   use the closest word of {lang_name} even if it would usually be left out.

Narration (frame → original text, with the time it is spoken in and a length budget for {lang_name}):
{lines}

On-screen strings:
{strings}

Return JSON: {{"lines": {{"1": "…", "2": "…"}}, "strings": {{"<original>": "<translation>", …}}}}"""


def budget(lang, seconds):
    spec = langs.get(lang)
    return f"{seconds:.1f} s → at most about {int(seconds * spec['rate'] * 1.05)} {spec['unit']}"


def length(lang, text):
    unit = langs.get(lang)["unit"]
    if unit == "words":
        return len(re.findall(r"[\w'’-]+", text))
    if unit == "syllables":
        return len(langs.HANGUL.findall(text))
    return len(re.findall(r"[\w]", text))


def match_keys(table, originals):
    """Map the model's keys back to the exact on-screen strings — models quietly turn ？ into ? or ： into :."""
    norm = {unicodedata.normalize("NFKC", o).replace(" ", ""): o for o in originals}
    out = {}
    for k, v in table.items():
        o = k if k in originals else norm.get(unicodedata.normalize("NFKC", k).replace(" ", ""))
        if o:
            out[o] = v
    return out


def translate(lines, strings, lang, audience, spec, seconds):
    prompt = PROMPT.format(lang=lang, lang_name=langs.get(lang)["name"], audience=audience or "general",
                           lines="\n".join(f"{k} ({budget(lang, seconds[k])}): {v}" for k, v in sorted(lines.items())),
                           strings="\n".join(f"- {s}" + (f"   [line: {c}]" if c else "") for s, c in strings.items())
                           or "(none)")
    j = llm.complete_json(spec, prompt, max_tokens=8000)
    out = {"lines": {int(k): v for k, v in (j.get("lines") or {}).items()},
           "strings": match_keys(j.get("strings") or {}, list(strings))}
    emptied = [o for o, v in out["strings"].items() if re.search(SRC_CHARS, o) and not re.sub(r"[\s=:：+×÷()\d.]", "", v)]
    if emptied:      # a word that vanished (份 → "") breaks "5 份 = 3 cm²" — ask once more for just these
        fix = llm.complete_json(spec, PROMPT.format(lang=lang, lang_name=langs.get(lang)["name"], audience=audience or "general",
                                                    lines="(none — only the strings below)",
                                                    strings="\n".join(f"- {s}   [line: {strings.get(s, '')}]" for s in emptied))
                                + "\nEvery one of these MUST contain a word.", max_tokens=2000)
        out["strings"].update({k: v for k, v in match_keys(fix.get("strings") or {}, emptied).items() if v.strip()})
    skipped = [o for o in strings if o not in out["strings"]]
    if skipped:
        print("  ⚠ no translation for on-screen: " + " · ".join(skipped[:8]))
    missing = [k for k in lines if k not in out["lines"]]
    if missing:
        sys.exit(f"✗ the translation skipped frames {missing} — rerun, or write them into the translations file")
    return out


SHORTEN = """These {lang_name} narration lines for a lesson video are too long for the time they must be
spoken in. Rewrite each one shorter — same meaning, same facts and numbers, natural teacher speech, the
point and shape names unchanged — within its budget.

{lines}

Return JSON: {{"lines": {{"<frame>": "<shorter line>", …}}}}"""


def shorten(over, lang, spec):
    """over = {frame: (line, seconds)} → {frame: shorter line}"""
    prompt = SHORTEN.format(lang_name=langs.get(lang)["name"], lines="\n".join(
        f"{k} ({budget(lang, sec)}; now {length(lang, line)} {langs.get(lang)['unit']}): {line}"
        for k, (line, sec) in sorted(over.items())))
    j = llm.complete_json(spec, prompt, max_tokens=4000)
    return {int(k): v for k, v in (j.get("lines") or {}).items() if int(k) in over}


def write_script(project, src_script, lines, voice):
    def repl(m):
        frame = int(m.group(1))
        body = re.sub(r"(?m)^(    \S.*\n?)+", lambda _: "    " + lines[frame] + "\n", m.group(2), count=1)
        body = re.sub(r"(?m)^\*\*EN:\*\*.*\n?", "", body)                # bilingual lines belong to the source
        return m.group(0)[:m.start(2) - m.start(0)] + body
    script = re.sub(r"^## Line .*?\(Frame (\d+)\)\n(.*?)(?=^## |\Z)", repl, src_script, flags=re.M | re.S)
    script = re.sub(r"(?m)^\*\*Voice:\*\*.*$", f"**Voice:** {voice} (edge-tts)", script)
    (project / "SCRIPT.md").write_text(script, "utf-8")


def write_storyboard(project, lines):
    from reels_rsi.project import split_frames
    sb = (project / "STORYBOARD.md").read_text("utf-8")
    for num, fid, block in split_frames(sb):
        if num in lines:
            new = re.sub(r'(?m)^(-\s+voiceover:\s*).*$', lambda m: f'{m.group(1)}"{lines[num]}"', block, count=1)
            sb = sb.replace(block, new, 1)
    (project / "STORYBOARD.md").write_text(sb, "utf-8")


def apply_strings(project, table):
    files = [*project.glob("compositions/frames/*.html"), *project.glob("compositions/overlays/*.html"),
             *project.glob("assets/*.js")]
    for f in files:
        text = orig = f.read_text("utf-8")
        for src in sorted(table, key=len, reverse=True):
            text = text.replace(src, table[src])
        if text != orig:
            f.write_text(text, "utf-8")
    left = [s for s in table if s in "".join(f.read_text("utf-8") for f in files)]
    return left


def pick_voice(src_script, lang, voice):
    if voice:
        return voice
    m = re.search(r"\*\*Voice:\*\*\s*(\S+)", src_script)
    female = bool(m and any(n in m.group(1) for n in FEMALE_NAMES))
    return langs.FEMALE[lang] if female else langs.get(lang)["voice"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reels dub", description="Dub a finished reel into another language.")
    ap.add_argument("project")
    ap.add_argument("--lang", required=True, choices=list(langs.LANGS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice", default=None, help="edge voice (default: the language's voice, same gender as the source)")
    ap.add_argument("--translations", default=None, help="a dub.json to use instead of asking a model")
    ap.add_argument("--model", default=None, help="provider:model for the translation (default: role retro)")
    ap.add_argument("--render", action="store_true", help="finalize and render when the voice is done")
    a = ap.parse_args(argv)

    src = Path(a.project).resolve()
    from reels_rsi.project import require_project
    require_project(src, need=("SCRIPT.md", "STORYBOARD.md", "audio_meta.json"))
    out = Path(a.out or f"{src}-{a.lang}").resolve()
    src_script = (src / "SCRIPT.md").read_text("utf-8")
    lines = script_lines(src_script)
    seconds = {v["frame"]: v["duration_s"] for v in json.loads((src / "audio_meta.json").read_text("utf-8"))["voices"]}
    strings = screen_strings(src, context=True)

    if a.translations:
        t = json.loads(Path(a.translations).read_text("utf-8"))
        tr = {"lines": {int(k): v for k, v in t["lines"].items()}, "strings": t.get("strings", {})}
    else:
        spec = a.model or config.role("retro")
        if not spec:
            sys.exit("✗ no model for the translation — pass --model provider:model or --translations FILE")
        aud = re.search(r"^audience:\s*(.+)$", (src / "STORYBOARD.md").read_text("utf-8"), re.M)
        print(f"▶ translating {len(lines)} lines + {len(strings)} on-screen strings → {a.lang} ({spec}) …", flush=True)
        tr = translate(lines, strings, a.lang, aud.group(1) if aud else "", spec, seconds)

    copy_project(src, out)
    (out / ".reels").mkdir(exist_ok=True)
    (out / ".reels" / "dub.json").write_text(json.dumps({"source": str(src), "lang": a.lang, **tr},
                                                         ensure_ascii=False, indent=2), "utf-8")
    voice = pick_voice(src_script, a.lang, a.voice)
    write_script(out, src_script, tr["lines"], voice)
    write_storyboard(out, tr["lines"])
    left = apply_strings(out, tr["strings"])
    print(f"✓ {out.name}: script + {len(tr['strings'])} on-screen strings translated → {out}")
    if left:
        print("  ⚠ still in the source language on screen: " + " · ".join(left[:8]))

    from reels_rsi.pipeline import tts
    fit = ["--lang", a.lang, "--voice", voice, "--fit", str(src / "audio_meta.json")]
    tts.main(["--project", str(out), *fit])
    voiced = {v["frame"]: v["duration_s"] for v in json.loads((out / "audio_meta.json").read_text("utf-8"))["voices"]}
    over = {k: (tr["lines"][k], seconds[k]) for k, d in voiced.items() if k in seconds and d > seconds[k] * 1.06}
    if over and not a.translations:
        print(f"▶ {len(over)} line(s) still too long even sped up — shortening frames {sorted(over)} …", flush=True)
        tr["lines"].update(shorten(over, a.lang, a.model or config.role("retro")))
        (out / ".reels" / "dub.json").write_text(json.dumps({"source": str(src), "lang": a.lang, **tr},
                                                             ensure_ascii=False, indent=2), "utf-8")
        write_script(out, src_script, tr["lines"], voice)
        write_storyboard(out, tr["lines"])
        tts.main(["--project", str(out), "--only", ",".join(map(str, sorted(over))), *fit])
    if a.render:
        from reels_rsi.project import cmd_finalize, cmd_render
        cmd_finalize([str(out)])
        cmd_render([str(out)])


if __name__ == "__main__":
    main()
