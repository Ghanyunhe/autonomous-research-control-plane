from __future__ import annotations

from controlplane.brain.objective_evolver import NextIterationPlan
from controlplane.schemas.task_intent import TaskIntent


def derive_task_intent(plan: NextIterationPlan) -> TaskIntent:
    if plan.strategy == "refine":
        return TaskIntent(
            task_type="repair",
            worker_preference="claude_code",
            acceptance_emphasis="artifact_presence",
            goal_hint=plan.reason,
            focus_areas=plan.focus_areas,
        )

    if plan.strategy == "hold":
        return TaskIntent(
            task_type="analysis",
            worker_preference="any",
            acceptance_emphasis="scientific_validity",
            goal_hint=plan.reason,
            focus_areas=plan.focus_areas,
        )

    if plan.strategy == "continue" and plan.focus_areas:
        return TaskIntent(
            task_type="analysis",
            worker_preference="any",
            acceptance_emphasis="scientific_validity",
            goal_hint=plan.reason,
            focus_areas=plan.focus_areas,
        )

    return TaskIntent(
        task_type="code_and_run",
        worker_preference="any",
        acceptance_emphasis="balanced",
        goal_hint=plan.reason,
        focus_areas=plan.focus_areas,
    )
