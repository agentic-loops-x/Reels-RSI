import json

import pytest

from reels_rsi.rsi import bench, evolve, score


def test_full_round_with_a_quota_pause(monkeypatch, isolated_home):
    state = {"quota_once": True}

    def fake_run(harness, model, prompt, cwd, log_path=None, env=None, timeout=0):
        if "improving the Reels-RSI skill" in prompt:            # the proposer edits the candidate copy
            cand = cwd / "skill"
            (cand / "SKILL.md").write_text((cand / "SKILL.md").read_text() + "\nNew: label at least 30 px.\n")
            (cand / "CHANGES.md").write_text("- labels ≥ 30 px (judge: tiny labels)\n")
            return {"ok": True, "tail": "edited", "seconds": 1, "cost_usd": None, "turns": 1}
        if "-cand" in str(cwd) and "en-seasons" in prompt and state["quota_once"]:
            state["quota_once"] = False
            return {"ok": False, "tail": "You've hit your session limit", "seconds": 1, "cost_usd": None, "turns": 1}
        return {"ok": True, "tail": "reel done", "seconds": 1, "cost_usd": None, "turns": 1}

    def fake_score_row(row, proj, judge):
        row.update(status="scored", composite=70.0, det=95.0, judge=60.0, rendered=True, notes=["n"], top_issues=[], findings=[])
        return row

    monkeypatch.setattr(bench.agents, "run", fake_run)
    monkeypatch.setattr(bench, "score_row", fake_score_row)
    monkeypatch.setattr(score, "compare", lambda a, b, spec, votes=3, detail=False: {"A": 1, "B": 2, "why": ["B: clearer", "A: x", "B: y"]})
    monkeypatch.setattr(score, "side_by_side", lambda a, b, out: None)

    with pytest.raises(SystemExit) as e:                       # candidate run hits the quota → paused, not failed
        evolve.cmd_evolve(["--yes", "--model", "sonnet", "--judge", "claude-cli:sonnet"])
    assert "paused" in str(e.value)
    eid = next(evolve.evolve_root().iterdir()).name
    evolve.cmd_evolve(["--resume", eid])                        # continues: candidate + holdout + verdict
    result = json.loads((evolve.evolve_root() / eid / "result.json").read_text())
    assert result["accepted"] and result["votes"] == [8, 4] and result["holdout_votes"] == [8, 4]
    report = (evolve.evolve_root() / eid / "report.md").read_text()
    assert "ACCEPTED" in report and "labels ≥ 30 px" in report and "votes base : cand" in report


def test_position_robust_verdict():
    # a judge that always picks the second-shown reel: 2-2 raw, and a tie — not a win for either side
    p = {"base": 2, "cand": 2, "picks": ["B", "A", "B", "A"], "first": ["A", "B", "A", "B"]}
    assert evolve.robust(p) == "tie"
    # the candidate also wins when shown first → candidate
    p = {"base": 1, "cand": 3, "picks": ["B", "B", "B", "A"], "first": ["A", "B", "A", "B"]}
    assert evolve.robust(p) == "cand"
    # no positions recorded (old state files) → fall back to the count
    assert evolve.robust({"base": 1, "cand": 2}) == "cand"
