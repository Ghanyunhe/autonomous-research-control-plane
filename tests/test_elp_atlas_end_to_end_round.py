from __future__ import annotations

from pathlib import Path

from elp_atlas.round.run import EndToEndRoundResult, run_end_to_end_round, save_end_to_end_round


def test_run_end_to_end_round_returns_complete_artifact_bundle() -> None:
    result = run_end_to_end_round(round_id=1, phase_label="phase12_end_to_end_mvp")

    assert isinstance(result, EndToEndRoundResult)
    assert result.round_id == 1
    assert result.filtered_candidate_count >= result.selected_candidate_count
    assert result.selected_candidate_count > 0
    assert result.training_checkpoint_id == "solver_round_1"
    assert result.challenger_samples_consumed > 0
    assert result.domain_a_pass_rate == 1.0
    assert result.domain_b_execution_success_rate == 1.0


def test_save_end_to_end_round_writes_json_artifact(tmp_path: Path) -> None:
    result = run_end_to_end_round(round_id=2, phase_label="phase12_end_to_end_mvp")
    path = tmp_path / "end_to_end_round.json"

    save_end_to_end_round(path, result)

    text = path.read_text()
    assert "phase12_end_to_end_mvp" in text
    assert "training_checkpoint_id" in text
