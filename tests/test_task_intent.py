from __future__ import annotations

from controlplane.brain.task_intent import derive_task_intent
from controlplane.brain.objective_evolver import NextIterationPlan


def test_derive_task_intent_maps_refine_to_repair() -> None:
    plan = NextIterationPlan(
        next_objective="Refine metrics generation",
        strategy="refine",
        reason="Previous round missed artifacts.",
        focus_areas=["missing_artifacts"],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "repair"
    assert intent.worker_preference == "claude_code"
    assert intent.acceptance_emphasis == "artifact_presence"
    assert intent.focus_areas == ["missing_artifacts"]


def test_derive_task_intent_keeps_first_round_as_code_and_run() -> None:
    plan = NextIterationPlan(
        next_objective="Create metrics.json",
        strategy="continue",
        reason="No prior iteration exists; start from the base objective.",
        focus_areas=[],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "code_and_run"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "balanced"


def test_derive_task_intent_maps_successful_continuation_to_analysis() -> None:
    plan = NextIterationPlan(
        next_objective="Continue from the successful round",
        strategy="continue",
        reason="Previous round succeeded and exposed a usable continuation point.",
        focus_areas=["build_on_success"],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == ["build_on_success"]


def test_derive_task_intent_maps_hold_to_analysis_review_mode() -> None:
    plan = NextIterationPlan(
        next_objective="Create metrics.json",
        strategy="hold",
        reason="Verifier recommended STOP, so the base objective is retained pending review.",
        focus_areas=[],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == []


def test_derive_task_intent_maps_pending_promotion_investigation_to_analysis() -> None:
    plan = NextIterationPlan(
        next_objective="Investigate the blocked promotion pair before broader expansion.",
        strategy="continue",
        reason="Previous round succeeded; investigate_pending_promotion_pair is active.",
        focus_areas=["build_on_success", "pending_promotion_pair_investigation"],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == ["build_on_success", "pending_promotion_pair_investigation"]


def test_derive_task_intent_maps_anchor_coherence_reconcile_to_analysis() -> None:
    plan = NextIterationPlan(
        next_objective="Reconcile backlog and hypothesis signals before broader expansion.",
        strategy="continue",
        reason="Previous round succeeded; reconcile_anchor_signals is active due to anchor coherence mismatch.",
        focus_areas=["build_on_success", "reconcile_anchor_signals"],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == ["build_on_success", "reconcile_anchor_signals"]


def test_derive_task_intent_maps_persistent_action_mode_divergence_resolution_to_analysis() -> None:
    plan = NextIterationPlan(
        next_objective="Resolve the persistent action-mode divergence before broader expansion.",
        strategy="continue",
        reason=(
            "Previous round succeeded; resolve_persistent_action_mode_divergence is active due to "
            "persistent unresolved action-mode divergence between scale_confident_anchor and "
            "recover_missing_artifacts."
        ),
        focus_areas=[
            "build_on_success",
            "reconcile_anchor_signals",
            "persistent_action_mode_divergence_resolution",
        ],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == [
        "build_on_success",
        "reconcile_anchor_signals",
        "persistent_action_mode_divergence_resolution",
    ]


def test_derive_task_intent_maps_persistent_coordination_divergence_resolution_to_analysis() -> None:
    plan = NextIterationPlan(
        next_objective="Resolve the persistent coordination divergence before broader expansion.",
        strategy="continue",
        reason=(
            "Previous round succeeded; resolve_persistent_coordination_divergence is active due to "
            "persistent unresolved coordination divergence; action-mode divergence between "
            "scale_confident_anchor and recover_missing_artifacts. anchor coherence expected "
            "h_primary but selected h_other."
        ),
        focus_areas=[
            "build_on_success",
            "reconcile_anchor_signals",
            "persistent_coordination_divergence_resolution",
        ],
    )

    intent = derive_task_intent(plan)

    assert intent.task_type == "analysis"
    assert intent.worker_preference == "any"
    assert intent.acceptance_emphasis == "scientific_validity"
    assert intent.focus_areas == [
        "build_on_success",
        "reconcile_anchor_signals",
        "persistent_coordination_divergence_resolution",
    ]
