from __future__ import annotations

from elp_atlas.generation.fixtures import make_math_candidate_fixture, make_tool_use_candidate_fixture
from elp_atlas.schemas import CandidateTask
from elp_atlas.skills.encoding import (
    abstract_skill_record_from_candidate,
    encode_skill_record,
    summarize_skill_record,
)


def test_make_math_candidate_fixture_returns_candidate_task() -> None:
    candidate = make_math_candidate_fixture(task_id="math_1")

    assert isinstance(candidate, CandidateTask)
    assert candidate.domain == "math"
    assert candidate.skill_record.domain == "math"
    assert "linear_equation" in candidate.skill_record.skill_tags


def test_make_tool_use_candidate_fixture_returns_candidate_task() -> None:
    candidate = make_tool_use_candidate_fixture(task_id="tool_1")

    assert isinstance(candidate, CandidateTask)
    assert candidate.domain == "tool_use"
    assert candidate.skill_record.domain == "tool_use"
    assert "tool_selection" in candidate.skill_record.skill_tags


def test_abstract_skill_record_from_candidate_preserves_core_fields() -> None:
    candidate = make_math_candidate_fixture(task_id="math_2")

    record = abstract_skill_record_from_candidate(candidate)

    assert record.domain == "math"
    assert "solve_equation" in record.reasoning_ops
    assert "sign_error" in record.failure_modes_targeted


def test_encode_skill_record_returns_deterministic_key() -> None:
    candidate = make_tool_use_candidate_fixture(task_id="tool_2")
    record = abstract_skill_record_from_candidate(candidate)

    encoded_once = encode_skill_record(record)
    encoded_twice = encode_skill_record(record)

    assert encoded_once == encoded_twice
    assert encoded_once.startswith("tool_use:")
    assert "tool_selection" in encoded_once


def test_summarize_skill_record_returns_human_readable_summary() -> None:
    candidate = make_math_candidate_fixture(task_id="math_3")
    record = abstract_skill_record_from_candidate(candidate)

    summary = summarize_skill_record(record)

    assert "domain=math" in summary
    assert "skills=linear_equation" in summary
