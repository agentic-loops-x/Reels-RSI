"""Optional illustration generator — used only when an image API key is configured.   [UNTESTED: no key yet]

Code-drawn SVG tops out at clip-art for characters, creatures and painterly scenes; for those
the HyperFrames guidance is: generate the static art once, then animate code layers above it.

Providers (auto = first key found):
  openai  OPENAI_API_KEY   model: $OPENAI_IMAGE_MODEL  (default gpt-image-1)
  gemini  GEMINI_API_KEY   model: $GEMINI_IMAGE_MODEL  (default gemini-2.5-flash-image)

--key-out magenta: prompt asks for a flat #FF00FF background, then ffmpeg colorkey cuts it out
(more reliable than AI background removal on flat illustration). Always add restraint language
("minimal, lots of negative space") — image models over-fill the frame.

Usage: takeloop image --project <dir> --name earth --prompt "..." [--size 1536x1024] [--key-out magenta]
Exit code 2 = no provider configured (draw it with code instead).
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


def post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def openai_image(prompt, size):
    data = post("https://api.openai.com/v1/images/generations",
                {"model": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"), "prompt": prompt, "size": size, "n": 1},
                {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    return base64.b64decode(data["data"][0]["b64_json"])


def gemini_image(prompt, size):
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    data = post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"contents": [{"parts": [{"text": f"{prompt}\nAspect/size: {size}."}]}]},
                {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for part in data["candidates"][0]["content"]["parts"]:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            return base64.b64decode(inline["data"])
    raise RuntimeError("gemini returned no image part")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default="1536x1024")
    ap.add_argument("--provider", default="auto", choices=["auto", "openai", "gemini"])
    ap.add_argument("--key-out", default=None, choices=[None, "magenta"])
    a = ap.parse_args(argv)

    provider = a.provider
    if provider == "auto":
        provider = "openai" if os.environ.get("OPENAI_API_KEY") else "gemini" if os.environ.get("GEMINI_API_KEY") else None
    if not provider:
        print("no image provider configured (OPENAI_API_KEY / GEMINI_API_KEY) — draw this with code")
        sys.exit(2)

    prompt = a.prompt
    if a.key_out == "magenta":
        prompt += " Isolated subject on a perfectly flat solid #FF00FF magenta background, no shadow on the background."
    png = (openai_image if provider == "openai" else gemini_image)(prompt, a.size)

    out_dir = Path(a.project) / "public"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = out_dir / f"{a.name}.raw.png"
    raw.write_bytes(png)
    final = out_dir / f"{a.name}.png"
    if a.key_out == "magenta":
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                        "-vf", "colorkey=0xFF00FF:0.28:0.08,format=rgba", str(final)], check=True)
        raw.unlink()
    else:
        raw.rename(final)
    print(f"✓ {provider}: public/{final.name}")


if __name__ == "__main__":
    main()
