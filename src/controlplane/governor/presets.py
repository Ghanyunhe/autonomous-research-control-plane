from __future__ import annotations


def build_policy_for_mode(mode: str) -> dict:
    if mode == "strong_autonomy":
        return {
            "autonomy": {
                "auto_continue": True,
                "auto_repair": True,
                "auto_pivot": True,
                "auto_finalize": True,
            },
            "escalation": {
                "require_human_for_pivot": False,
                "require_human_for_final_stop": False,
                "consecutive_failures_threshold": 5,
            },
            "budgets": {"max_experiments": 50},
        }
    if mode == "strict_review":
        return {
            "autonomy": {
                "auto_continue": False,
                "auto_repair": False,
                "auto_pivot": False,
                "auto_finalize": False,
            },
            "escalation": {
                "require_human_for_pivot": True,
                "require_human_for_final_stop": True,
                "consecutive_failures_threshold": 1,
            },
            "budgets": {"max_experiments": 20},
        }
    return {
        "autonomy": {
            "auto_continue": True,
            "auto_repair": True,
            "auto_pivot": False,
            "auto_finalize": False,
        },
        "escalation": {
            "require_human_for_pivot": True,
            "require_human_for_final_stop": True,
            "consecutive_failures_threshold": 3,
        },
        "budgets": {"max_experiments": 40},
    }
