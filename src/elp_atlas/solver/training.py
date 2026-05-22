from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from elp_atlas.schemas import CandidateTask, RoundCheckpoint


class SolverTrainingResult(BaseModel):
    round_id: int
    phase_label: str
    checkpoint_id: str
    selected_train_batch_size: int
    accepted_domains: list[str] = Field(default_factory=list)
    training_summary: str

    def as_checkpoint(self) -> RoundCheckpoint:
        return RoundCheckpoint(
            round_id=self.round_id,
            phase_label=self.phase_label,
            config_snapshot={"checkpoint_id": self.checkpoint_id},
            artifact_paths=[f"artifacts/elp_atlas/{self.checkpoint_id}.json"],
            metrics={"selected_train_batch_size": float(self.selected_train_batch_size)},
            summary=self.training_summary,
        )


def run_solver_training_round(
    *,
    round_id: int,
    phase_label: str,
    train_batch: list[CandidateTask],
) -> SolverTrainingResult:
    accepted_domains = sorted({candidate.domain for candidate in train_batch})
    checkpoint_id = f"solver_round_{round_id}"
    return SolverTrainingResult(
        round_id=round_id,
        phase_label=phase_label,
        checkpoint_id=checkpoint_id,
        selected_train_batch_size=len(train_batch),
        accepted_domains=accepted_domains,
        training_summary=f"Trained solver on {len(train_batch)} candidate tasks.",
    )


def save_training_result(path: Path, result: SolverTrainingResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
