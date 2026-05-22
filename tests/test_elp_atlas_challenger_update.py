from __future__ import annotations

from pathlib import Path

from elp_atlas.challenger.update import ChallengerUpdateResult, run_challenger_update, save_challenger_update
from elp_atlas.rewards import score_candidate_batch
from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture


def test_run_challenger_update_returns_structured_reward_summary() -> None:
    scores = score_candidate_batch(
        [
            make_math_candidate_fixture(task_id="challenger_math_1"),
            make_tool_use_candidate_fixture(task_id="challenger_tool_1"),
        ]
    )

    result = run_challenger_update(round_id=1, phase_label="phase10_challenger_update_mvp", rewards=scores)

    assert isinstance(result, ChallengerUpdateResult)
    assert result.round_id == 1
    assert result.samples_consumed == 2
    assert result.reward_mean > 0.0
    assert result.reward_max >= result.reward_mean


def test_save_challenger_update_writes_json_artifact(tmp_path: Path) -> None:
    scores = score_candidate_batch([make_math_candidate_fixture(task_id="challenger_math_2")])
    result = run_challenger_update(round_id=2, phase_label="phase10_challenger_update_mvp", rewards=scores)
    path = tmp_path / "challenger_update.json"

    save_challenger_update(path, result)

    text = path.read_text()
    assert "phase10_challenger_update_mvp" in text
    assert "reward_mean" in text
