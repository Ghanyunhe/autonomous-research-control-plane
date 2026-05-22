from __future__ import annotations


def make_governance_decision(state: dict, verification: dict, policy: dict) -> dict:
    experiments_run = int(state["budget_status"]["experiments_run"])
    failure_streak = int(state["failure_status"]["failure_streak"])
    max_experiments = int(policy["budgets"]["max_experiments"])
    failure_threshold = int(policy["escalation"]["consecutive_failures_threshold"])
    verification_status = verification.get("status")
    rework_priority = verification.get("rework_priority", "none")

    if experiments_run >= max_experiments:
        decision = "STOP"
        reason = "The campaign reached its configured experiment budget and must stop."
    elif failure_streak >= failure_threshold:
        decision = "ESCALATE"
        reason = "The campaign hit the consecutive failure threshold and should be escalated."
    elif verification_status == "rework":
        decision = "REFINE"
        reason = "Verification requested rework before the campaign can continue."
    else:
        decision = "CONTINUE"
        reason = "Verification accepted the latest round, so the campaign can continue."

    return {
        "decision": decision,
        "reason": reason,
        "basis": {
            "verification_status": verification_status,
            "rework_priority": rework_priority,
            "failure_streak": failure_streak,
            "experiments_run": experiments_run,
            "max_experiments": max_experiments,
            "failure_threshold": failure_threshold,
        },
    }


def decide_next_action(state: dict, verification: dict, policy: dict) -> str:
    return make_governance_decision(state, verification, policy)["decision"]
