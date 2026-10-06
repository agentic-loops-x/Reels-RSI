"""Languages a reel can be narrated and captioned in — one table, read by voice, captions, fonts, srt.

    zh 中文 · en English · ja 日本語 · ko 한국어      (+ zh-en bilingual captions via **EN:** lines)

Per language: the default Edge voice (and good alternatives), how captions are cut (`cjk` = no spaces,
grouped by character count; `spaced` = word groups with spaces), which Noto family ships the glyphs,
and a narration budget for scripts. `reels voice` writes the real durations back anyway — the budget
only keeps the first draft near the target length.
"""

import re

LANGS = {
    "zh": {"name": "中文", "voice": "zh-CN-YunxiNeural",
           "voices": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunjianNeural", "zh-CN-XiaoyiNeural"],
           "captions": "cjk", "font": "SC", "rate": 4.2, "unit": "characters"},
    "en": {"name": "English", "voice": "en-US-AndrewNeural",
           "voices": ["en-US-AvaNeural", "en-GB-RyanNeural", "en-US-EmmaNeural"],
           "captions": "spaced", "font": "SC", "rate": 2.6, "unit": "words"},
    "ja": {"name": "日本語", "voice": "ja-JP-KeitaNeural",
           "voices": ["ja-JP-NanamiNeural"],
           "captions": "cjk", "font": "JP", "rate": 5.0, "unit": "characters"},   # measured: kanji + kana
    "ko": {"name": "한국어", "voice": "ko-KR-InJoonNeural",
           "voices": ["ko-KR-SunHiNeural", "ko-KR-HyunsuMultilingualNeural"],
           "captions": "spaced", "font": "KR", "rate": 4.0, "unit": "syllables"},   # measured: Hangul blocks
}

# Noto families on Google Fonts (OFL). SC ships with `reels setup`; JP/KR download on first use.
FONT_FILES = {
    "SC": {"serif": ("NotoSerifSC-VF.ttf", "notoserifsc/NotoSerifSC%5Bwght%5D.ttf"),
           "sans": ("NotoSansSC-VF.ttf", "notosanssc/NotoSansSC%5Bwght%5D.ttf")},
    "JP": {"serif": ("NotoSerifJP-VF.ttf", "notoserifjp/NotoSerifJP%5Bwght%5D.ttf"),
           "sans": ("NotoSansJP-VF.ttf", "notosansjp/NotoSansJP%5Bwght%5D.ttf")},
    "KR": {"serif": ("NotoSerifKR-VF.ttf", "notoserifkr/NotoSerifKR%5Bwght%5D.ttf"),
           "sans": ("NotoSansKR-VF.ttf", "notosanskr/NotoSansKR%5Bwght%5D.ttf")},
}

HANGUL = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")
KANA = re.compile(r"[ぁ-ゖァ-ヺ]")
HAN = re.compile(r"[一-鿿]")


def detect(text):
    """Hangul → ko · kana → ja · Han → zh · otherwise en (a few kana or Hangul in a mostly-other text count)."""
    if len(HANGUL.findall(text)) >= 3:
        return "ko"
    if len(KANA.findall(text)) >= 3:
        return "ja"
    if HAN.search(text):
        return "zh"
    return "en"


def get(code):
    if code not in LANGS:
        raise SystemExit(f"✗ language {code!r} — supported: {', '.join(LANGS)}")
    return LANGS[code]
