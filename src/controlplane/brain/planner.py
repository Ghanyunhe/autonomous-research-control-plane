from __future__ import annotations


def score_candidate(candidate: dict) -> float:
    return (
        0.50 * candidate["expected_information_gain"]
        + 0.35 * candidate["risk_reduction"]
        - 0.15 * candidate["cost_score"]
    )


def select_next_experiment(backlog: list[dict]) -> dict:
    if not backlog:
        raise ValueError("Backlog is empty")
    return max(backlog, key=score_candidate)
