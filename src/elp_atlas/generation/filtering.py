from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from elp_atlas.schemas import CandidateTask
from elp_atlas.skills.encoding import encode_skill_record


class FilteredCandidate(BaseModel):
    task_id: str
    accepted: bool
    rejection_reasons: list[str] = Field(default_factory=list)
    skill_key: str
    cheap_score: float = 0.0


def filter_candidates(candidates: list[CandidateTask]) -> list[FilteredCandidate]:
    results: list[FilteredCandidate] = []
    for candidate in candidates:
        rejection_reasons: list[str] = []
        if len(candidate.problem.strip()) < 30:
            rejection_reasons.append("problem_too_short")
        if not candidate.anti_leakage_check.strip():
            rejection_reasons.append("missing_anti_leakage_check")
        if not candidate.skill_record.skill_tags:
            rejection_reasons.append("missing_skill_tags")
        if not candidate.skill_record.reasoning_ops:
            rejection_reasons.append("missing_reasoning_ops")
        results.append(
            FilteredCandidate(
                task_id=candidate.task_id,
                accepted=not rejection_reasons,
                rejection_reasons=rejection_reasons,
                skill_key=encode_skill_record(candidate.skill_record),
                cheap_score=float(candidate.metadata.get("cheap_score", 0.0)),
            )
        )
    return results


def select_top_per_skill(candidates: list[CandidateTask], *, top_k: int) -> list[CandidateTask]:
    grouped: dict[str, list[CandidateTask]] = defaultdict(list)
    for candidate in candidates:
        grouped[encode_skill_record(candidate.skill_record)].append(candidate)

    selected: list[CandidateTask] = []
    for skill_key in sorted(grouped):
        ranked = sorted(
            grouped[skill_key],
            key=lambda candidate: float(candidate.metadata.get("cheap_score", 0.0)),
            reverse=True,
        )
        selected.extend(ranked[:top_k])
    return selected


def save_filtered_candidates(path: Path, results: list[FilteredCandidate]) -> None:
    path.write_text(
        "[\n"
        + ",\n".join(result.model_dump_json(indent=2) for result in results)
        + "\n]\n"
    )
