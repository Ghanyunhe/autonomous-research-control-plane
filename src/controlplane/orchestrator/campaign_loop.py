from __future__ import annotations


def run_campaign_loop(campaign_dir, iteration_runner, max_rounds=100):
    decisions: list[str] = []
    for _ in range(max_rounds):
        decision = iteration_runner(campaign_dir)
        decisions.append(decision)
        if decision in {"STOP", "ESCALATE"}:
            break
    return decisions
