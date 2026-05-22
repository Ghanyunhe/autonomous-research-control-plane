from __future__ import annotations

from pathlib import Path

from elp_atlas.memory.replay import ReplayMemoryEntry, build_replay_memory, save_replay_memory
from elp_atlas.regression.report import RegressionReport, build_regression_report, save_regression_report
from elp_atlas.solver.training import run_solver_training_round
from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture


def test_build_replay_memory_returns_entries_for_old_skills() -> None:
    entries = build_replay_memory(
        [
            make_math_candidate_fixture(task_id="replay_math_1"),
            make_tool_use_candidate_fixture(task_id="replay_tool_1"),
        ]
    )

    assert isinstance(entries[0], ReplayMemoryEntry)
    assert len(entries) == 2
    assert entries[0].task_id == "replay_math_1"


def test_build_regression_report_summarizes_training_checkpoint_and_regression() -> None:
    training = run_solver_training_round(
        round_id=3,
        phase_label="phase11_regression_memory_mvp",
        train_batch=[make_math_candidate_fixture(task_id="train_math_3")],
    )

    report = build_regression_report(
        checkpoint_id=training.checkpoint_id,
        old_skill_scores={"math.linear_equation": 0.72, "tool_use.tool_selection": 0.61},
        new_skill_scores={"math.linear_equation": 0.70, "tool_use.tool_selection": 0.64},
    )

    assert isinstance(report, RegressionReport)
    assert report.checkpoint_id == "solver_round_3"
    assert report.total_regression > 0.0
    assert "math.linear_equation" in report.regressed_skills


def test_replay_memory_and_regression_report_can_be_persisted(tmp_path: Path) -> None:
    replay_entries = build_replay_memory([make_math_candidate_fixture(task_id="replay_math_2")])
    report = build_regression_report(
        checkpoint_id="solver_round_4",
        old_skill_scores={"math.linear_equation": 0.80},
        new_skill_scores={"math.linear_equation": 0.78},
    )

    replay_path = tmp_path / "replay_memory.json"
    report_path = tmp_path / "regression_report.json"

    save_replay_memory(replay_path, replay_entries)
    save_regression_report(report_path, report)

    assert "replay_math_2" in replay_path.read_text()
    assert "solver_round_4" in report_path.read_text()
