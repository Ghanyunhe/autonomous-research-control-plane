from __future__ import annotations

from pathlib import Path

from elp_atlas.eval.domain_b import DomainBEvaluationResult, evaluate_domain_b, save_domain_b_result
from elp_atlas.generation.fixtures import make_tool_use_candidate_fixture


def test_evaluate_domain_b_returns_structured_summary_for_tiny_fixture_batch() -> None:
    fixtures = [
        make_tool_use_candidate_fixture(task_id="tool_eval_1"),
        make_tool_use_candidate_fixture(task_id="tool_eval_2"),
    ]

    result = evaluate_domain_b(fixtures)

    assert isinstance(result, DomainBEvaluationResult)
    assert result.benchmark_name == "domain_b_tiny_tool_use"
    assert result.total_examples == 2
    assert result.execution_successes == 2
    assert result.execution_success_rate == 1.0
    assert "tool_selection" in result.skill_coverage


def test_save_domain_b_result_writes_json_artifact(tmp_path: Path) -> None:
    result = evaluate_domain_b([make_tool_use_candidate_fixture(task_id="tool_eval_3")])
    path = tmp_path / "domain_b_result.json"

    save_domain_b_result(path, result)

    text = path.read_text()
    assert "domain_b_tiny_tool_use" in text
    assert "execution_success_rate" in text
