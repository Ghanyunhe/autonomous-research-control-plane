from __future__ import annotations

from pathlib import Path

from elp_atlas.eval import run_domain_a_dataset


def test_run_domain_a_dataset_evaluates_local_jsonl_file() -> None:
    path = Path("data/domain_a/tiny_math_eval.jsonl")

    result = run_domain_a_dataset(path)

    assert result.dataset_path == str(path)
    assert result.total_examples == 6
    assert result.passed_examples == 6
    assert result.pass_rate == 1.0
