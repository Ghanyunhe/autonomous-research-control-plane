from __future__ import annotations

from pathlib import Path
import subprocess
from unittest.mock import patch

from controlplane.dispatcher.launchers.claude_code import ClaudeCodeLauncher
from controlplane.governor.decisions import make_governance_decision
from controlplane.orchestrator.iteration_loop import run_iteration
from controlplane.verifier.completion_judge import verify_completion


def test_run_iteration_returns_continue_for_successful_stubbed_flow(tmp_path) -> None:
    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_11",
            "objective": "Run one experiment",
            "deliverables": ["metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_1",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            }
        ],
        launcher=lambda task: {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["metrics.json"],
        },
        verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
        governor=lambda state, verification, policy: "CONTINUE",
    )
    assert decision == "CONTINUE"


def test_run_iteration_uses_launcher_object_and_injects_repo_path(tmp_path: Path) -> None:
    seen_task: dict = {}

    class FakeLauncher:
        def launch(self, task: dict) -> dict:
            seen_task.update(task)
            return {
                "task_id": task["task_id"],
                "status": "success",
                "deliverable_paths": [],
            }

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_12",
            "objective": "Run one experiment",
            "deliverables": [],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_2",
                "task_type": "code_and_run",
                "deliverables": [],
                "acceptance_criteria": [],
            }
        ],
        launcher=FakeLauncher(),
        verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
        governor=lambda state, verification, policy: "CONTINUE",
    )
    assert decision == "CONTINUE"
    assert seen_task["context_refs"]["repo_path"] == str(tmp_path)


def test_run_iteration_routes_with_default_launcher_factory(tmp_path: Path) -> None:
    seen: dict = {}

    class FakeLauncher:
        def launch(self, task: dict) -> dict:
            seen["task"] = task
            return {
                "task_id": task["task_id"],
                "status": "success",
                "deliverable_paths": [],
            }

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_13",
            "objective": "Route through default dispatcher",
            "deliverables": [],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_3",
                "task_type": "code_and_run",
                "deliverables": [],
                "acceptance_criteria": [],
            }
        ],
        launcher=None,
        launcher_factory=lambda task: FakeLauncher(),
        verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
        governor=lambda state, verification, policy: "CONTINUE",
    )
    assert decision == "CONTINUE"
    assert seen["task"]["task_type"] == "code_and_run"


def test_run_iteration_defaults_code_and_run_to_claude_launcher(tmp_path: Path) -> None:
    seen = {}

    def fake_launch(self, task: dict) -> dict:  # noqa: ANN001
        seen["launcher_type"] = type(self).__name__
        seen["task_type"] = task["task_type"]
        return {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": [],
        }

    with patch.object(ClaudeCodeLauncher, "launch", fake_launch):
        decision = run_iteration(
            campaign_dir=tmp_path,
            planner=lambda state, policy: {
                "experiment_id": "exp_14",
                "objective": "Default routing",
                "deliverables": [],
            },
            decomposer=lambda brief: [
                {
                    "task_id": "task_4",
                    "task_type": "code_and_run",
                    "deliverables": [],
                    "acceptance_criteria": [],
                }
            ],
            launcher=None,
            verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
            governor=lambda state, verification, policy: "CONTINUE",
        )
    assert decision == "CONTINUE"
    assert seen["launcher_type"] == "ClaudeCodeLauncher"
    assert seen["task_type"] == "code_and_run"



def test_run_iteration_passes_initial_state_to_governor(tmp_path) -> None:
    seen_state = {}

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_15",
            "objective": "Use carried state",
            "deliverables": ["metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_5",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            }
        ],
        launcher=lambda task: {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["metrics.json"],
        },
        verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
        governor=lambda state, verification, policy: seen_state.update(state) or "STOP",
        initial_state={
            "budget_status": {"experiments_run": 40},
            "failure_status": {"failure_streak": 2},
        },
    )

    assert decision == "STOP"
    assert seen_state == {
        "budget_status": {"experiments_run": 40},
        "failure_status": {"failure_streak": 2},
    }


def test_run_iteration_can_return_structured_governance_record(tmp_path) -> None:
    governance = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_16",
            "objective": "Use structured governance output",
            "deliverables": ["metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_6",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            }
        ],
        launcher=lambda task: {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["metrics.json"],
        },
        verifier=lambda brief, artifacts, result: {"status": "accept", "recommended_brain_action": "CONTINUE"},
        governor=lambda state, verification, policy: {
            "decision": "CONTINUE",
            "reason": "Structured governor output.",
            "basis": {"verification_status": "accept"},
        },
    )

    assert governance == {
        "decision": "CONTINUE",
        "reason": "Structured governor output.",
        "basis": {"verification_status": "accept"},
    }


def test_run_iteration_executes_multi_worker_serial_tasks_in_order(tmp_path) -> None:
    launched: list[str] = []
    seen_artifacts: dict = {}
    seen_result: dict = {}

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_17",
            "objective": "Run multi-worker serial flow",
            "deliverables": ["metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_review",
                "task_type": "analysis",
                "deliverables": [],
                "acceptance_criteria": [],
            },
            {
                "task_id": "task_impl",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            },
        ],
        launcher=lambda task: launched.append(task["task_id"]) or {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["metrics.json"] if task["task_id"] == "task_impl" else [],
        },
        verifier=lambda brief, artifacts, result: seen_artifacts.update(artifacts)
        or seen_result.update(result)
        or {
            "status": "accept",
            "recommended_brain_action": "CONTINUE",
            "task_id": result["task_id"],
        },
        governor=lambda state, verification, policy: "CONTINUE",
    )

    assert decision == "CONTINUE"
    assert launched == ["task_review", "task_impl"]
    assert seen_result["task_id"] == "task_impl"
    assert seen_artifacts["deliverable_paths"] == ["metrics.json"]
    assert [trace["task_id"] for trace in seen_artifacts["task_results"]] == ["task_review", "task_impl"]
    assert seen_artifacts["task_results"][0]["deliverable_paths"] == []
    assert seen_artifacts["task_results"][1]["deliverable_paths"] == ["metrics.json"]


def test_run_iteration_aggregates_deliverables_across_multi_task_round(tmp_path) -> None:
    seen_artifacts: dict = {}

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_18",
            "objective": "Aggregate artifacts across a multi-task round",
            "deliverables": ["review_note.md", "metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_review",
                "task_type": "analysis",
                "deliverables": ["review_note.md"],
                "acceptance_criteria": ["review_note.md exists"],
            },
            {
                "task_id": "task_impl",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            },
        ],
        launcher=lambda task: {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["review_note.md"] if task["task_id"] == "task_review" else ["metrics.json"],
        },
        verifier=lambda brief, artifacts, result: seen_artifacts.update(artifacts)
        or {
            "status": "accept",
            "recommended_brain_action": "CONTINUE",
            "task_id": result["task_id"],
        },
        governor=lambda state, verification, policy: "CONTINUE",
    )

    assert decision == "CONTINUE"
    assert seen_artifacts["deliverable_paths"] == ["review_note.md", "metrics.json"]


def test_run_iteration_exposes_execution_summary_for_multi_task_round(tmp_path) -> None:
    seen_artifacts: dict = {}

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_19",
            "objective": "Aggregate execution context across a multi-task round",
            "deliverables": ["metrics.json"],
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_review",
                "task_type": "analysis",
                "deliverables": [],
                "acceptance_criteria": [],
            },
            {
                "task_id": "task_impl",
                "task_type": "code_and_run",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            },
        ],
        launcher=lambda task: {
            "task_id": task["task_id"],
            "status": "success",
            "deliverable_paths": ["metrics.json"] if task["task_id"] == "task_impl" else [],
            "summary": (
                "The result suggests the metric improved because the review step identified the key evidence."
                if task["task_id"] == "task_review"
                else "Created metrics.json successfully."
            ),
        },
        verifier=lambda brief, artifacts, result: seen_artifacts.update(artifacts)
        or {
            "status": "accept",
            "recommended_brain_action": "CONTINUE",
            "task_id": result["task_id"],
        },
        governor=lambda state, verification, policy: "CONTINUE",
    )

    assert decision == "CONTINUE"
    assert "review step identified the key evidence" in seen_artifacts["execution_summary"]
    assert "Created metrics.json successfully." in seen_artifacts["execution_summary"]


def test_run_iteration_supports_real_claude_launcher_verifier_and_governor_flow(tmp_path: Path) -> None:
    def fake_runner(command, *, cwd, capture_output, text, timeout, check):  # noqa: ANN001
        (Path(cwd) / "metrics.json").write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="created metrics", stderr="")

    launcher = ClaudeCodeLauncher(binary_path="/usr/bin/ccb", runner=fake_runner)

    decision = run_iteration(
        campaign_dir=tmp_path,
        planner=lambda state, policy: {
            "experiment_id": "exp_real_launcher",
            "objective": "Create metrics.json through the launcher",
            "deliverables": ["metrics.json"],
            "acceptance_emphasis": "balanced",
            "repo_path": str(tmp_path),
        },
        decomposer=lambda brief: [
            {
                "task_id": "task_real_launcher",
                "task_type": "code_and_run",
                "goal": "Create metrics.json through the launcher",
                "deliverables": ["metrics.json"],
                "acceptance_criteria": ["metrics.json exists"],
            }
        ],
        launcher=launcher,
        verifier=verify_completion,
        governor=lambda state, verification, policy: make_governance_decision(
            state,
            verification,
            {
                "budgets": {"max_experiments": 40},
                "escalation": {"consecutive_failures_threshold": 3},
            },
        ),
        initial_state={
            "budget_status": {"experiments_run": 0},
            "failure_status": {"failure_streak": 0},
        },
    )

    assert decision == {
        "decision": "CONTINUE",
        "reason": "Verification accepted the latest round, so the campaign can continue.",
        "basis": {
            "verification_status": "accept",
            "rework_priority": "none",
            "failure_streak": 0,
            "experiments_run": 0,
            "max_experiments": 40,
            "failure_threshold": 3,
        },
    }
    assert (tmp_path / "metrics.json").exists()
