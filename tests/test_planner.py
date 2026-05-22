from __future__ import annotations

from controlplane.brain.planner import score_candidate, select_next_experiment


def test_select_next_experiment_prefers_high_information_gain() -> None:
    backlog = [
        {"experiment_id": "exp_low", "expected_information_gain": 0.20, "risk_reduction": 0.10, "cost_score": 0.10},
        {"experiment_id": "exp_best", "expected_information_gain": 0.80, "risk_reduction": 0.50, "cost_score": 0.20},
    ]
    selected = select_next_experiment(backlog)
    assert selected["experiment_id"] == "exp_best"


def test_score_candidate_balances_information_risk_and_cost() -> None:
    score = score_candidate(
        {
            "experiment_id": "exp_a",
            "expected_information_gain": 0.60,
            "risk_reduction": 0.40,
            "cost_score": 0.20,
        }
    )

    assert round(score, 2) == 0.41


def test_select_next_experiment_prefers_risk_reduction_when_information_gain_is_close() -> None:
    backlog = [
        {"experiment_id": "exp_info_only", "expected_information_gain": 0.70, "risk_reduction": 0.10, "cost_score": 0.20},
        {"experiment_id": "exp_balanced", "expected_information_gain": 0.68, "risk_reduction": 0.50, "cost_score": 0.20},
    ]

    selected = select_next_experiment(backlog)
    assert selected["experiment_id"] == "exp_balanced"


def test_select_next_experiment_raises_for_empty_backlog() -> None:
    try:
        select_next_experiment([])
    except ValueError as exc:
        assert "Backlog is empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty backlog")
