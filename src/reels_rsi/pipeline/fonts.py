"""Ship the project's fonts as files in <project>/assets/fonts/.

The render machine is a clean headless Chrome: any family a frame names must ship as a file.
  · Noto Serif SC / Noto Sans SC (~20 MB each) are subset to exactly the characters the project
    shows — rerun after ANY copy change (SCRIPT.md, STORYBOARD.md, compositions/). Japanese and
    Korean reels are cut from Noto JP / KR instead (downloaded on first use) under the same names.
  · Instrument Serif / Archivo are converted whole when frame.md or a frame references them.
JetBrains Mono, Inter, Montserrat… are pre-bundled by HyperFrames and need nothing.

Usage: reels fonts --project <dir>
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from reels_rsi import paths
CJK = {"NotoSerifSC-VF.ttf": "NotoSerifSC-Subset.woff2", "NotoSansSC-VF.ttf": "NotoSansSC-Subset.woff2"}
LATIN = {
    "Instrument Serif": {"InstrumentSerif-Regular.ttf": "InstrumentSerif-Regular.woff2",
                         "InstrumentSerif-Italic.ttf": "InstrumentSerif-Italic.woff2"},
    "Archivo": {"Archivo-VF.ttf": "Archivo-Variable.woff2"},
}

FACE_CSS = """/* paste inside each frame's <style> — only the families the frame uses */
@font-face { font-family: "Noto Serif SC"; src: url("assets/fonts/NotoSerifSC-Subset.woff2") format("woff2"); font-weight: 200 900; }
@font-face { font-family: "Noto Sans SC"; src: url("assets/fonts/NotoSansSC-Subset.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Regular.woff2") format("woff2"); font-weight: 400; font-style: normal; }
@font-face { font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Italic.woff2") format("woff2"); font-weight: 400; font-style: italic; }
@font-face { font-family: "Archivo"; src: url("assets/fonts/Archivo-Variable.woff2") format("woff2"); font-weight: 100 900; }
"""


def subset(src, out, text=None):
    args = [sys.executable, "-m", "fontTools.subset", str(src), "--layout-features=*", "--flavor=woff2",
            f"--output-file={out}"]
    args.append(f"--text={text}" if text is not None else "--unicodes=*")
    subprocess.run(args, check=True)


def language(project):
    meta = project / "audio_meta.json"
    if meta.exists():
        lang = json.loads(meta.read_text("utf-8")).get("language")
        if lang:
            return lang
    from reels_rsi import langs
    script = project / "SCRIPT.md"
    return langs.detect(script.read_text("utf-8")) if script.exists() else "zh"


def source_fonts(lang):
    """The serif + sans Noto files whose glyphs this language needs; JP/KR download on first use."""
    from reels_rsi import langs
    from reels_rsi.env import FONT_BASE
    family = langs.FONT_FILES[langs.get(lang)["font"]]
    out = {}
    for style, (name, rel) in family.items():
        path = paths.fonts() / name
        if not path.exists():
            print(f"  downloading {name} (once, ~10 MB, SIL OFL) …", flush=True)
            try:
                with urllib.request.urlopen(FONT_BASE + rel, timeout=300) as r:
                    data = r.read()
            except OSError as e:
                sys.exit(f"✗ could not download {name} ({e}) — put it in {paths.fonts()} by hand")
            path.write_bytes(data)
        out[style] = path
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    project = Path(ap.parse_args(argv).project).resolve()
    lang = language(project)
    out = project / "assets" / "fonts"
    out.mkdir(parents=True, exist_ok=True)

    files = [project / "SCRIPT.md", project / "STORYBOARD.md", project / "frame.md",
             *project.glob("compositions/**/*.html")]
    corpus = "".join(f.read_text("utf-8") for f in files if f.exists())
    chars = set(corpus) | {chr(c) for c in range(0x20, 0x7F)} | set("，。？！；：、「」『』（）——…·“”‘’×÷±≈→←↑↓°")
    text = "".join(sorted(c for c in chars if c.isprintable()))
    if not (paths.fonts() / "NotoSansSC-VF.ttf").exists():
        sys.exit("✗ fonts missing — run `reels setup` first")
    # The subsets keep the family names "Noto Serif SC" / "Noto Sans SC" that presets, caption skins and
    # frames already use; for ja / ko they are cut from Noto JP / KR, so kanji take Japanese forms and
    # Hangul exists at all. font-faces.css also registers the real names (Noto Sans JP …).
    src = source_fonts(lang)
    subset(src["serif"], out / CJK["NotoSerifSC-VF.ttf"], text)
    subset(src["sans"], out / CJK["NotoSansSC-VF.ttf"], text)
    for family, faces in LATIN.items():
        if family in corpus:
            for src, dst in faces.items():
                subset(paths.fonts() / src, out / dst)
    faces = FACE_CSS
    # Mixed-language reels: Hangul in a non-Korean reel gets Korean glyphs under the same family names,
    # limited by unicode-range, so "Noto Sans SC" renders 한국어 too instead of tofu.
    from reels_rsi import langs
    hangul = "".join(sorted(set(langs.HANGUL.findall(text))))
    if hangul and lang != "ko":
        kr = source_fonts("ko")
        subset(kr["serif"], out / "NotoSerifKR-Fallback.woff2", hangul)
        subset(kr["sans"], out / "NotoSansKR-Fallback.woff2", hangul)
        rng = "U+1100-11FF, U+3130-318F, U+AC00-D7A3"
        faces += (f'@font-face {{ font-family: "Noto Serif SC"; src: url("assets/fonts/NotoSerifKR-Fallback.woff2") format("woff2"); font-weight: 200 900; unicode-range: {rng}; }}\n'
                  f'@font-face {{ font-family: "Noto Sans SC"; src: url("assets/fonts/NotoSansKR-Fallback.woff2") format("woff2"); font-weight: 100 900; unicode-range: {rng}; }}\n')
    fam = {"ja": "JP", "ko": "KR"}.get(lang)
    if fam:
        faces += (f'@font-face {{ font-family: "Noto Serif {fam}"; src: url("assets/fonts/NotoSerifSC-Subset.woff2") format("woff2"); font-weight: 200 900; }}\n'
                  f'@font-face {{ font-family: "Noto Sans {fam}"; src: url("assets/fonts/NotoSansSC-Subset.woff2") format("woff2"); font-weight: 100 900; }}\n')
    (out / "font-faces.css").write_text(faces, "utf-8")
    for f in sorted(out.glob("*.woff2")):
        print(f"  {f.name}: {f.stat().st_size / 1024:.0f} KB")
    print(f"✓ fonts ({lang}): {len(text)} chars subset → assets/fonts/")


if __name__ == "__main__":
    main()
