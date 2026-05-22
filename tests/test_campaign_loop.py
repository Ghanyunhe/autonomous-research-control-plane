from __future__ import annotations

from controlplane.orchestrator.campaign_loop import run_campaign_loop


def test_run_campaign_loop_stops_after_stop_decision(tmp_path) -> None:
    decisions = iter(["CONTINUE", "STOP"])

    def fake_iteration(_campaign_dir):
        return next(decisions)

    result = run_campaign_loop(tmp_path, iteration_runner=fake_iteration, max_rounds=5)
    assert result == ["CONTINUE", "STOP"]
