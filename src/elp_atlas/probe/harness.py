from __future__ import annotations

from pathlib import Path

from elp_atlas.schemas import ProbeResult


def run_probe_update(
    *,
    probe_id: str,
    skill_node_id: str,
    before_score: float,
    after_score: float,
    old_memory_before: float,
    old_memory_after: float,
    frontier_size: int,
    old_memory_size: int,
) -> ProbeResult:
    """Return a minimal synthetic probe result for before/after delta evaluation."""
    learning_progress_estimate = round(after_score - before_score, 2)
    regression_estimate = round(max(0.0, old_memory_before - old_memory_after), 2)
    return ProbeResult(
        probe_id=probe_id,
        skill_node_id=skill_node_id,
        before_score=before_score,
        after_score=after_score,
        learning_progress_estimate=learning_progress_estimate,
        regression_estimate=regression_estimate,
        eval_set_sizes={"frontier": frontier_size, "old": old_memory_size},
        notes="Synthetic probe harness result.",
    )


def save_probe_result(path: Path, result: ProbeResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
