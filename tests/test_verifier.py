from __future__ import annotations

from pathlib import Path

from controlplane.verifier.completion_judge import verify_completion


def test_verify_completion_accepts_complete_bundle() -> None:
    brief = {"deliverables": ["metrics.json"], "objective": "Test robustness"}
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {"status": "success", "task_id": "task_1"}
    report = verify_completion(brief, artifacts, worker_result)
    assert report["status"] == "accept"
    assert report["failed_check_types"] == []
    assert report["rework_priority"] == "none"


def test_verify_completion_surfaces_emphasis_in_rework_reasoning() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Repair the failed experiment",
        "acceptance_emphasis": "artifact_presence",
    }
    artifacts = {"deliverable_paths": []}
    worker_result = {"status": "failed", "task_id": "task_1"}

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert report["failed_check_types"] == ["artifact_presence", "worker_execution"]
    assert report["rework_priority"] == "high"
    assert report["warnings"] == ["Prioritize artifact_presence during the next verification pass."]


def test_verify_completion_marks_scientific_validity_when_summary_is_operational_only() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]
    assert report["recommended_brain_action"] == "REFINE"


def test_verify_completion_marks_scientific_validity_when_summary_is_empty() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]


def test_verify_completion_marks_scientific_validity_when_summary_is_too_short() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Observed some changes in metrics.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]


def test_verify_completion_accepts_scientific_validity_when_summary_contains_findings() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "The experiment suggests robustness drops under noise, with evidence from the reported metrics.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]


def test_verify_completion_accepts_thin_summary_when_result_note_contains_findings(tmp_path: Path) -> None:
    repo_path = tmp_path
    (repo_path / "result_note.md").write_text(
        (
            "The result suggests the robustness drops because the noisy condition "
            "reduced the metric, and the evidence is the repeated finding across runs."
        ),
        encoding="utf-8",
    )
    brief = {
        "deliverables": ["metrics.json", "result_note.md"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
        "repo_path": str(repo_path),
    }
    artifacts = {"deliverable_paths": ["metrics.json", "result_note.md"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]


def test_verify_completion_rejects_thin_summary_when_result_note_is_also_weak(tmp_path: Path) -> None:
    repo_path = tmp_path
    (repo_path / "result_note.md").write_text(
        "Created the result note and saved the metrics file.",
        encoding="utf-8",
    )
    brief = {
        "deliverables": ["metrics.json", "result_note.md"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
        "repo_path": str(repo_path),
    }
    artifacts = {"deliverable_paths": ["metrics.json", "result_note.md"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]


def test_verify_completion_treats_missing_result_note_as_optional(tmp_path: Path) -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
        "repo_path": str(tmp_path),
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]


def test_verify_completion_leaves_non_scientific_emphasis_unchanged_for_thin_summary() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Generate metrics",
        "acceptance_emphasis": "artifact_presence",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]


def test_verify_completion_uses_execution_summary_from_multi_task_round() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {
        "deliverable_paths": ["metrics.json"],
        "execution_summary": (
            "The result suggests the metric improved because the review step identified the key evidence "
            "and the implementation step preserved the finding across the run."
        ),
        "task_results": [
            {
                "task_id": "task_review",
                "status": "success",
                "summary": (
                    "The result suggests the metric improved because the review step identified the key evidence."
                ),
            },
            {
                "task_id": "task_impl",
                "status": "success",
                "summary": "Created metrics.json successfully.",
            },
        ],
    }
    worker_result = {
        "status": "success",
        "task_id": "task_impl",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]
