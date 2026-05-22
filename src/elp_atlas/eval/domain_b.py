from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from elp_atlas.schemas import CandidateTask


class DomainBEvaluationResult(BaseModel):
    benchmark_name: str
    total_examples: int
    valid_schema_outputs: int
    execution_successes: int
    execution_success_rate: float
    skill_coverage: list[str] = Field(default_factory=list)
    notes: str = ""


def evaluate_domain_b(candidates: list[CandidateTask]) -> DomainBEvaluationResult:
    """Run a tiny synthetic Domain B evaluation over tool-use fixtures."""
    valid_schema_outputs = 0
    execution_successes = 0
    skill_coverage: set[str] = set()
    for candidate in candidates:
        if candidate.domain != "tool_use":
            continue
        if candidate.verifier.type == "tool_call":
            valid_schema_outputs += 1
        if candidate.reference_answer.strip() and "tool" in candidate.reference_answer and "arguments" in candidate.reference_answer:
            execution_successes += 1
        skill_coverage.update(candidate.skill_record.skill_tags)
    total_examples = len(candidates)
    execution_success_rate = 0.0 if total_examples == 0 else round(execution_successes / total_examples, 2)
    return DomainBEvaluationResult(
        benchmark_name="domain_b_tiny_tool_use",
        total_examples=total_examples,
        valid_schema_outputs=valid_schema_outputs,
        execution_successes=execution_successes,
        execution_success_rate=execution_success_rate,
        skill_coverage=sorted(skill_coverage),
        notes="Synthetic Domain B benchmark result.",
    )


def save_domain_b_result(path: Path, result: DomainBEvaluationResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
