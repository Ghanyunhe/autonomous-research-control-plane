from __future__ import annotations

from controlplane.governor.decisions import decide_next_action, make_governance_decision
from controlplane.governor.presets import build_policy_for_mode


def test_build_policy_for_strong_autonomy_allows_auto_pivot() -> None:
    policy = build_policy_for_mode("strong_autonomy")
    assert policy["autonomy"]["auto_pivot"] is True
    assert policy["escalation"]["require_human_for_final_stop"] is False


def test_decide_next_action_refines_on_rework() -> None:
    state = {
        "budget_status": {"experiments_run": 0},
        "failure_status": {"failure_streak": 0},
    }
    verification = {"status": "rework", "rework_priority": "medium"}
    policy = build_policy_for_mode("moderate_autonomy")
    assert decide_next_action(state, verification, policy) == "REFINE"


def test_decide_next_action_refines_high_priority_rework() -> None:
    state = {
        "budget_status": {"experiments_run": 0},
        "failure_status": {"failure_streak": 0},
    }
    verification = {"status": "rework", "rework_priority": "high"}
    policy = build_policy_for_mode("moderate_autonomy")
    assert decide_next_action(state, verification, policy) == "REFINE"


def test_make_governance_decision_returns_structured_stop_record() -> None:
    state = {
        "budget_status": {"experiments_run": 40},
        "failure_status": {"failure_streak": 0},
    }
    verification = {"status": "accept"}
    policy = build_policy_for_mode("moderate_autonomy")

    assert make_governance_decision(state, verification, policy) == {
        "decision": "STOP",
        "reason": "The campaign reached its configured experiment budget and must stop.",
        "basis": {
            "verification_status": "accept",
            "rework_priority": "none",
            "failure_streak": 0,
            "experiments_run": 40,
            "max_experiments": 40,
            "failure_threshold": 3,
        },
    }


def test_make_governance_decision_returns_structured_escalation_record() -> None:
    state = {
        "budget_status": {"experiments_run": 2},
        "failure_status": {"failure_streak": 3},
    }
    verification = {"status": "rework", "rework_priority": "medium"}
    policy = build_policy_for_mode("moderate_autonomy")

    assert make_governance_decision(state, verification, policy) == {
        "decision": "ESCALATE",
        "reason": "The campaign hit the consecutive failure threshold and should be escalated.",
        "basis": {
            "verification_status": "rework",
            "rework_priority": "medium",
            "failure_streak": 3,
            "experiments_run": 2,
            "max_experiments": 40,
            "failure_threshold": 3,
        },
    }
