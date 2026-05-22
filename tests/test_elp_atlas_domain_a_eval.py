from __future__ import annotations

from pathlib import Path

from elp_atlas.eval.domain_a import DomainAEvaluationResult, evaluate_domain_a, save_domain_a_result
from elp_atlas.generation.fixtures import make_math_candidate_fixture


def test_evaluate_domain_a_returns_structured_summary_for_tiny_fixture_batch() -> None:
    fixtures = [
        make_math_candidate_fixture(task_id="math_eval_1"),
        make_math_candidate_fixture(task_id="math_eval_2"),
    ]

    result = evaluate_domain_a(fixtures)

    assert isinstance(result, DomainAEvaluationResult)
    assert result.benchmark_name == "domain_a_tiny_math"
    assert result.total_examples == 2
    assert result.passed_examples == 2
    assert result.pass_rate == 1.0
    assert "linear_equation" in result.skill_coverage


def test_save_domain_a_result_writes_json_artifact(tmp_path: Path) -> None:
    result = evaluate_domain_a([make_math_candidate_fixture(task_id="math_eval_3")])
    path = tmp_path / "domain_a_result.json"

    save_domain_a_result(path, result)

    text = path.read_text()
    assert "domain_a_tiny_math" in text
    assert "pass_rate" in text
