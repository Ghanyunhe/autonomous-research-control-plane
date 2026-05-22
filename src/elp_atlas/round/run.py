from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from elp_atlas.challenger import run_challenger_update
from elp_atlas.eval import evaluate_domain_a, evaluate_domain_b
from elp_atlas.generation import (
    filter_candidates,
    make_math_candidate_fixture,
    make_tool_use_candidate_fixture,
    select_top_per_skill,
)
from elp_atlas.probe import run_probe_update
from elp_atlas.rewards import score_candidate_batch
from elp_atlas.solver import run_solver_training_round


class EndToEndRoundResult(BaseModel):
    round_id: int
    phase_label: str
    filtered_candidate_count: int
    selected_candidate_count: int
    training_checkpoint_id: str
    challenger_samples_consumed: int
    domain_a_pass_rate: float
    domain_b_execution_success_rate: float
    summary: str


def run_end_to_end_round(*, round_id: int, phase_label: str) -> EndToEndRoundResult:
    candidates = [
        make_math_candidate_fixture(task_id=f"math_round_{round_id}"),
        make_tool_use_candidate_fixture(task_id=f"tool_round_{round_id}"),
    ]
    filtered = filter_candidates(candidates)
    accepted_task_ids = {entry.task_id for entry in filtered if entry.accepted}
    accepted_candidates = [candidate for candidate in candidates if candidate.task_id in accepted_task_ids]

    scores = score_candidate_batch(accepted_candidates)
    score_map = {score.task_id: score.cheap_score for score in scores}
    for candidate in accepted_candidates:
        candidate.metadata["cheap_score"] = score_map[candidate.task_id]

    shortlisted = select_top_per_skill(accepted_candidates, top_k=1)

    _ = run_probe_update(
        probe_id=f"probe_round_{round_id}",
        skill_node_id="node_1",
        before_score=0.40,
        after_score=0.52,
        old_memory_before=0.70,
        old_memory_after=0.68,
        frontier_size=16,
        old_memory_size=32,
    )

    training = run_solver_training_round(
        round_id=round_id,
        phase_label=phase_label,
        train_batch=shortlisted,
    )
    challenger = run_challenger_update(round_id=round_id, phase_label=phase_label, rewards=scores)
    domain_a = evaluate_domain_a([candidate for candidate in accepted_candidates if candidate.domain == "math"])
    domain_b = evaluate_domain_b([candidate for candidate in accepted_candidates if candidate.domain == "tool_use"])

    return EndToEndRoundResult(
        round_id=round_id,
        phase_label=phase_label,
        filtered_candidate_count=len(filtered),
        selected_candidate_count=len(shortlisted),
        training_checkpoint_id=training.checkpoint_id,
        challenger_samples_consumed=challenger.samples_consumed,
        domain_a_pass_rate=domain_a.pass_rate,
        domain_b_execution_success_rate=domain_b.execution_success_rate,
        summary="Tiny end-to-end ELP-Atlas round completed.",
    )


def save_end_to_end_round(path: Path, result: EndToEndRoundResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
