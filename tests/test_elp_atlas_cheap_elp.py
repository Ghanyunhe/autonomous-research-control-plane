from __future__ import annotations

from pathlib import Path

from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture
from elp_atlas.rewards.cheap_elp import (
    CheapELPScore,
    save_score_batch,
    score_candidate_batch,
    score_candidate_task,
)


def test_score_candidate_task_returns_stable_breakdown() -> None:
    candidate = make_math_candidate_fixture(task_id="math_score_1")

    score = score_candidate_task(candidate)

    assert isinstance(score, CheapELPScore)
    assert score.task_id == "math_score_1"
    assert 0.0 <= score.novelty <= 1.0
    assert 0.0 <= score.frontier <= 1.0
    assert 0.0 <= score.noise <= 1.0
    assert score.state_hint


def test_score_candidate_batch_sorts_by_score_descending() -> None:
    strong = make_tool_use_candidate_fixture(task_id="strong")
    weak = make_math_candidate_fixture(task_id="weak")
    weak.skill_record.skill_tags = []
    weak.skill_record.reasoning_ops = []
    weak.skill_record.failure_modes_targeted = []
    weak.skill_record.difficulty_estimate = 0.99
    weak.anti_leakage_check = ""

    scores = score_candidate_batch([weak, strong])

    assert [score.task_id for score in scores] == ["strong", "weak"]
    assert scores[0].cheap_score >= scores[1].cheap_score


def test_save_score_batch_writes_json_artifact(tmp_path: Path) -> None:
    scores = score_candidate_batch(
        [
            make_math_candidate_fixture(task_id="math_score_2"),
            make_tool_use_candidate_fixture(task_id="tool_score_2"),
        ]
    )
    path = tmp_path / "candidate_scores.json"

    save_score_batch(path, scores)

    text = path.read_text()
    assert "math_score_2" in text
    assert "cheap_score" in text
