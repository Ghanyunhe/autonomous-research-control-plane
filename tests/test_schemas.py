from __future__ import annotations

import pytest

from controlplane.schemas.experiment_brief import ExperimentBrief
from controlplane.schemas.task_packet import TaskPacket
from controlplane.schemas.task_intent import TaskIntent


def test_experiment_brief_accepts_valid_payload() -> None:
    brief = ExperimentBrief(
        experiment_id="exp_11",
        objective="Test class-imbalanced label noise robustness",
        hypothesis_links=["h1"],
        inputs={"repo_path": "/tmp/repo", "artifact_refs": [], "dataset_refs": []},
        constraints={
            "max_runtime_minutes": 45,
            "max_api_cost_usd": 4.0,
            "allowed_backends": ["claude_code"],
        },
        deliverables=["metrics.json"],
        acceptance_criteria=["metrics file exists"],
        decomposition_hint="single_worker",
        preferred_worker_profile="coder_plus_runner",
    )
    assert brief.experiment_id == "exp_11"


def test_task_packet_rejects_unknown_task_type() -> None:
    with pytest.raises(ValueError):
        TaskPacket(
            task_id="task_1",
            experiment_id="exp_11",
            task_type="unknown",
            goal="Invalid",
            worker_requirements={"backend": "claude_code", "strengths": [], "skills": [], "tools_needed": []},
            deliverables=[],
            acceptance_criteria=[],
            retry_policy={"max_retries": 1, "fallback_backend": "codex"},
        )


def test_task_intent_accepts_supported_task_type() -> None:
    intent = TaskIntent(
        task_type="repair",
        worker_preference="claude_code",
        acceptance_emphasis="artifact_presence",
        goal_hint="Fix missing artifacts from the previous round",
        focus_areas=["missing_artifacts"],
    )
    assert intent.task_type == "repair"
