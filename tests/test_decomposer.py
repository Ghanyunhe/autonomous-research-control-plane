from __future__ import annotations

from controlplane.brain.decomposer import decompose_experiment
from controlplane.schemas.task_intent import TaskIntent
from controlplane.schemas.experiment_brief import ExperimentBrief


def test_decompose_single_worker_brief_creates_one_task() -> None:
    brief = ExperimentBrief(
        experiment_id="exp_11",
        objective="Run one bounded experiment",
        hypothesis_links=["h1"],
        inputs={"repo_path": "/tmp/repo", "artifact_refs": [], "dataset_refs": []},
        constraints={
            "max_runtime_minutes": 30,
            "max_api_cost_usd": 3.0,
            "allowed_backends": ["claude_code"],
        },
        deliverables=["metrics.json"],
        acceptance_criteria=["metrics.json exists"],
        decomposition_hint="single_worker",
        preferred_worker_profile="coder_plus_runner",
    )
    intent = TaskIntent(
        task_type="analysis",
        worker_preference="codex",
        acceptance_emphasis="scientific_validity",
        goal_hint="Summarize the successful outputs",
        focus_areas=["build_on_success"],
    )
    tasks = decompose_experiment(brief, intent)
    assert len(tasks) == 1
    assert tasks[0].task_type == "analysis"
    assert tasks[0].worker_requirements["backend"] == "codex"
    assert tasks[0].worker_requirements["skills"] == ["scientific_review"]


def test_decompose_multi_worker_serial_brief_creates_two_serial_tasks() -> None:
    brief = ExperimentBrief(
        experiment_id="exp_12",
        objective="Run a serial two-step experiment",
        hypothesis_links=["h1"],
        inputs={"repo_path": "/tmp/repo", "artifact_refs": [], "dataset_refs": []},
        constraints={
            "max_runtime_minutes": 30,
            "max_api_cost_usd": 3.0,
            "allowed_backends": ["claude_code", "codex"],
        },
        deliverables=["metrics.json"],
        acceptance_criteria=["metrics.json exists"],
        decomposition_hint="multi_worker_serial",
        preferred_worker_profile="coder_plus_runner",
    )
    intent = TaskIntent(
        task_type="analysis",
        worker_preference="any",
        acceptance_emphasis="scientific_validity",
        goal_hint="Review and then implement the next bounded step",
        focus_areas=["build_on_success"],
    )

    tasks = decompose_experiment(brief, intent)

    assert len(tasks) == 2
    assert tasks[0].task_id.endswith("_review")
    assert tasks[0].task_type == "analysis"
    assert tasks[0].worker_requirements["skills"] == ["scientific_review"]
    assert tasks[1].task_id.endswith("_impl")
    assert tasks[1].task_type == "code_and_run"
    assert tasks[1].worker_requirements["skills"] == ["repo_write", "experiment_execution"]


def test_decompose_repair_intent_marks_debugging_skills() -> None:
    brief = ExperimentBrief(
        experiment_id="exp_13",
        objective="Repair a previously failing bounded experiment",
        hypothesis_links=["h1"],
        inputs={"repo_path": "/tmp/repo", "artifact_refs": [], "dataset_refs": []},
        constraints={
            "max_runtime_minutes": 30,
            "max_api_cost_usd": 3.0,
            "allowed_backends": ["claude_code", "codex"],
        },
        deliverables=["metrics.json"],
        acceptance_criteria=["metrics.json exists"],
        decomposition_hint="single_worker",
        preferred_worker_profile="coder_plus_runner",
    )
    intent = TaskIntent(
        task_type="repair",
        worker_preference="claude_code",
        acceptance_emphasis="artifact_presence",
        goal_hint="Repair the broken execution path",
        focus_areas=["artifact_gap"],
    )

    tasks = decompose_experiment(brief, intent)

    assert len(tasks) == 1
    assert tasks[0].task_type == "repair"
    assert tasks[0].worker_requirements["skills"] == ["debugging", "repo_write", "experiment_execution"]
