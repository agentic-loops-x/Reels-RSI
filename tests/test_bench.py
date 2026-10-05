from evofilm.rsi import bench


def test_quota_stop_then_resume(monkeypatch, tmp_path):
    calls = {"n": 0, "quota": True}

    def fake_run(harness, model, prompt, cwd, log_path=None, env=None, timeout=0):
        calls["n"] += 1
        if "鸡兔" in prompt and calls["quota"]:
            return {"ok": False, "tail": "You've hit your session limit · resets 10pm", "seconds": 1, "cost_usd": None, "turns": 1}
        return {"ok": True, "tail": "done", "seconds": 1, "cost_usd": None, "turns": 1}

    def fake_score_row(row, proj, judge):
        row.update(status="scored", composite=70.0, det=90.0, judge=60.0, rendered=True, notes=[], top_issues=[], findings=[])
        return row

    monkeypatch.setattr(bench.agents, "run", fake_run)
    monkeypatch.setattr(bench, "score_row", fake_score_row)
    ids = ["sci-rainbow", "solve-chicken-rabbit", "en-seasons"]
    s = bench.run(ids=ids, harness="claude", model="sonnet", judge="none:x", rid="t-run")
    assert not s["complete"] and s["missing"] == ["solve-chicken-rabbit", "en-seasons"]   # stopped, not scored as 0
    calls["quota"] = False
    s = bench.run(resume="t-run")
    assert s["complete"] and [r["topic"] for r in s["rows"]] == ["sci-rainbow", "solve-chicken-rabbit", "en-seasons"]
    assert s["mean"] == 70.0
