from __future__ import annotations

from pathlib import Path

from elp_atlas.eval.domain_a import evaluate_domain_a, load_domain_a_dataset


def test_load_domain_a_dataset_reads_jsonl_candidates() -> None:
    path = Path("data/domain_a/tiny_math_eval.jsonl")

    candidates = load_domain_a_dataset(path)

    assert len(candidates) == 6
    assert candidates[0].task_id == "gsm8k_like_1"
    assert candidates[0].domain == "math"


def test_evaluate_domain_a_supports_real_dataset_candidates() -> None:
    path = Path("data/domain_a/tiny_math_eval.jsonl")

    result = evaluate_domain_a(load_domain_a_dataset(path))

    assert result.benchmark_name == "domain_a_tiny_math"
    assert result.total_examples == 6
    assert result.passed_examples == 6
    assert result.pass_rate == 1.0
