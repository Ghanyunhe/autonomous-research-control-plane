from __future__ import annotations

from controlplane.schemas.task_packet import TaskPacket
from controlplane.schemas.task_intent import TaskIntent


def _skills_for_task(task_type: str) -> list[str]:
    if task_type == "analysis":
        return ["scientific_review"]
    if task_type == "repair":
        return ["debugging", "repo_write", "experiment_execution"]
    if task_type == "code_and_run":
        return ["repo_write", "experiment_execution"]
    return []


def decompose_experiment(brief, intent: TaskIntent) -> list[TaskPacket]:
    if brief.decomposition_hint == "single_worker":
        return [
            TaskPacket(
                task_id=f"task_{brief.experiment_id}_impl",
                experiment_id=brief.experiment_id,
                task_type=intent.task_type,
                goal=f"{brief.objective}\n\nExecution hint: {intent.goal_hint}",
                worker_requirements={
                    "backend": intent.worker_preference,
                    "strengths": ["coding"],
                    "skills": _skills_for_task(intent.task_type),
                    "tools_needed": ["shell", "repo_write"],
                },
                deliverables=brief.deliverables,
                acceptance_criteria=brief.acceptance_criteria,
                retry_policy={"max_retries": 2, "fallback_backend": "codex"},
            )
        ]

    if brief.decomposition_hint == "multi_worker_serial":
        return [
            TaskPacket(
                task_id=f"task_{brief.experiment_id}_review",
                experiment_id=brief.experiment_id,
                task_type="analysis",
                goal=(
                    f"{brief.objective}\n\n"
                    "Serial step 1: review context, inspect current evidence, and prepare the execution handoff.\n\n"
                    f"Execution hint: {intent.goal_hint}"
                ),
                worker_requirements={
                    "backend": "any",
                    "strengths": ["repo_navigation"],
                    "skills": _skills_for_task("analysis"),
                    "tools_needed": ["shell"],
                },
                deliverables=[],
                acceptance_criteria=[],
                retry_policy={"max_retries": 1, "fallback_backend": "codex"},
            ),
            TaskPacket(
                task_id=f"task_{brief.experiment_id}_impl",
                experiment_id=brief.experiment_id,
                task_type="code_and_run",
                goal=(
                    f"{brief.objective}\n\n"
                    "Serial step 2: implement the bounded execution step using the reviewed context."
                ),
                worker_requirements={
                    "backend": intent.worker_preference,
                    "strengths": ["coding"],
                    "skills": _skills_for_task("code_and_run"),
                    "tools_needed": ["shell", "repo_write"],
                },
                deliverables=brief.deliverables,
                acceptance_criteria=brief.acceptance_criteria,
                retry_policy={"max_retries": 2, "fallback_backend": "codex"},
            ),
        ]

    raise ValueError(f"Unsupported decomposition_hint: {brief.decomposition_hint}")
