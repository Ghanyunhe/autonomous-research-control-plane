from __future__ import annotations

from pathlib import Path

from elp_atlas.probe.harness import run_probe_update, save_probe_result
from elp_atlas.schemas import ProbeResult


def test_run_probe_update_returns_probe_result_with_positive_learning_progress() -> None:
    result = run_probe_update(
        probe_id="probe_1",
        skill_node_id="node_1",
        before_score=0.35,
        after_score=0.48,
        old_memory_before=0.72,
        old_memory_after=0.70,
        frontier_size=32,
        old_memory_size=64,
    )

    assert isinstance(result, ProbeResult)
    assert result.probe_id == "probe_1"
    assert result.skill_node_id == "node_1"
    assert result.learning_progress_estimate == 0.13
    assert result.regression_estimate == 0.02


def test_run_probe_update_clamps_negative_regression_to_zero_when_old_memory_improves() -> None:
    result = run_probe_update(
        probe_id="probe_2",
        skill_node_id="node_2",
        before_score=0.41,
        after_score=0.50,
        old_memory_before=0.62,
        old_memory_after=0.68,
        frontier_size=16,
        old_memory_size=48,
    )

    assert result.learning_progress_estimate == 0.09
    assert result.regression_estimate == 0.0


def test_save_probe_result_writes_json_artifact(tmp_path: Path) -> None:
    result = run_probe_update(
        probe_id="probe_3",
        skill_node_id="node_3",
        before_score=0.20,
        after_score=0.29,
        old_memory_before=0.55,
        old_memory_after=0.52,
        frontier_size=12,
        old_memory_size=24,
    )
    path = tmp_path / "probe_result.json"

    save_probe_result(path, result)

    text = path.read_text()
    assert "probe_3" in text
    assert "learning_progress_estimate" in text
