from __future__ import annotations

from controlplane.brain.decomposer import decompose_experiment
from controlplane.dispatcher.launchers.claude_code import ClaudeCodeLauncher
from controlplane.dispatcher.router import DEFAULT_WORKER_REGISTRY, choose_worker, create_launcher, resolve_launcher_for_task
from controlplane.schemas.experiment_brief import ExperimentBrief
from controlplane.schemas.task_intent import TaskIntent


def test_choose_worker_prefers_debugger_for_repair_task() -> None:
    registry = [
        {"worker_id": "coder", "backend": "codex", "enabled": True, "strengths": ["coding"], "trusted_for": ["code_and_run"]},
        {"worker_id": "debugger", "backend": "claude_code", "enabled": True, "strengths": ["debugging"], "trusted_for": ["repair"]},
    ]
    selected = choose_worker({"task_type": "repair"}, registry)
    assert selected["worker_id"] == "debugger"


def test_default_registry_routes_code_and_run_to_claude_code() -> None:
    selected = choose_worker({"task_type": "code_and_run"}, DEFAULT_WORKER_REGISTRY)
    assert selected["backend"] == "claude_code"


def test_choose_worker_respects_backend_preference_when_possible() -> None:
    selected = choose_worker(
        {"task_type": "analysis", "worker_requirements": {"backend": "codex"}},
        DEFAULT_WORKER_REGISTRY,
    )
    assert selected["backend"] == "codex"


def test_choose_worker_prefers_worker_with_required_skills() -> None:
    registry = [
        {
            "worker_id": "generic",
            "backend": "codex",
            "enabled": True,
            "strengths": ["coding"],
            "skills": [],
            "trusted_for": ["analysis"],
        },
        {
            "worker_id": "research_reviewer",
            "backend": "claude_code",
            "enabled": True,
            "strengths": ["repo_navigation"],
            "skills": ["scientific_review"],
            "trusted_for": ["analysis"],
        },
    ]

    selected = choose_worker(
        {"task_type": "analysis", "worker_requirements": {"skills": ["scientific_review"]}},
        registry,
    )

    assert selected["worker_id"] == "research_reviewer"


def test_choose_worker_raises_when_required_skills_are_unavailable() -> None:
    registry = [
        {
            "worker_id": "generic",
            "backend": "codex",
            "enabled": True,
            "strengths": ["coding"],
            "skills": [],
            "trusted_for": ["analysis"],
        }
    ]

    try:
        choose_worker(
            {"task_type": "analysis", "worker_requirements": {"skills": ["scientific_review"]}},
            registry,
        )
    except ValueError as exc:
        assert "skills" in str(exc)
    else:
        raise AssertionError("Expected ValueError when required skills are unavailable")


def test_choose_worker_can_consume_real_decomposed_analysis_task_skills() -> None:
    brief = ExperimentBrief(
        experiment_id="exp_router_1",
        objective="Review accepted evidence and propose next research step",
        hypothesis_links=["h1"],
        inputs={"repo_path": "/tmp/repo", "artifact_refs": [], "dataset_refs": []},
        constraints={
            "max_runtime_minutes": 30,
            "max_api_cost_usd": 3.0,
            "allowed_backends": ["claude_code", "codex"],
        },
        deliverables=["result_note.md"],
        acceptance_criteria=["result_note.md exists"],
        decomposition_hint="single_worker",
        preferred_worker_profile="coder_plus_runner",
    )
    intent = TaskIntent(
        task_type="analysis",
        worker_preference="any",
        acceptance_emphasis="scientific_validity",
        goal_hint="Review the current research evidence",
        focus_areas=["build_on_success"],
    )
    registry = [
        {
            "worker_id": "generic",
            "backend": "codex",
            "enabled": True,
            "strengths": ["coding"],
            "skills": [],
            "trusted_for": ["analysis"],
        },
        {
            "worker_id": "research_reviewer",
            "backend": "claude_code",
            "enabled": True,
            "strengths": ["repo_navigation"],
            "skills": ["scientific_review"],
            "trusted_for": ["analysis"],
        },
    ]

    task = decompose_experiment(brief, intent)[0].model_dump()
    selected = choose_worker(task, registry)

    assert task["worker_requirements"]["skills"] == ["scientific_review"]
    assert selected["worker_id"] == "research_reviewer"


def test_create_launcher_returns_claude_code_launcher() -> None:
    launcher = create_launcher({"backend": "claude_code"})
    assert isinstance(launcher, ClaudeCodeLauncher)


def test_resolve_launcher_for_task_uses_default_registry() -> None:
    launcher = resolve_launcher_for_task({"task_type": "code_and_run"})
    assert isinstance(launcher, ClaudeCodeLauncher)
