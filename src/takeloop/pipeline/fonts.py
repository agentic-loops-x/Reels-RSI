"""Ship the project's fonts as files in <project>/assets/fonts/.

The render machine is a clean headless Chrome: any family a frame names must ship as a file.
  · Noto Serif SC / Noto Sans SC (~20 MB each) are subset to exactly the characters the project
    shows — rerun after ANY copy change (SCRIPT.md, STORYBOARD.md, compositions/).
  · Instrument Serif / Archivo are converted whole when frame.md or a frame references them.
JetBrains Mono, Inter, Montserrat… are pre-bundled by HyperFrames and need nothing.

Usage: takeloop fonts --project <dir>
"""

import argparse
import subprocess
import sys
from pathlib import Path

from takeloop import paths
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    project = Path(ap.parse_args(argv).project).resolve()
    out = project / "assets" / "fonts"
    out.mkdir(parents=True, exist_ok=True)

    files = [project / "SCRIPT.md", project / "STORYBOARD.md", project / "frame.md",
             *project.glob("compositions/**/*.html")]
    corpus = "".join(f.read_text("utf-8") for f in files if f.exists())
    chars = set(corpus) | {chr(c) for c in range(0x20, 0x7F)} | set("，。？！；：、「」『』（）——…·“”‘’×÷±≈→←↑↓°")
    text = "".join(sorted(c for c in chars if c.isprintable()))
    if not (paths.fonts() / "NotoSansSC-VF.ttf").exists():
        sys.exit("✗ fonts missing — run `takeloop setup` first")
    for src, dst in CJK.items():
        subset(paths.fonts() / src, out / dst, text)
    for family, faces in LATIN.items():
        if family in corpus:
            for src, dst in faces.items():
                subset(paths.fonts() / src, out / dst)
    (out / "font-faces.css").write_text(FACE_CSS, "utf-8")
    for f in sorted(out.glob("*.woff2")):
        print(f"  {f.name}: {f.stat().st_size / 1024:.0f} KB")
    print(f"✓ fonts: {len(text)} chars subset → assets/fonts/")


if __name__ == "__main__":
    main()
