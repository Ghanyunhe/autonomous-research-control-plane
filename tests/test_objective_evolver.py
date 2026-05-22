from __future__ import annotations

from controlplane.brain.objective_evolver import evolve_objective
from controlplane.brain.objective_evolver import plan_next_iteration
from controlplane.brain.objective_evolver import plan_next_iteration_with_candidate_transition


def _mentions_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def test_evolve_objective_returns_base_when_no_history() -> None:
    assert evolve_objective("Create metrics.json", None) == "Create metrics.json"


def test_evolve_objective_continue_uses_worker_summary() -> None:
    evolved = evolve_objective(
        "Create metrics.json",
        {
            "decision": "CONTINUE",
            "worker_result": {"summary": "metrics.json was created successfully"},
        },
    )
    assert "Create metrics.json" in evolved
    assert "metrics.json was created successfully" in evolved


def test_plan_next_iteration_returns_structured_refine_plan() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {"failures": ["missing_artifacts", "worker_not_successful"]},
        },
    )

    assert plan.strategy == "refine"
    assert "missing_artifacts" in plan.reason
    assert plan.focus_areas == ["missing_artifacts", "worker_not_successful"]
    assert "Refine the previous attempt" in plan.next_objective


def test_plan_next_iteration_refine_artifact_presence_targets_deliverables() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["missing_artifacts"],
                "failed_check_types": ["artifact_presence"],
                "rework_priority": "medium",
            },
        },
    )

    assert plan.strategy == "refine"
    assert plan.focus_areas == ["artifact_presence"]
    assert _mentions_any(plan.reason, ("missing", "output", "artifact", "deliverable", "recover"))
    assert _mentions_any(plan.next_objective, ("missing", "output", "artifact", "deliverable", "recover"))


def test_plan_next_iteration_refine_worker_execution_targets_stability() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["worker_not_successful"],
                "failed_check_types": ["worker_execution"],
                "rework_priority": "medium",
            },
        },
    )

    assert plan.focus_areas == ["worker_execution"]
    assert _mentions_any(plan.reason, ("execution", "worker", "runtime", "stability", "stabiliz", "recover"))
    assert _mentions_any(plan.next_objective, ("execution", "worker", "runtime", "stability", "stabiliz", "recover"))


def test_plan_next_iteration_refine_scientific_validity_targets_rigor() -> None:
    plan = plan_next_iteration(
        "Evaluate the hypothesis",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["insufficient_evidence"],
                "failed_check_types": ["scientific_validity"],
                "rework_priority": "low",
            },
        },
    )

    assert plan.focus_areas == ["scientific_validity"]
    assert _mentions_any(plan.reason, ("scientific", "evidence", "rigor", "validity", "method"))
    assert _mentions_any(plan.next_objective, ("scientific", "evidence", "rigor", "validity", "method"))


def test_plan_next_iteration_refine_high_priority_combines_structured_failures() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["missing_artifacts", "worker_not_successful"],
                "failed_check_types": ["artifact_presence", "worker_execution"],
                "rework_priority": "high",
            },
        },
    )

    assert plan.focus_areas == ["artifact_presence", "worker_execution"]
    assert plan.reason.startswith("High priority: ")
    assert "\n\nRefine the previous attempt. High priority: Focus on these remediation goals:" in plan.next_objective
    assert _mentions_any(plan.next_objective, ("missing", "output", "artifact", "deliverable", "recover"))
    assert _mentions_any(plan.next_objective, ("execution", "worker", "runtime", "stability", "stabiliz"))


def test_plan_next_iteration_refine_ignores_unknown_failed_check_types() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["missing_artifacts"],
                "failed_check_types": ["unknown_check", "artifact_presence", "unknown_check"],
                "rework_priority": "medium",
            },
        },
    )

    assert plan.strategy == "refine"
    assert plan.focus_areas == ["artifact_presence"]
    assert "unknown_check" not in plan.reason
    assert "unknown_check" not in plan.next_objective
    assert _mentions_any(plan.reason, ("artifact", "deliverable", "output", "recover"))


def test_plan_next_iteration_refine_falls_back_to_legacy_failures_when_structured_types_unrecognized() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "REFINE",
            "verification": {
                "failures": ["missing_artifacts", "worker_not_successful"],
                "failed_check_types": ["unknown_check", "another_unknown_check"],
                "rework_priority": "high",
            },
        },
    )

    assert plan.strategy == "refine"
    assert plan.focus_areas == ["missing_artifacts", "worker_not_successful"]
    assert plan.reason == "Previous round requested refinement because: missing_artifacts, worker_not_successful."
    assert plan.next_objective.endswith(
        "Refine the previous attempt. Explicitly address: missing_artifacts, worker_not_successful."
    )


def test_plan_next_iteration_defaults_to_continue_strategy_for_first_round() -> None:
    plan = plan_next_iteration("Create metrics.json", None)

    assert plan.strategy == "continue"
    assert plan.reason == "No prior iteration exists; start from the base objective."
    assert plan.focus_areas == []
    assert plan.next_objective == "Create metrics.json"


def test_plan_next_iteration_prefers_verifier_continue_over_decision() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "ESCALATE",
            "worker_result": {"summary": "metrics.json was created successfully"},
            "verification": {"recommended_brain_action": "CONTINUE"},
        },
    )

    assert plan.strategy == "continue"
    assert "metrics.json was created successfully" in plan.next_objective


def test_plan_next_iteration_prefers_verifier_refine_over_decision() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "REFINE",
                "failures": ["missing_artifacts"],
                "failed_check_types": ["artifact_presence"],
                "rework_priority": "medium",
            },
        },
    )

    assert plan.strategy == "refine"
    assert plan.focus_areas == ["artifact_presence"]


def test_plan_next_iteration_with_candidate_transition_mentions_new_refine_anchor() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Durable recovery objective",
        {
            "decision": "REFINE",
            "verification": {
                "recommended_brain_action": "REFINE",
                "failures": ["missing_artifacts"],
                "failed_check_types": ["artifact_presence"],
                "rework_priority": "medium",
            },
        },
        previous_objective="Seed backlog objective",
    )

    assert plan.strategy == "refine"
    assert plan.focus_areas == ["artifact_presence"]
    assert plan.next_objective.startswith("Durable recovery objective")
    assert "Refine the previous attempt" in plan.next_objective
    assert "newly selected candidate" in plan.reason


def test_plan_next_iteration_with_candidate_transition_mentions_expansion_recovery_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Healthier backlog objective",
        {
            "decision": "REFINE",
            "verification": {
                "recommended_brain_action": "REFINE",
                "failures": ["insufficient_evidence"],
                "failed_check_types": ["scientific_validity"],
                "rework_priority": "high",
            },
        },
        previous_objective="Blocked backlog objective",
        transition_context={
            "mode": "recovery",
            "backlog_action": "recover_regressing_candidate",
            "backlog_action_mode": "reroute_for_stronger_evidence",
            "hypothesis_action": "stabilize_regressing_hypothesis",
            "hypothesis_action_mode": "recover_missing_artifacts",
            "dominant_failure_mode": "scientific_validity",
            "backlog_selection_score_signals": {
                "status": "blocked",
                "phase": "regressing",
                "phase_strength": "medium",
                "trajectory_signal": "newly_regressing",
                "action_mode": "reroute_for_stronger_evidence",
            },
            "hypothesis_selection_score_signals": {
                "status": "unstable",
                "phase": "regressing",
                "phase_strength": "low",
                "trajectory_signal": "newly_regressing",
                "action_mode": "recover_missing_artifacts",
            },
            "backlog_alternative_anchor": {
                "experiment_id": "exp_alt",
                "reason": "recovering medium-confidence anchor",
                "score_signals": {
                    "status": "mixed",
                    "phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "promote_emerging_anchor",
                },
                "suppressed_by": "weaker_phase_strength",
                "frontier_age": "persistent",
                "frontier_trend": "rising",
            },
            "hypothesis_alternative_anchor": {
                "hypothesis_id": "h_alt",
                "reason": "stable low-confidence anchor",
                "score_signals": {
                    "status": "mixed",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "suppressed_by": "stale_trajectory",
                "frontier_age": "new",
                "frontier_trend": "holding",
            },
            "hypothesis_alternative_scope": "active_frontier",
        },
    )

    assert plan.strategy == "refine"
    assert plan.next_objective.startswith("Healthier backlog objective")
    assert "Use the new candidate as the recovery anchor" in plan.next_objective
    assert "prioritize scientific_validity recovery" in plan.next_objective
    assert "recover_regressing_candidate" in plan.next_objective
    assert "execute reroute_for_stronger_evidence" in plan.next_objective
    assert "stabilize_regressing_hypothesis" in plan.next_objective
    assert "execute recover_missing_artifacts" in plan.next_objective
    assert "using a blocked / regressing / medium / newly_regressing selected anchor" in plan.next_objective
    assert "using a unstable / regressing / low / newly_regressing selected hypothesis anchor" in plan.next_objective
    assert "keep exp_alt in reserve as a persistent backlog alternative that is rising in the frontier" in plan.next_objective
    assert "with recovering / medium / newly_recovering signals" in plan.next_objective
    assert "while it remains suppressed by weaker_phase_strength" in plan.next_objective
    assert "keep h_alt in reserve as a newly-entered active hypothesis alternative that is holding its frontier position" in plan.next_objective
    assert "with stable / low / stale_stable signals" in plan.next_objective
    assert "while it remains suppressed by stale_trajectory" in plan.next_objective
    assert "newly selected candidate" in plan.reason
    assert "expansion-state recovery guidance" in plan.reason
    assert "recover_regressing_candidate" in plan.reason
    assert "backlog action mode reroute_for_stronger_evidence" in plan.reason
    assert "stabilize_regressing_hypothesis" in plan.reason
    assert "hypothesis action mode recover_missing_artifacts" in plan.reason
    assert "dominant failure mode scientific_validity" in plan.reason
    assert "selected anchor score signals status blocked, phase regressing, phase strength medium, trajectory newly_regressing, action mode reroute_for_stronger_evidence" in plan.reason
    assert "selected hypothesis anchor score signals status unstable, phase regressing, phase strength low, trajectory newly_regressing, action mode recover_missing_artifacts" in plan.reason
    assert "backlog alternative exp_alt is currently suppressed by weaker_phase_strength" in plan.reason
    assert "and remains persistent in the frontier" in plan.reason
    assert "while rising in the frontier" in plan.reason
    assert "active hypothesis alternative h_alt is currently suppressed by stale_trajectory" in plan.reason
    assert "and is newly entering the frontier" in plan.reason
    assert "while holding its frontier position" in plan.reason
    assert "scientific_validity" in plan.focus_areas
    assert "recover_regressing_candidate" in plan.focus_areas
    assert "reroute_for_stronger_evidence" in plan.focus_areas
    assert "stabilize_regressing_hypothesis" in plan.focus_areas
    assert "recover_missing_artifacts" in plan.focus_areas
    assert "Blocked backlog objective" in plan.reason


def test_plan_next_iteration_with_candidate_transition_mentions_phase_aware_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Accelerating backlog objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Stable backlog objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "stable",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
        },
    )

    assert plan.strategy == "continue"
    assert plan.next_objective.startswith("Accelerating backlog objective")
    assert "accelerating backlog trajectory" in plan.next_objective
    assert "phase-aware expansion guidance" in plan.reason
    assert "backlog phase accelerating" in plan.reason
    assert "hypothesis phase stable" in plan.reason
    assert "backlog phase strength high" in plan.reason
    assert "hypothesis phase strength medium" in plan.reason
    assert "promote_promising_candidate" in plan.reason
    assert "promote_supported_hypothesis" in plan.reason
    assert "high-confidence accelerating backlog trajectory" in plan.next_objective
    assert "medium-confidence stable hypothesis trajectory" in plan.next_objective
    assert "accelerating" in plan.focus_areas
    assert "stable" in plan.focus_areas
    assert "high" in plan.focus_areas
    assert "medium" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_low_confidence_validation_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Validation backlog objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_phase_signal": "stable",
            "hypothesis_phase_signal": "stable",
            "backlog_phase_strength_signal": "low",
            "hypothesis_phase_strength_signal": "low",
            "expansion_confidence_action": "validate_low_confidence_anchor",
        },
    )

    assert plan.strategy == "continue"
    assert "low-confidence stable backlog trajectory" in plan.next_objective
    assert "Validate the anchor before broader expansion" in plan.next_objective
    assert "validate_low_confidence_anchor" in plan.reason
    assert "validate_before_expansion" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_recommended_action_modes() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Action-mode backlog objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "accelerating",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
        },
    )

    assert plan.strategy == "continue"
    assert "backlog action mode scale_confident_anchor" in plan.reason
    assert "hypothesis action mode promote_emerging_anchor" in plan.reason
    assert "scale_confident_anchor" in plan.focus_areas
    assert "promote_emerging_anchor" in plan.focus_areas
    assert "execute the backlog action mode scale_confident_anchor" in plan.next_objective
    assert "execute the hypothesis action mode promote_emerging_anchor" in plan.next_objective


def test_plan_next_iteration_with_candidate_transition_mentions_trajectory_signals() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Recovery-oriented objective",
        None,
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "stabilize_recovering_candidate",
            "backlog_action_mode": "stabilize_recovery",
            "backlog_phase_signal": "recovering",
            "backlog_phase_strength_signal": "medium",
            "backlog_trajectory_signal": "newly_recovering",
            "hypothesis_action": "promote_supported_hypothesis",
            "hypothesis_action_mode": "validate_low_confidence_anchor",
            "hypothesis_phase_signal": "stable",
            "hypothesis_phase_strength_signal": "low",
            "hypothesis_trajectory_signal": "stale_stable",
        },
    )

    assert plan.strategy == "continue"
    assert "backlog trajectory newly_recovering" in plan.reason
    assert "hypothesis trajectory stale_stable" in plan.reason
    assert "newly_recovering" in plan.focus_areas
    assert "stale_stable" in plan.focus_areas
    assert "focus on the newly_recovering backlog trajectory" in plan.next_objective
    assert "avoid relying only on the stale_stable hypothesis trajectory" in plan.next_objective


def test_plan_next_iteration_with_candidate_transition_mentions_selection_context() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Selection-context objective",
        None,
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "backlog_phase_signal": "stable",
            "backlog_phase_strength_signal": "low",
            "backlog_selection_source": "backlog_file",
            "backlog_selection_mode": "tracked_reprioritization",
            "backlog_selection_score_signals": {
                "status": "promising",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "hypothesis_selection_score_signals": {
                "status": "supported",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "selection source backlog_file" in plan.reason
    assert "selection mode tracked_reprioritization" in plan.reason
    assert "selected anchor score signals status promising, phase stable, phase strength low, trajectory stale_stable, action mode validate_low_confidence_anchor" in plan.reason
    assert "selected hypothesis anchor score signals status supported, phase stable, phase strength low, trajectory stale_stable, action mode validate_low_confidence_anchor" in plan.reason
    assert "selected from backlog_file" in plan.next_objective
    assert "via tracked_reprioritization" in plan.next_objective
    assert "using a promising / stable / low / stale_stable selected anchor" in plan.next_objective
    assert "using a supported / stable / low / stale_stable selected hypothesis anchor" in plan.next_objective


def test_plan_next_iteration_with_candidate_transition_mentions_frontier_pressure_selection_context() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Pressure-context objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "scale_confident_anchor",
            "backlog_selection_score_signals": {
                "status": "promising",
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
            },
            "hypothesis_selection_score_signals": {
                "status": "supported",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "used_backlog_frontier_pressure": True,
            "used_hypothesis_frontier_pressure": True,
        },
    )

    assert plan.strategy == "continue"
    assert "backlog frontier pressure influenced the selected candidate transition" in plan.reason
    assert "hypothesis frontier pressure influenced the selected candidate transition" in plan.reason
    assert "Preserve the pressure-driven backlog reprioritization signal" in plan.next_objective
    assert "Preserve the pressure-driven hypothesis reprioritization signal" in plan.next_objective
    assert "frontier_pressure_backlog" in plan.focus_areas
    assert "frontier_pressure_hypothesis" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_recommendation_state_hints() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Recommendation-context objective",
        None,
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "scale_confident_anchor",
            "backlog_phase_signal": "accelerating",
            "backlog_phase_strength_signal": "high",
            "backlog_trajectory_signal": "strong_acceleration",
            "backlog_recommendation_drivers": {
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
                "status": "promising",
                "recommendation_state_hint": "promising / accelerating / high / strong_acceleration / scale_confident_anchor recommended anchor",
            },
            "hypothesis_action": "promote_supported_hypothesis",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "hypothesis_phase_signal": "accelerating",
            "hypothesis_phase_strength_signal": "medium",
            "hypothesis_trajectory_signal": "newly_accelerating",
            "hypothesis_recommendation_drivers": {
                "phase": "accelerating",
                "phase_strength": "medium",
                "trajectory_signal": "newly_accelerating",
                "action_mode": "promote_emerging_anchor",
                "status": "supported",
                "recommendation_state_hint": "supported / accelerating / medium / newly_accelerating / promote_emerging_anchor recommended hypothesis anchor",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "backlog recommendation state hint promising / accelerating / high / strong_acceleration / scale_confident_anchor recommended anchor" in plan.reason
    assert "hypothesis recommendation state hint supported / accelerating / medium / newly_accelerating / promote_emerging_anchor recommended hypothesis anchor" in plan.reason
    assert "guided by the promising / accelerating / high / strong_acceleration / scale_confident_anchor recommended anchor" in plan.next_objective
    assert "guided by the supported / accelerating / medium / newly_accelerating / promote_emerging_anchor recommended hypothesis anchor" in plan.next_objective


def test_plan_next_iteration_with_candidate_transition_mentions_alternative_anchor_context() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Selection-context objective",
        {
            "objective": "Fallback objective",
            "decision": "CONTINUE",
            "verification": {"status": "accept", "failed_check_types": []},
            "worker_result": {"summary": "created metrics.json"},
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "backlog_selection_source": "backlog_file",
            "backlog_selection_mode": "tracked_reprioritization",
            "backlog_alternative_anchor": {
                "experiment_id": "exp_alt",
                "reason": "recovering medium-confidence anchor",
                "score_signals": {
                    "status": "mixed",
                    "phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "promote_emerging_anchor",
                },
                "suppressed_by": "weaker_phase_strength",
                "frontier_age": "persistent",
                "frontier_trend": "rising",
            },
            "hypothesis_alternative_anchor": {
                "hypothesis_id": "h_alt",
                "reason": "stable low-confidence anchor",
                "score_signals": {
                    "status": "mixed",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "suppressed_by": "stale_trajectory",
                "frontier_age": "new",
                "frontier_trend": "holding",
            },
            "hypothesis_alternative_scope": "active_frontier",
        },
    )

    assert plan.strategy == "continue"
    assert "backlog alternative exp_alt is currently suppressed by weaker_phase_strength" in plan.reason
    assert "and remains persistent in the frontier" in plan.reason
    assert "while rising in the frontier" in plan.reason
    assert "alternative exp_alt score signals status mixed, phase recovering, phase strength medium, trajectory newly_recovering, action mode promote_emerging_anchor" in plan.reason
    assert "active hypothesis alternative h_alt is currently suppressed by stale_trajectory" in plan.reason
    assert "and is newly entering the frontier" in plan.reason
    assert "while holding its frontier position" in plan.reason
    assert "alternative h_alt score signals status mixed, phase stable, phase strength low, trajectory stale_stable, action mode validate_low_confidence_anchor" in plan.reason
    assert "Keep exp_alt in reserve as a persistent backlog alternative that is rising in the frontier" in plan.next_objective
    assert "with recovering / medium / newly_recovering signals" in plan.next_objective
    assert "Keep h_alt in reserve as a newly-entered active hypothesis alternative that is holding its frontier position" in plan.next_objective
    assert "with stable / low / stale_stable signals" in plan.next_objective
    assert "alternative_exp_alt" not in plan.focus_areas
    assert "alternative_h_alt" not in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_hypothesis_projection_provenance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Hypothesis-provenance objective",
        None,
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "hypothesis_action": "promote_supported_hypothesis",
            "hypothesis_action_mode": "validate_low_confidence_anchor",
            "hypothesis_projection_experiment_id": "exp_best",
            "hypothesis_selection_source": "backlog_candidate_links",
            "hypothesis_selection_mode": "selected_candidate_projection",
        },
    )

    assert plan.strategy == "continue"
    assert "hypothesis projection from experiment exp_best" in plan.reason
    assert "hypothesis selection source backlog_candidate_links" in plan.reason
    assert "hypothesis selection mode selected_candidate_projection" in plan.reason
    assert "use hypothesis context projected from experiment exp_best" in plan.next_objective
    assert "keep the selected_candidate_projection hypothesis context active" in plan.next_objective
    assert "hypothesis_projection_exp_best" not in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_hypothesis_reprioritization_provenance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Hypothesis-reprioritization objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "hypothesis_action": "promote_supported_hypothesis",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "hypothesis_selection_source": "durable_state",
            "hypothesis_selection_mode": "tracked_reprioritization",
            "used_hypothesis_frontier_pressure": True,
        },
    )

    assert plan.strategy == "continue"
    assert "hypothesis selection source durable_state" in plan.reason
    assert "hypothesis selection mode tracked_reprioritization" in plan.reason
    assert "hypothesis frontier pressure influenced the selected candidate transition" in plan.reason
    assert "keep the tracked_reprioritization hypothesis context active" in plan.next_objective
    assert "Preserve the pressure-driven hypothesis reprioritization signal" in plan.next_objective


def test_plan_next_iteration_with_candidate_transition_mentions_hypothesis_projection_in_recovery() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Recovery objective",
        {
            "decision": "REFINE",
            "verification": {
                "recommended_brain_action": "REFINE",
                "status": "rework",
                "failed_check_types": ["scientific_validity"],
            },
        },
        previous_objective="Prior recovery objective",
        transition_context={
            "mode": "recovery",
            "backlog_action": "recover_regressing_candidate",
            "hypothesis_action": "stabilize_regressing_hypothesis",
            "dominant_failure_mode": "scientific_validity",
            "hypothesis_projection_experiment_id": "exp_best",
            "hypothesis_selection_source": "backlog_candidate_links",
            "hypothesis_selection_mode": "selected_candidate_projection",
        },
    )

    assert plan.strategy == "refine"
    assert "hypothesis projection from experiment exp_best" in plan.reason
    assert "hypothesis selection source backlog_candidate_links" in plan.reason
    assert "hypothesis selection mode selected_candidate_projection" in plan.reason
    assert "use hypothesis context projected from experiment exp_best" in plan.next_objective
    assert "keep the selected_candidate_projection hypothesis context active" in plan.next_objective
    assert "hypothesis_projection_exp_best" not in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_reconcile_anchor_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Divergent anchor objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action": "stabilize_recovering_hypothesis",
            "hypothesis_action_mode": "recover_missing_artifacts",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "reconcile_anchor_signals",
        },
    )

    assert plan.strategy == "continue"
    assert "reconcile_anchor_signals" in plan.reason
    assert "Reconcile backlog and hypothesis signals before broader expansion" in plan.next_objective
    assert "reconcile_anchor_signals" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_pending_promotion_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Pending-promotion objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "investigate_pending_candidate_promotion",
            "hypothesis_action": "investigate_pending_hypothesis_promotion",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "resolve_persistent_pending_promotion_pair",
            "joint_pending_promotion_pair": {
                "experiment_id": "exp_alt",
                "hypothesis_id": "h_alt",
                "gate_blockers": ["challenger_recent_rework"],
                "pressure_streak": 2,
                "pending_state": "persistent",
            },
            "pending_promotion_candidate_id": "exp_alt",
            "pending_promotion_hypothesis_id": "h_alt",
            "pending_promotion_gate_blockers": ["challenger_recent_rework"],
        },
    )

    assert plan.strategy == "continue"
    assert "resolve_persistent_pending_promotion_pair" in plan.reason
    assert "pending promotion candidate exp_alt" in plan.reason
    assert "pending promotion hypothesis h_alt" in plan.reason
    assert "joint pending promotion pair exp_alt/h_alt is persistent" in plan.reason
    assert "challenger_recent_rework" in plan.reason
    assert "Resolve the persistently blocked promotion pair before broader expansion." in plan.next_objective
    assert "persistent_pending_promotion_pair_resolution" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_pending_promotion_guidance_without_duplication() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Pending-promotion objective",
        None,
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "investigate_pending_candidate_promotion",
            "expansion_confidence_action": "investigate_pending_promotions",
            "pending_promotion_candidate_id": "exp_alt",
            "pending_promotion_gate_blockers": ["challenger_recent_rework"],
        },
    )

    assert plan.reason.count("investigate_pending_promotions") == 1
    assert plan.next_objective.count("Investigate the blocked promotion signals before broader expansion.") == 1


def test_plan_next_iteration_with_candidate_transition_mentions_anchor_coherence_reconcile_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Coherence objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "hypothesis_action_mode": "validate_low_confidence_anchor",
            "backlog_phase_signal": "stable",
            "hypothesis_phase_signal": "stable",
            "backlog_phase_strength_signal": "low",
            "hypothesis_phase_strength_signal": "low",
            "expansion_confidence_action": "reconcile_anchor_signals",
            "anchor_coherence": "divergent",
            "anchor_coherence_expected_hypothesis_ids": ["h_primary"],
            "anchor_coherence_selected_hypothesis_id": "h_other",
        },
    )

    assert plan.strategy == "continue"
    assert "reconcile_anchor_signals" in plan.reason
    assert "anchor coherence expected h_primary but selected h_other" in plan.reason
    assert "Reconcile backlog and hypothesis signals before broader expansion" in plan.next_objective
    assert "reconcile_anchor_signals" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_persistent_anchor_divergence_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Persistent coherence objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_action_mode": "validate_low_confidence_anchor",
            "hypothesis_action_mode": "validate_low_confidence_anchor",
            "backlog_phase_signal": "stable",
            "hypothesis_phase_signal": "stable",
            "backlog_phase_strength_signal": "low",
            "hypothesis_phase_strength_signal": "low",
            "expansion_confidence_action": "resolve_persistent_anchor_divergence",
            "anchor_coherence": "divergent",
            "anchor_coherence_expected_hypothesis_ids": ["h_primary"],
            "anchor_coherence_selected_hypothesis_id": "h_other",
            "anchor_divergence_memory": {
                "expected_hypothesis_ids": ["h_primary"],
                "selected_hypothesis_id": "h_other",
                "divergence_streak": 2,
                "divergence_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "persistent unresolved anchor divergence" in plan.reason
    assert "resolve_persistent_anchor_divergence" in plan.reason
    assert "anchor coherence expected h_primary but selected h_other" in plan.reason
    assert "Resolve the persistent anchor divergence before broader expansion" in plan.next_objective
    assert "persistent_anchor_divergence_resolution" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_persistent_action_mode_divergence_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Persistent action-mode divergence objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "stabilize_recovering_hypothesis",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "recover_missing_artifacts",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "resolve_persistent_action_mode_divergence",
            "action_mode_divergence_memory": {
                "backlog_action_mode": "scale_confident_anchor",
                "hypothesis_action_mode": "recover_missing_artifacts",
                "divergence_streak": 2,
                "divergence_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "resolve_persistent_action_mode_divergence" in plan.reason
    assert "persistent unresolved action-mode divergence" in plan.reason
    assert "action-mode divergence between scale_confident_anchor and recover_missing_artifacts" in plan.reason
    assert "Resolve the persistent action-mode divergence before broader expansion." in plan.next_objective
    assert "persistent_action_mode_divergence_resolution" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_persistent_coordination_divergence_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Persistent coordination divergence objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "stabilize_recovering_hypothesis",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "recover_missing_artifacts",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "resolve_persistent_coordination_divergence",
            "anchor_coherence": "divergent",
            "anchor_coherence_expected_hypothesis_ids": ["h_primary"],
            "anchor_coherence_selected_hypothesis_id": "h_other",
            "anchor_divergence_memory": {
                "expected_hypothesis_ids": ["h_primary"],
                "selected_hypothesis_id": "h_other",
                "divergence_streak": 2,
                "divergence_state": "persistent",
            },
            "action_mode_divergence_memory": {
                "backlog_action_mode": "scale_confident_anchor",
                "hypothesis_action_mode": "recover_missing_artifacts",
                "divergence_streak": 2,
                "divergence_state": "persistent",
            },
            "persistent_coordination_divergence": {
                "expected_hypothesis_ids": ["h_primary"],
                "selected_hypothesis_id": "h_other",
                "backlog_action_mode": "scale_confident_anchor",
                "hypothesis_action_mode": "recover_missing_artifacts",
                "divergence_streak": 2,
                "divergence_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "resolve_persistent_coordination_divergence" in plan.reason
    assert "persistent unresolved coordination divergence" in plan.reason
    assert "anchor coherence expected h_primary but selected h_other" in plan.reason
    assert "action-mode divergence between scale_confident_anchor and recover_missing_artifacts" in plan.reason
    assert "Resolve the persistent coordination divergence before broader expansion." in plan.next_objective
    assert "persistent_coordination_divergence_resolution" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_persistent_joint_reserve_memory_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Persistent reserve objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_promising_candidate",
            "hypothesis_action": "promote_supported_hypothesis",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "accelerating",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "resolve_persistent_joint_reserve_memory",
            "persistent_joint_reserve_memory": {
                "experiment_id": "exp_reserve",
                "hypothesis_id": "h_reserve",
                "backlog_frontier_age": "persistent",
                "backlog_frontier_trend": "rising",
                "backlog_suppressed_by": "stale_trajectory",
                "hypothesis_frontier_age": "persistent",
                "hypothesis_frontier_trend": "rising",
                "hypothesis_suppressed_by": "weaker_phase_strength",
                "reserve_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "resolve_persistent_joint_reserve_memory" in plan.reason
    assert "persistent joint reserve memory" in plan.reason
    assert "exp_reserve/h_reserve" in plan.reason
    assert "Resolve the persistent joint reserve memory before broader expansion." in plan.next_objective
    assert "persistent_joint_reserve_memory_resolution" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_promotion_ready_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Promotion-ready objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "promote_ready_candidate",
            "hypothesis_action": "promote_ready_hypothesis",
            "backlog_action_mode": "scale_confident_anchor",
            "hypothesis_action_mode": "promote_emerging_anchor",
            "backlog_phase_signal": "accelerating",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "high",
            "hypothesis_phase_strength_signal": "high",
            "expansion_confidence_action": "advance_persistent_promotion_ready_pair",
            "promotion_ready_candidate_id": "exp_alt",
            "promotion_ready_hypothesis_id": "h_alt",
            "joint_promotion_ready_pair": {
                "experiment_id": "exp_alt",
                "hypothesis_id": "h_alt",
                "pressure_streak": 2,
                "readiness_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "advance_persistent_promotion_ready_pair" in plan.reason
    assert "promotion-ready candidate exp_alt" in plan.reason
    assert "promotion-ready hypothesis h_alt" in plan.reason
    assert "joint promotion-ready pair exp_alt/h_alt" in plan.reason
    assert "is persistent" in plan.reason
    assert "Advance the persistently gate-cleared challenger pair before broader expansion." in plan.next_objective
    assert "persistent_promotion_ready_pair_advancement" in plan.focus_areas


def test_plan_next_iteration_with_candidate_transition_mentions_joint_recovery_pair_guidance() -> None:
    plan = plan_next_iteration_with_candidate_transition(
        "Recovery-pair objective",
        {
            "decision": "CONTINUE",
            "verification": {
                "recommended_brain_action": "CONTINUE",
                "status": "accept",
            },
        },
        previous_objective="Fallback objective",
        transition_context={
            "mode": "continuation",
            "backlog_action": "recover_regressing_candidate",
            "hypothesis_action": "stabilize_regressing_hypothesis",
            "backlog_action_mode": "reroute_for_stronger_evidence",
            "hypothesis_action_mode": "reroute_for_stronger_evidence",
            "backlog_phase_signal": "recovering",
            "hypothesis_phase_signal": "recovering",
            "backlog_phase_strength_signal": "medium",
            "hypothesis_phase_strength_signal": "medium",
            "expansion_confidence_action": "stabilize_persistent_joint_recovery_pair",
            "joint_recovery_pair": {
                "experiment_id": "exp_recover",
                "hypothesis_id": "h_recover",
                "failure_mode": "scientific_validity",
                "recovery_state": "persistent",
            },
        },
    )

    assert plan.strategy == "continue"
    assert "stabilize_persistent_joint_recovery_pair" in plan.reason
    assert "joint recovery pair exp_recover/h_recover is persistent" in plan.reason
    assert "scientific_validity" in plan.reason
    assert "Stabilize the persistently aligned recovery pair before broader expansion." in plan.next_objective
    assert "persistent_joint_recovery_pair_stabilization" in plan.focus_areas


def test_plan_next_iteration_uses_hold_for_verifier_escalate() -> None:
    base_objective = "Create metrics.json"
    plan = plan_next_iteration(
        base_objective,
        {
            "decision": "CONTINUE",
            "verification": {"recommended_brain_action": "ESCALATE"},
        },
    )

    assert plan.strategy == "hold"
    assert plan.next_objective == base_objective
    assert plan.focus_areas == []
    assert "ESCALATE" in plan.reason


def test_plan_next_iteration_uses_hold_for_verifier_stop() -> None:
    base_objective = "Create metrics.json"
    plan = plan_next_iteration(
        base_objective,
        {
            "decision": "CONTINUE",
            "verification": {"recommended_brain_action": "STOP"},
        },
    )

    assert plan.strategy == "hold"
    assert plan.next_objective == base_objective
    assert plan.focus_areas == []
    assert "STOP" in plan.reason


def test_plan_next_iteration_uses_hold_for_verifier_pivot() -> None:
    base_objective = "Create metrics.json"
    plan = plan_next_iteration(
        base_objective,
        {
            "decision": "CONTINUE",
            "verification": {"recommended_brain_action": "PIVOT"},
        },
    )

    assert plan.strategy == "hold"
    assert plan.next_objective == base_objective
    assert plan.focus_areas == []
    assert "PIVOT" in plan.reason


def test_plan_next_iteration_preserves_legacy_hold_fallback_without_verifier_action() -> None:
    base_objective = "Create metrics.json"
    plan = plan_next_iteration(
        base_objective,
        {
            "decision": "ESCALATE",
            "verification": {},
        },
    )

    assert plan.strategy == "hold"
    assert plan.next_objective == base_objective
    assert plan.focus_areas == []
    assert plan.reason == "Previous decision was ESCALATE, so the base objective is retained."
