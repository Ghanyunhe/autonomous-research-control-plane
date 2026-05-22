from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from elp_atlas.schemas import CandidateTask


class CheapELPScore(BaseModel):
    task_id: str
    novelty: float
    frontier: float
    noise: float
    gradient_learning_progress: float
    cheap_score: float
    state_hint: str


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def estimate_novelty(candidate: CandidateTask) -> float:
    unique_parts = {
        *candidate.skill_record.skill_tags,
        *candidate.skill_record.reasoning_ops,
        *candidate.skill_record.failure_modes_targeted,
    }
    denominator = max(
        1,
        len(candidate.skill_record.skill_tags)
        + len(candidate.skill_record.reasoning_ops)
        + len(candidate.skill_record.failure_modes_targeted),
    )
    return _clamp(len(unique_parts) / denominator)


def estimate_frontier(candidate: CandidateTask) -> float:
    difficulty = candidate.skill_record.difficulty_estimate
    if difficulty is None:
        difficulty = 0.5
    difficulty = _clamp(difficulty)
    return _clamp(4 * difficulty * (1 - difficulty))


def estimate_noise(candidate: CandidateTask) -> float:
    noise = 0.0
    if not candidate.anti_leakage_check.strip():
        noise += 0.4
    if len(candidate.problem.strip()) < 30:
        noise += 0.3
    if not candidate.skill_record.skill_tags:
        noise += 0.2
    if not candidate.skill_record.reasoning_ops:
        noise += 0.1
    return _clamp(noise)


def estimate_gradient_learning_progress(candidate: CandidateTask) -> float:
    tags = len(candidate.skill_record.skill_tags)
    ops = len(candidate.skill_record.reasoning_ops)
    failure_modes = len(candidate.skill_record.failure_modes_targeted)
    raw = 0.2 + (0.15 * tags) + (0.1 * ops) + (0.05 * failure_modes)
    return _clamp(raw)


def score_candidate_task(candidate: CandidateTask) -> CheapELPScore:
    novelty = estimate_novelty(candidate)
    frontier = estimate_frontier(candidate)
    noise = estimate_noise(candidate)
    gradient_learning_progress = estimate_gradient_learning_progress(candidate)
    cheap_score = (
        (1.0 * gradient_learning_progress)
        + (0.3 * frontier)
        + (0.25 * novelty)
        - (0.8 * noise)
    )
    state_hint = (
        f"grad_lp={gradient_learning_progress:.2f}; frontier={frontier:.2f}; "
        f"novelty={novelty:.2f}; noise={noise:.2f}"
    )
    return CheapELPScore(
        task_id=candidate.task_id,
        novelty=novelty,
        frontier=frontier,
        noise=noise,
        gradient_learning_progress=gradient_learning_progress,
        cheap_score=cheap_score,
        state_hint=state_hint,
    )


def score_candidate_batch(candidates: list[CandidateTask]) -> list[CheapELPScore]:
    return sorted((score_candidate_task(candidate) for candidate in candidates), key=lambda score: score.cheap_score, reverse=True)


def save_score_batch(path: Path, scores: list[CheapELPScore]) -> None:
    path.write_text(
        "[\n"
        + ",\n".join(score.model_dump_json(indent=2) for score in scores)
        + "\n]\n"
    )
