from __future__ import annotations

from pathlib import Path

from elp_atlas.generation.filtering import (
    FilteredCandidate,
    filter_candidates,
    save_filtered_candidates,
    select_top_per_skill,
)
from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture
from elp_atlas.skills.encoding import encode_skill_record


def test_filter_candidates_marks_rejection_reasons() -> None:
    good = make_math_candidate_fixture(task_id="good")
    bad = make_math_candidate_fixture(task_id="bad")
    bad.problem = "short"
    bad.anti_leakage_check = ""
    bad.skill_record.skill_tags = []

    results = filter_candidates([good, bad])

    assert isinstance(results[0], FilteredCandidate)
    assert results[0].accepted is True
    assert results[1].accepted is False
    assert "missing_anti_leakage_check" in results[1].rejection_reasons
    assert "missing_skill_tags" in results[1].rejection_reasons
    assert "problem_too_short" in results[1].rejection_reasons


def test_select_top_per_skill_keeps_best_candidates_per_skill() -> None:
    a = make_math_candidate_fixture(task_id="a")
    b = make_math_candidate_fixture(task_id="b")
    c = make_tool_use_candidate_fixture(task_id="c")

    a.metadata["cheap_score"] = 0.50
    b.metadata["cheap_score"] = 0.80
    c.metadata["cheap_score"] = 0.70

    shortlisted = select_top_per_skill([a, b, c], top_k=1)

    assert [candidate.task_id for candidate in shortlisted] == ["b", "c"]
    assert encode_skill_record(shortlisted[0].skill_record) != encode_skill_record(shortlisted[1].skill_record)


def test_save_filtered_candidates_writes_json_artifact(tmp_path: Path) -> None:
    results = filter_candidates([make_tool_use_candidate_fixture(task_id="tool_filter_1")])
    path = tmp_path / "filtered_candidates.json"

    save_filtered_candidates(path, results)

    text = path.read_text()
    assert "tool_filter_1" in text
    assert "accepted" in text
