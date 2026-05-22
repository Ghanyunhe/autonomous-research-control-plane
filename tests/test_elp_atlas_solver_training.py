from __future__ import annotations

from pathlib import Path

from elp_atlas.checkpoints.manifest import build_checkpoint_manifest, save_checkpoint_manifest
from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture
from elp_atlas.solver.training import SolverTrainingResult, run_solver_training_round, save_training_result


def test_run_solver_training_round_returns_structured_training_summary() -> None:
    train_batch = [
        make_math_candidate_fixture(task_id="train_math_1"),
        make_tool_use_candidate_fixture(task_id="train_tool_1"),
    ]

    result = run_solver_training_round(
        round_id=1,
        phase_label="phase9_solver_training_mvp",
        train_batch=train_batch,
    )

    assert isinstance(result, SolverTrainingResult)
    assert result.round_id == 1
    assert result.selected_train_batch_size == 2
    assert result.checkpoint_id == "solver_round_1"
    assert result.accepted_domains == ["math", "tool_use"]


def test_training_result_and_manifest_can_be_persisted(tmp_path: Path) -> None:
    result = run_solver_training_round(
        round_id=2,
        phase_label="phase9_solver_training_mvp",
        train_batch=[make_math_candidate_fixture(task_id="train_math_2")],
    )
    training_path = tmp_path / "training_summary.json"
    manifest_path = tmp_path / "checkpoint_manifest.json"

    save_training_result(training_path, result)
    manifest = build_checkpoint_manifest([result.as_checkpoint()])
    save_checkpoint_manifest(manifest_path, manifest)

    assert "solver_round_2" in training_path.read_text()
    assert "phase9_solver_training_mvp" in manifest_path.read_text()
