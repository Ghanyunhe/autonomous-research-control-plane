from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from elp_atlas.schemas import CandidateTask


class DomainAEvaluationResult(BaseModel):
    benchmark_name: str
    total_examples: int
    passed_examples: int
    pass_rate: float
    skill_coverage: list[str] = Field(default_factory=list)
    notes: str = ""


def load_domain_a_dataset(path: Path) -> list[CandidateTask]:
    candidates: list[CandidateTask] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        candidates.append(CandidateTask.model_validate(json.loads(line)))
    return candidates


def evaluate_domain_a(candidates: list[CandidateTask]) -> DomainAEvaluationResult:
    """Run a tiny Domain A evaluation over candidate tasks."""
    passed_examples = 0
    skill_coverage: set[str] = set()
    for candidate in candidates:
        if candidate.domain == "math" and candidate.reference_answer.strip():
            passed_examples += 1
        skill_coverage.update(candidate.skill_record.skill_tags)
    total_examples = len(candidates)
    pass_rate = 0.0 if total_examples == 0 else round(passed_examples / total_examples, 2)
    return DomainAEvaluationResult(
        benchmark_name="domain_a_tiny_math",
        total_examples=total_examples,
        passed_examples=passed_examples,
        pass_rate=pass_rate,
        skill_coverage=sorted(skill_coverage),
        notes="Synthetic Domain A benchmark result.",
    )


def save_domain_a_result(path: Path, result: DomainAEvaluationResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
