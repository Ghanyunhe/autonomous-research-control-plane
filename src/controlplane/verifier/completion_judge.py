from __future__ import annotations

from pathlib import Path
import re


def required_artifacts_present(brief: dict, artifacts: dict) -> bool:
    return all(path in artifacts["deliverable_paths"] for path in brief["deliverables"])


def has_minimal_scientific_explanation(summary: str) -> bool:
    normalized_summary = " ".join(summary.lower().split())
    if len(normalized_summary) < 60:
        return False
    scientific_term_patterns = (
        r"\bbecause\b",
        r"\bsuggest(?:s|ed|ing)?\b",
        r"\bevidence\b",
        r"\bresult(?:s)?\b",
        r"\bfinding(?:s)?\b",
        r"\bhypothes(?:is|es)\b",
        r"\bobserv(?:e|es|ed|ing|ation|ations)\b",
        r"\bmetric(?:s)?\b",
    )
    interpretive_term_patterns = scientific_term_patterns[:3] + scientific_term_patterns[4:7]
    total_matches = sum(bool(re.search(pattern, normalized_summary)) for pattern in scientific_term_patterns)
    has_interpretive_signal = any(
        re.search(pattern, normalized_summary) for pattern in interpretive_term_patterns
    )
    return total_matches >= 2 and has_interpretive_signal


def read_optional_result_note(brief: dict) -> str:
    repo_path = brief.get("repo_path")
    if not repo_path:
        return ""
    try:
        return (Path(repo_path) / "result_note.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def verify_completion(brief: dict, artifacts: dict, worker_result: dict) -> dict:
    failures: list[str] = []
    failed_check_types: list[str] = []
    warnings: list[str] = []
    acceptance_emphasis = brief.get("acceptance_emphasis", "balanced")
    if not required_artifacts_present(brief, artifacts):
        failures.append("missing_artifacts")
        failed_check_types.append("artifact_presence")
    if worker_result["status"] != "success":
        failures.append("worker_not_successful")
        failed_check_types.append("worker_execution")
    explanatory_text = worker_result.get("summary", "")
    if acceptance_emphasis == "scientific_validity":
        execution_summary = (artifacts.get("execution_summary") or "").strip()
        explanatory_text = "\n".join(
            text for text in (execution_summary, explanatory_text, read_optional_result_note(brief)) if text
        )
    if (
        acceptance_emphasis == "scientific_validity"
        and worker_result["status"] == "success"
        and not has_minimal_scientific_explanation(explanatory_text)
    ):
        failures.append("insufficient_scientific_explanation")
        failed_check_types.append("scientific_validity")
    status = "accept" if not failures else "rework"
    if status == "rework" and acceptance_emphasis != "balanced":
        warnings.append(f"Prioritize {acceptance_emphasis} during the next verification pass.")
    rework_priority = "none" if status == "accept" else "medium"
    if status == "rework" and "artifact_presence" in failed_check_types and "worker_execution" in failed_check_types:
        rework_priority = "high"
    return {
        "task_id": worker_result["task_id"],
        "status": status,
        "failures": failures,
        "failed_check_types": failed_check_types,
        "rework_priority": rework_priority,
        "warnings": warnings,
        "recommended_brain_action": "CONTINUE" if status == "accept" else "REFINE",
    }
