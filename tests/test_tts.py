import shutil

import pytest

from reels_rsi.pipeline import tts


def test_edge_compat_points_at_msedgeservices(monkeypatch):
    import edge_tts.communicate as comm
    import edge_tts.constants as const
    monkeypatch.setattr(const, "WSS_URL", "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=X")
    monkeypatch.setattr(comm, "WSS_URL", const.WSS_URL)
    monkeypatch.delenv("REELS_EDGE_ENDPOINT", raising=False)
    assert tts.edge_compat() is True
    assert "api.msedgeservices.com" in const.WSS_URL and comm.WSS_URL == const.WSS_URL
    assert "Ocp-Apim-Subscription-Key=" + const.TRUSTED_CLIENT_TOKEN in const.WSS_URL
    assert tts.edge_compat() is False                     # already there — left alone
    monkeypatch.setattr(const, "WSS_URL", "wss://speech.platform.bing.com/x")
    monkeypatch.setenv("REELS_EDGE_ENDPOINT", "legacy")
    assert tts.edge_compat() is False and "bing.com" in const.WSS_URL


def test_estimate_words_cjk_and_spaced():
    zh = tts.estimate_words("机器翻译，曾经要读。", 4.0, "zh")
    assert [w["text"] for w in zh] == list("机器翻译曾经要读")
    assert zh[0]["start"] == 0.05 and zh[-1]["end"] <= 4.0 and all(a["start"] < b["start"] for a, b in zip(zh, zh[1:]))
    assert zh[4]["start"] - zh[3]["start"] > zh[1]["start"] - zh[0]["start"]        # the comma adds a pause
    en = tts.estimate_words("Attention is all you need, said the paper.", 3.0, "en")
    assert [w["text"] for w in en] == ["Attention", "is", "all", "you", "need", "said", "the", "paper"]
    assert en[-1]["end"] <= 3.0
    glued = tts.attach_punct(tts.estimate_words("机器翻译，曾经要读。", 4.0, "zh"), "机器翻译，曾经要读。")
    assert glued[3]["text"] == "译，" and glued[-1]["text"] == "读。"


@pytest.mark.skipif(not shutil.which("say") or not shutil.which("ffmpeg"), reason="macOS say + ffmpeg")
def test_say_synth_writes_audio_and_timings(tmp_path):
    mp3 = tmp_path / "x.mp3"
    words = tts.say_synth("你好，世界。", None, mp3, "zh")
    assert mp3.exists() and mp3.stat().st_size > 1000
    assert [w["text"] for w in words] == ["你", "好", "世", "界"] and words[-1]["end"] <= tts.probe(mp3)
