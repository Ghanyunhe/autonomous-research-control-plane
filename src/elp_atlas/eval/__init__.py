"""Evaluation harness seams for ELP-Atlas domains."""

from elp_atlas.eval.domain_a import (
    DomainAEvaluationResult,
    evaluate_domain_a,
    load_domain_a_dataset,
    run_domain_a_dataset,
    save_domain_a_result,
)
from elp_atlas.eval.domain_b import DomainBEvaluationResult, evaluate_domain_b, save_domain_b_result

__all__ = [
    "DomainAEvaluationResult",
    "DomainBEvaluationResult",
    "evaluate_domain_a",
    "evaluate_domain_b",
    "load_domain_a_dataset",
    "run_domain_a_dataset",
    "save_domain_a_result",
    "save_domain_b_result",
]
