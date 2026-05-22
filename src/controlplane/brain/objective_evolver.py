from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NextIterationPlan:
    next_objective: str
    strategy: str
    reason: str
    focus_areas: list[str]


STRUCTURED_REFINEMENT_GUIDANCE: dict[str, dict[str, str]] = {
    "artifact_presence": {
        "reason": "recover missing outputs and restore required artifacts or deliverables",
        "objective": "Recover missing outputs and produce the required artifacts or deliverables.",
    },
    "worker_execution": {
        "reason": "stabilize worker execution and improve runtime recovery",
        "objective": "Stabilize worker execution and improve runtime recovery so the task completes reliably.",
    },
    "scientific_validity": {
        "reason": "strengthen evidence, rigor, validity, and method quality",
        "objective": "Improve the supporting evidence, scientific rigor, validity, and method quality.",
    },
}


def plan_next_iteration(base_objective: str, last_record: dict | None) -> NextIterationPlan:
    return _plan_next_iteration(base_objective, last_record, candidate_transition=None)


def _plan_next_iteration(
    base_objective: str,
    last_record: dict | None,
    candidate_transition: dict | None,
) -> NextIterationPlan:
    if not last_record:
        if candidate_transition and candidate_transition.get("changed"):
            expansion_focus_areas: list[str] = []
            expansion_transition_reason = ""
            expansion_objective_suffix = ""
            backlog_action = candidate_transition.get("backlog_action")
            backlog_action_mode = candidate_transition.get("backlog_action_mode")
            hypothesis_action = candidate_transition.get("hypothesis_action")
            hypothesis_action_mode = candidate_transition.get("hypothesis_action_mode")
            backlog_phase_signal = candidate_transition.get("backlog_phase_signal")
            hypothesis_phase_signal = candidate_transition.get("hypothesis_phase_signal")
            backlog_phase_strength_signal = candidate_transition.get("backlog_phase_strength_signal")
            hypothesis_phase_strength_signal = candidate_transition.get("hypothesis_phase_strength_signal")
            backlog_trajectory_signal = candidate_transition.get("backlog_trajectory_signal")
            hypothesis_trajectory_signal = candidate_transition.get("hypothesis_trajectory_signal")
            expansion_confidence_action = candidate_transition.get("expansion_confidence_action")
            backlog_selection_source = candidate_transition.get("backlog_selection_source")
            backlog_selection_mode = candidate_transition.get("backlog_selection_mode")
            backlog_selection_score_signals = candidate_transition.get("backlog_selection_score_signals") or {}
            used_backlog_frontier_pressure = bool(candidate_transition.get("used_backlog_frontier_pressure"))
            backlog_recommendation_drivers = candidate_transition.get("backlog_recommendation_drivers") or {}
            backlog_alternative_anchor = candidate_transition.get("backlog_alternative_anchor") or {}
            hypothesis_alternative_anchor = candidate_transition.get("hypothesis_alternative_anchor") or {}
            hypothesis_alternative_scope = candidate_transition.get("hypothesis_alternative_scope")
            hypothesis_projection_experiment_id = candidate_transition.get("hypothesis_projection_experiment_id")
            hypothesis_selection_source = candidate_transition.get("hypothesis_selection_source")
            hypothesis_selection_mode = candidate_transition.get("hypothesis_selection_mode")
            hypothesis_selection_score_signals = candidate_transition.get("hypothesis_selection_score_signals") or {}
            used_hypothesis_frontier_pressure = bool(candidate_transition.get("used_hypothesis_frontier_pressure"))
            hypothesis_recommendation_drivers = candidate_transition.get("hypothesis_recommendation_drivers") or {}
            pending_promotion_candidate_id = candidate_transition.get("pending_promotion_candidate_id")
            pending_promotion_hypothesis_id = candidate_transition.get("pending_promotion_hypothesis_id")
            pending_promotion_gate_blockers = list(candidate_transition.get("pending_promotion_gate_blockers") or [])
            joint_pending_promotion_pair = candidate_transition.get("joint_pending_promotion_pair") or {}
            promotion_ready_candidate_id = candidate_transition.get("promotion_ready_candidate_id")
            promotion_ready_hypothesis_id = candidate_transition.get("promotion_ready_hypothesis_id")
            joint_promotion_ready_pair = candidate_transition.get("joint_promotion_ready_pair") or {}
            joint_recovery_pair = candidate_transition.get("joint_recovery_pair") or {}
            anchor_coherence = candidate_transition.get("anchor_coherence")
            anchor_coherence_expected_hypothesis_ids = list(
                candidate_transition.get("anchor_coherence_expected_hypothesis_ids") or []
            )
            anchor_coherence_selected_hypothesis_id = candidate_transition.get(
                "anchor_coherence_selected_hypothesis_id"
            )
            anchor_divergence_memory = candidate_transition.get("anchor_divergence_memory") or {}

            phase_details = []
            if backlog_phase_signal:
                phase_details.append(f"backlog phase {backlog_phase_signal}")
                if backlog_phase_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_phase_signal)
            if backlog_phase_strength_signal:
                phase_details.append(f"backlog phase strength {backlog_phase_strength_signal}")
                if backlog_phase_strength_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_phase_strength_signal)
            if backlog_trajectory_signal:
                phase_details.append(f"backlog trajectory {backlog_trajectory_signal}")
                if backlog_trajectory_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_trajectory_signal)
            if hypothesis_phase_signal:
                phase_details.append(f"hypothesis phase {hypothesis_phase_signal}")
                if hypothesis_phase_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_phase_signal)
            if hypothesis_phase_strength_signal:
                phase_details.append(f"hypothesis phase strength {hypothesis_phase_strength_signal}")
                if hypothesis_phase_strength_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_phase_strength_signal)
            if hypothesis_trajectory_signal:
                phase_details.append(f"hypothesis trajectory {hypothesis_trajectory_signal}")
                if hypothesis_trajectory_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_trajectory_signal)
            if backlog_action:
                phase_details.append(f"backlog recommendation {backlog_action}")
                if backlog_action not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_action)
            if backlog_action_mode:
                phase_details.append(f"backlog action mode {backlog_action_mode}")
                if backlog_action_mode not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_action_mode)
            if hypothesis_action:
                phase_details.append(f"hypothesis recommendation {hypothesis_action}")
                if hypothesis_action not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_action)
            if hypothesis_action_mode:
                phase_details.append(f"hypothesis action mode {hypothesis_action_mode}")
                if hypothesis_action_mode not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_action_mode)
            if expansion_confidence_action:
                phase_details.append(f"expansion confidence action {expansion_confidence_action}")
                if expansion_confidence_action not in expansion_focus_areas:
                    expansion_focus_areas.append(expansion_confidence_action)
            joint_pending_candidate_id = joint_pending_promotion_pair.get("experiment_id")
            joint_pending_hypothesis_id = joint_pending_promotion_pair.get("hypothesis_id")
            joint_pending_state = joint_pending_promotion_pair.get("pending_state")
            if joint_pending_candidate_id and joint_pending_hypothesis_id:
                detail = f"joint pending promotion pair {joint_pending_candidate_id}/{joint_pending_hypothesis_id}"
                if joint_pending_state:
                    detail = f"{detail} is {joint_pending_state}"
                phase_details.append(detail)
            joint_promotion_ready_candidate_id = joint_promotion_ready_pair.get("experiment_id")
            joint_promotion_ready_hypothesis_id = joint_promotion_ready_pair.get("hypothesis_id")
            if joint_promotion_ready_candidate_id and joint_promotion_ready_hypothesis_id:
                phase_details.append(
                    "joint promotion-ready pair "
                    f"{joint_promotion_ready_candidate_id}/{joint_promotion_ready_hypothesis_id}"
                )
            joint_recovery_candidate_id = joint_recovery_pair.get("experiment_id")
            joint_recovery_hypothesis_id = joint_recovery_pair.get("hypothesis_id")
            joint_recovery_failure_mode = joint_recovery_pair.get("failure_mode")
            joint_recovery_state = joint_recovery_pair.get("recovery_state")
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id:
                detail = f"joint recovery pair {joint_recovery_candidate_id}/{joint_recovery_hypothesis_id}"
                if joint_recovery_state:
                    detail = f"{detail} is {joint_recovery_state}"
                if joint_recovery_failure_mode:
                    detail = f"{detail} for {joint_recovery_failure_mode}"
                phase_details.append(detail)
            if (
                anchor_coherence == "divergent"
                and anchor_coherence_expected_hypothesis_ids
                and anchor_coherence_selected_hypothesis_id
            ):
                phase_details.append(
                    "anchor coherence expected "
                    f"{', '.join(anchor_coherence_expected_hypothesis_ids)} but selected "
                    f"{anchor_coherence_selected_hypothesis_id}"
                )
            if backlog_selection_source:
                phase_details.append(f"selection source {backlog_selection_source}")
            if backlog_selection_mode:
                phase_details.append(f"selection mode {backlog_selection_mode}")
            if backlog_selection_score_signals:
                signal_fragments = []
                if backlog_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_selection_score_signals['status']}")
                if backlog_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_selection_score_signals['phase']}")
                if backlog_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_selection_score_signals['phase_strength']}"
                    )
                if backlog_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_selection_score_signals['trajectory_signal']}"
                    )
                if backlog_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"selected anchor score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_selection_score_signals:
                signal_fragments = []
                if hypothesis_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_selection_score_signals['status']}")
                if hypothesis_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_selection_score_signals['phase']}")
                if hypothesis_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_selection_score_signals['phase_strength']}"
                    )
                if hypothesis_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_selection_score_signals['trajectory_signal']}"
                    )
                if hypothesis_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"selected hypothesis anchor score signals {', '.join(signal_fragments)}"
                    )
            if used_backlog_frontier_pressure:
                phase_details.append("backlog frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_backlog" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_backlog")
            if used_hypothesis_frontier_pressure:
                phase_details.append("hypothesis frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_hypothesis" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_hypothesis")
            backlog_alternative_id = backlog_alternative_anchor.get("experiment_id")
            backlog_alternative_reason = backlog_alternative_anchor.get("reason")
            backlog_alternative_score_signals = backlog_alternative_anchor.get("score_signals") or {}
            backlog_alternative_suppressed_by = backlog_alternative_anchor.get("suppressed_by")
            backlog_alternative_frontier_age = backlog_alternative_anchor.get("frontier_age")
            backlog_alternative_frontier_trend = backlog_alternative_anchor.get("frontier_trend")
            if backlog_alternative_id and backlog_alternative_suppressed_by:
                detail = (
                    f"backlog alternative {backlog_alternative_id} is currently suppressed by "
                    f"{backlog_alternative_suppressed_by}"
                )
                if backlog_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif backlog_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if backlog_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif backlog_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif backlog_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if backlog_alternative_reason:
                    detail = f"{detail} ({backlog_alternative_reason})"
                phase_details.append(detail)
            if backlog_alternative_id and backlog_alternative_score_signals:
                signal_fragments = []
                if backlog_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_alternative_score_signals['status']}")
                if backlog_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_alternative_score_signals['phase']}")
                if backlog_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_alternative_score_signals['phase_strength']}"
                    )
                if backlog_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_alternative_score_signals['trajectory_signal']}"
                    )
                if backlog_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"alternative {backlog_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            hypothesis_alternative_id = hypothesis_alternative_anchor.get("hypothesis_id")
            hypothesis_alternative_reason = hypothesis_alternative_anchor.get("reason")
            hypothesis_alternative_score_signals = hypothesis_alternative_anchor.get("score_signals") or {}
            hypothesis_alternative_suppressed_by = hypothesis_alternative_anchor.get("suppressed_by")
            hypothesis_alternative_frontier_age = hypothesis_alternative_anchor.get("frontier_age")
            hypothesis_alternative_frontier_trend = hypothesis_alternative_anchor.get("frontier_trend")
            if hypothesis_alternative_id and hypothesis_alternative_suppressed_by:
                hypothesis_alternative_label = (
                    "active hypothesis alternative"
                    if hypothesis_alternative_scope == "active_frontier"
                    else "hypothesis alternative"
                )
                detail = (
                    f"{hypothesis_alternative_label} {hypothesis_alternative_id} is currently suppressed by "
                    f"{hypothesis_alternative_suppressed_by}"
                )
                if hypothesis_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif hypothesis_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if hypothesis_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif hypothesis_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif hypothesis_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if hypothesis_alternative_reason:
                    detail = f"{detail} ({hypothesis_alternative_reason})"
                phase_details.append(detail)
            if hypothesis_alternative_id and hypothesis_alternative_score_signals:
                signal_fragments = []
                if hypothesis_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_alternative_score_signals['status']}")
                if hypothesis_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_alternative_score_signals['phase']}")
                if hypothesis_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_alternative_score_signals['phase_strength']}"
                    )
                if hypothesis_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_alternative_score_signals['trajectory_signal']}"
                    )
                if hypothesis_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"alternative {hypothesis_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_projection_experiment_id:
                phase_details.append(
                    f"hypothesis projection from experiment {hypothesis_projection_experiment_id}"
                )
            if hypothesis_selection_source:
                phase_details.append(f"hypothesis selection source {hypothesis_selection_source}")
            if hypothesis_selection_mode:
                phase_details.append(f"hypothesis selection mode {hypothesis_selection_mode}")
            backlog_recommendation_state_hint = backlog_recommendation_drivers.get("recommendation_state_hint")
            if backlog_recommendation_state_hint:
                phase_details.append(f"backlog recommendation state hint {backlog_recommendation_state_hint}")
            hypothesis_recommendation_state_hint = hypothesis_recommendation_drivers.get("recommendation_state_hint")
            if hypothesis_recommendation_state_hint:
                phase_details.append(
                    f"hypothesis recommendation state hint {hypothesis_recommendation_state_hint}"
                )
            if pending_promotion_candidate_id:
                phase_details.append(f"pending promotion candidate {pending_promotion_candidate_id}")
            if pending_promotion_hypothesis_id:
                phase_details.append(f"pending promotion hypothesis {pending_promotion_hypothesis_id}")
            if pending_promotion_gate_blockers:
                phase_details.append(
                    f"pending promotion gate blockers {', '.join(pending_promotion_gate_blockers)}"
                )
            if promotion_ready_candidate_id:
                phase_details.append(f"promotion-ready candidate {promotion_ready_candidate_id}")
            if promotion_ready_hypothesis_id:
                phase_details.append(f"promotion-ready hypothesis {promotion_ready_hypothesis_id}")
            if (
                anchor_coherence == "divergent"
                and anchor_coherence_expected_hypothesis_ids
                and anchor_coherence_selected_hypothesis_id
            ):
                phase_details.append(
                    "anchor coherence expected "
                    f"{', '.join(anchor_coherence_expected_hypothesis_ids)} but selected "
                    f"{anchor_coherence_selected_hypothesis_id}"
                )
            if phase_details:
                expansion_transition_reason = (
                    " The candidate transition follows phase-aware expansion guidance: "
                    f"{'; '.join(phase_details)}."
                )

            continuation_details = []
            if backlog_phase_signal == "accelerating":
                prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                continuation_details.append(f"build on the {prefix}accelerating backlog trajectory")
            elif backlog_phase_signal == "recovering":
                prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                continuation_details.append(f"continue the {prefix}backlog recovery trajectory")
            elif backlog_phase_signal == "stable":
                prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                continuation_details.append(f"preserve the {prefix}stable backlog trajectory")
            if hypothesis_phase_signal == "accelerating":
                prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                continuation_details.append(f"build on the {prefix}accelerating hypothesis trajectory")
            elif hypothesis_phase_signal == "recovering":
                prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                continuation_details.append(f"continue the {prefix}recovering hypothesis trajectory")
            elif hypothesis_phase_signal == "stable":
                prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                continuation_details.append(f"preserve the {prefix}stable hypothesis trajectory")
            if backlog_trajectory_signal == "newly_recovering":
                continuation_details.append("focus on the newly_recovering backlog trajectory")
            elif backlog_trajectory_signal == "strong_recovery":
                continuation_details.append("build on the strong_recovery backlog trajectory")
            if hypothesis_trajectory_signal == "stale_stable":
                continuation_details.append("avoid relying only on the stale_stable hypothesis trajectory")
            if backlog_recommendation_state_hint:
                continuation_details.append(
                    f"guided by the {backlog_recommendation_state_hint}"
                )
            if hypothesis_recommendation_state_hint:
                continuation_details.append(
                    f"guided by the {hypothesis_recommendation_state_hint}"
                )
            if backlog_selection_source:
                selection_clause = f"selected from {backlog_selection_source}"
                if backlog_selection_mode:
                    selection_clause = f"{selection_clause} via {backlog_selection_mode}"
                continuation_details.append(selection_clause)
            if backlog_selection_score_signals:
                signal_hint = []
                if backlog_selection_score_signals.get("status"):
                    signal_hint.append(backlog_selection_score_signals["status"])
                if backlog_selection_score_signals.get("phase"):
                    signal_hint.append(backlog_selection_score_signals["phase"])
                if backlog_selection_score_signals.get("phase_strength"):
                    signal_hint.append(backlog_selection_score_signals["phase_strength"])
                if backlog_selection_score_signals.get("trajectory_signal"):
                    signal_hint.append(backlog_selection_score_signals["trajectory_signal"])
                if signal_hint:
                    continuation_details.append(
                        f"using a {' / '.join(signal_hint)} selected anchor"
                    )
            if hypothesis_selection_score_signals:
                signal_hint = []
                if hypothesis_selection_score_signals.get("status"):
                    signal_hint.append(hypothesis_selection_score_signals["status"])
                if hypothesis_selection_score_signals.get("phase"):
                    signal_hint.append(hypothesis_selection_score_signals["phase"])
                if hypothesis_selection_score_signals.get("phase_strength"):
                    signal_hint.append(hypothesis_selection_score_signals["phase_strength"])
                if hypothesis_selection_score_signals.get("trajectory_signal"):
                    signal_hint.append(hypothesis_selection_score_signals["trajectory_signal"])
                if signal_hint:
                    continuation_details.append(
                        f"using a {' / '.join(signal_hint)} selected hypothesis anchor"
                    )
            if backlog_alternative_id:
                age_prefix = ""
                if backlog_alternative_frontier_age == "persistent":
                    age_prefix = "persistent "
                elif backlog_alternative_frontier_age == "new":
                    age_prefix = "newly-entered "
                alternative_clause = f"Keep {backlog_alternative_id} in reserve as a {age_prefix}backlog alternative"
                if backlog_alternative_frontier_trend == "rising":
                    alternative_clause = f"{alternative_clause} that is rising in the frontier"
                elif backlog_alternative_frontier_trend == "holding":
                    alternative_clause = f"{alternative_clause} that is holding its frontier position"
                elif backlog_alternative_frontier_trend == "slipping":
                    alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                signal_hint = []
                if backlog_alternative_score_signals.get("phase"):
                    signal_hint.append(backlog_alternative_score_signals["phase"])
                if backlog_alternative_score_signals.get("phase_strength"):
                    signal_hint.append(backlog_alternative_score_signals["phase_strength"])
                if backlog_alternative_score_signals.get("trajectory_signal"):
                    signal_hint.append(backlog_alternative_score_signals["trajectory_signal"])
                if signal_hint:
                    alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                if backlog_alternative_suppressed_by:
                    alternative_clause = f"{alternative_clause} while it remains suppressed by {backlog_alternative_suppressed_by}"
                continuation_details.append(alternative_clause)
            if hypothesis_projection_experiment_id:
                continuation_details.append(
                    f"use hypothesis context projected from experiment {hypothesis_projection_experiment_id}"
                )
            if hypothesis_selection_mode:
                continuation_details.append(
                    f"keep the {hypothesis_selection_mode} hypothesis context active"
                )
            if hypothesis_alternative_id:
                age_prefix = ""
                if hypothesis_alternative_frontier_age == "persistent":
                    age_prefix = "persistent "
                elif hypothesis_alternative_frontier_age == "new":
                    age_prefix = "newly-entered "
                alternative_kind = (
                    "active hypothesis alternative"
                    if hypothesis_alternative_scope == "active_frontier"
                    else "hypothesis alternative"
                )
                alternative_clause = f"Keep {hypothesis_alternative_id} in reserve as a {age_prefix}{alternative_kind}"
                if hypothesis_alternative_frontier_trend == "rising":
                    alternative_clause = f"{alternative_clause} that is rising in the frontier"
                elif hypothesis_alternative_frontier_trend == "holding":
                    alternative_clause = f"{alternative_clause} that is holding its frontier position"
                elif hypothesis_alternative_frontier_trend == "slipping":
                    alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                signal_hint = []
                if hypothesis_alternative_score_signals.get("phase"):
                    signal_hint.append(hypothesis_alternative_score_signals["phase"])
                if hypothesis_alternative_score_signals.get("phase_strength"):
                    signal_hint.append(hypothesis_alternative_score_signals["phase_strength"])
                if hypothesis_alternative_score_signals.get("trajectory_signal"):
                    signal_hint.append(hypothesis_alternative_score_signals["trajectory_signal"])
                if signal_hint:
                    alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                if hypothesis_alternative_suppressed_by:
                    alternative_clause = (
                        f"{alternative_clause} while it remains suppressed by {hypothesis_alternative_suppressed_by}"
                    )
                continuation_details.append(alternative_clause)
            if continuation_details:
                expansion_objective_suffix = (
                    " Continue with phase-aware expansion guidance and "
                    f"{'; '.join(continuation_details)}."
                )
            action_mode_details = []
            if backlog_action_mode:
                action_mode_details.append(f"execute the backlog action mode {backlog_action_mode}")
            if hypothesis_action_mode:
                action_mode_details.append(f"execute the hypothesis action mode {hypothesis_action_mode}")
            if action_mode_details:
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {'; '.join(action_mode_details)}."
                    if expansion_objective_suffix
                    else f" Execute {'; '.join(action_mode_details)}."
                )
            if expansion_confidence_action == "validate_low_confidence_anchor":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Validate the anchor before broader expansion."
                    if expansion_objective_suffix
                    else " Validate the anchor before broader expansion."
                )
                if "validate_before_expansion" not in expansion_focus_areas:
                    expansion_focus_areas.append("validate_before_expansion")
            if expansion_confidence_action == "reconcile_anchor_signals":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Reconcile backlog and hypothesis signals before broader expansion."
                    if expansion_objective_suffix
                    else " Reconcile backlog and hypothesis signals before broader expansion."
                )
                if "reconcile_anchor_signals" not in expansion_focus_areas:
                    expansion_focus_areas.append("reconcile_anchor_signals")
            if expansion_confidence_action == "resolve_persistent_pending_promotion_pair":
                investigation_clause = "Resolve the persistently blocked promotion pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "persistent_pending_promotion_pair_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_pending_promotion_pair_resolution")
            if expansion_confidence_action == "investigate_pending_promotion_pair":
                investigation_clause = "Investigate the blocked promotion pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "pending_promotion_pair_investigation" not in expansion_focus_areas:
                    expansion_focus_areas.append("pending_promotion_pair_investigation")
            if expansion_confidence_action == "investigate_pending_promotions":
                investigation_clause = "Investigate the blocked promotion signals before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "pending_promotion_investigation" not in expansion_focus_areas:
                    expansion_focus_areas.append("pending_promotion_investigation")
            if expansion_confidence_action == "stabilize_persistent_joint_recovery_pair":
                recovery_clause = "Stabilize the persistently aligned recovery pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {recovery_clause}"
                if "persistent_joint_recovery_pair_stabilization" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_joint_recovery_pair_stabilization")
            if expansion_confidence_action == "preserve_joint_recovery_pair":
                recovery_clause = "Preserve the aligned recovery pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {recovery_clause}"
                if "joint_recovery_pair" not in expansion_focus_areas:
                    expansion_focus_areas.append("joint_recovery_pair")
            if expansion_confidence_action == "promote_ready_challengers":
                promotion_clause = "Promote the gate-cleared challenger anchors before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {promotion_clause}"
                    if promotion_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {promotion_clause}"
                if "promotion_ready_execution" not in expansion_focus_areas:
                    expansion_focus_areas.append("promotion_ready_execution")
            if expansion_confidence_action == "advance_persistent_promotion_ready_pair":
                promotion_clause = "Advance the persistently gate-cleared challenger pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {promotion_clause}"
                    if promotion_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {promotion_clause}"
                if "persistent_promotion_ready_pair_advancement" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_promotion_ready_pair_advancement")

            return NextIterationPlan(
                next_objective=(
                    f"{base_objective}"
                    f"{(' ' + expansion_objective_suffix) if expansion_objective_suffix else ''}"
                ),
                strategy="continue",
                reason=(
                    "No prior iteration exists; start from the selected candidate objective."
                    f"{expansion_transition_reason}"
                ),
                focus_areas=expansion_focus_areas,
            )

        return NextIterationPlan(
            next_objective=base_objective,
            strategy="continue",
            reason="No prior iteration exists; start from the base objective.",
            focus_areas=[],
        )

    verification = last_record.get("verification") or {}
    decision = last_record.get("decision")
    recommended_action = verification.get("recommended_brain_action")
    effective_action = recommended_action or decision
    failures = verification.get("failures") or []
    failed_check_types = verification.get("failed_check_types") or []
    rework_priority = verification.get("rework_priority")
    worker_result = last_record.get("worker_result") or {}
    summary = worker_result.get("summary", "").strip()
    transition_reason = ""
    expansion_transition_reason = ""
    expansion_focus_areas: list[str] = []
    expansion_objective_suffix = ""
    expansion_confidence_action = None
    backlog_action = None
    backlog_action_mode = None
    hypothesis_action = None
    hypothesis_action_mode = None
    dominant_failure_mode = None
    backlog_phase_signal = None
    hypothesis_phase_signal = None
    backlog_phase_strength_signal = None
    hypothesis_phase_strength_signal = None
    backlog_trajectory_signal = None
    hypothesis_trajectory_signal = None
    backlog_selection_source = None
    backlog_selection_mode = None
    backlog_selection_score_signals = {}
    used_backlog_frontier_pressure = False
    hypothesis_projection_experiment_id = None
    hypothesis_selection_source = None
    hypothesis_selection_mode = None
    hypothesis_selection_score_signals = {}
    used_hypothesis_frontier_pressure = False
    hypothesis_alternative_scope = None
    pending_promotion_candidate_id = None
    pending_promotion_hypothesis_id = None
    pending_promotion_gate_blockers: list[str] = []
    joint_pending_promotion_pair: dict = {}
    promotion_ready_candidate_id = None
    promotion_ready_hypothesis_id = None
    joint_recovery_pair: dict = {}
    anchor_coherence = None
    anchor_coherence_expected_hypothesis_ids: list[str] = []
    anchor_coherence_selected_hypothesis_id = None
    if candidate_transition and candidate_transition.get("changed"):
        previous_objective = candidate_transition.get("from_objective", "the previous candidate")
        transition_reason = (
            " Shift the remediation anchor to the newly selected candidate instead of repeating "
            f"the previous candidate objective: {previous_objective}."
        )
        transition_mode = candidate_transition.get("mode")
        backlog_action = candidate_transition.get("backlog_action")
        backlog_action_mode = candidate_transition.get("backlog_action_mode")
        hypothesis_action = candidate_transition.get("hypothesis_action")
        hypothesis_action_mode = candidate_transition.get("hypothesis_action_mode")
        dominant_failure_mode = candidate_transition.get("dominant_failure_mode")
        backlog_phase_signal = candidate_transition.get("backlog_phase_signal")
        hypothesis_phase_signal = candidate_transition.get("hypothesis_phase_signal")
        backlog_phase_strength_signal = candidate_transition.get("backlog_phase_strength_signal")
        hypothesis_phase_strength_signal = candidate_transition.get("hypothesis_phase_strength_signal")
        backlog_trajectory_signal = candidate_transition.get("backlog_trajectory_signal")
        hypothesis_trajectory_signal = candidate_transition.get("hypothesis_trajectory_signal")
        expansion_confidence_action = candidate_transition.get("expansion_confidence_action")
        backlog_selection_source = candidate_transition.get("backlog_selection_source")
        backlog_selection_mode = candidate_transition.get("backlog_selection_mode")
        backlog_selection_score_signals = candidate_transition.get("backlog_selection_score_signals") or {}
        used_backlog_frontier_pressure = bool(candidate_transition.get("used_backlog_frontier_pressure"))
        backlog_recommendation_drivers = candidate_transition.get("backlog_recommendation_drivers") or {}
        hypothesis_projection_experiment_id = candidate_transition.get("hypothesis_projection_experiment_id")
        hypothesis_selection_source = candidate_transition.get("hypothesis_selection_source")
        hypothesis_selection_mode = candidate_transition.get("hypothesis_selection_mode")
        hypothesis_selection_score_signals = candidate_transition.get("hypothesis_selection_score_signals") or {}
        used_hypothesis_frontier_pressure = bool(candidate_transition.get("used_hypothesis_frontier_pressure"))
        hypothesis_recommendation_drivers = candidate_transition.get("hypothesis_recommendation_drivers") or {}
        pending_promotion_candidate_id = candidate_transition.get("pending_promotion_candidate_id")
        pending_promotion_hypothesis_id = candidate_transition.get("pending_promotion_hypothesis_id")
        pending_promotion_gate_blockers = list(candidate_transition.get("pending_promotion_gate_blockers") or [])
        joint_pending_promotion_pair = candidate_transition.get("joint_pending_promotion_pair") or {}
        promotion_ready_candidate_id = candidate_transition.get("promotion_ready_candidate_id")
        promotion_ready_hypothesis_id = candidate_transition.get("promotion_ready_hypothesis_id")
        joint_promotion_ready_pair = candidate_transition.get("joint_promotion_ready_pair") or {}
        joint_recovery_pair = candidate_transition.get("joint_recovery_pair") or {}
        anchor_coherence = candidate_transition.get("anchor_coherence")
        anchor_coherence_expected_hypothesis_ids = list(
            candidate_transition.get("anchor_coherence_expected_hypothesis_ids") or []
        )
        anchor_coherence_selected_hypothesis_id = candidate_transition.get(
            "anchor_coherence_selected_hypothesis_id"
        )
        anchor_divergence_memory = candidate_transition.get("anchor_divergence_memory") or {}
        joint_pending_candidate_id = joint_pending_promotion_pair.get("experiment_id") or pending_promotion_candidate_id
        joint_pending_hypothesis_id = (
            joint_pending_promotion_pair.get("hypothesis_id") or pending_promotion_hypothesis_id
        )
        joint_pending_state = joint_pending_promotion_pair.get("pending_state")
        joint_promotion_ready_candidate_id = joint_promotion_ready_pair.get("experiment_id")
        joint_promotion_ready_hypothesis_id = joint_promotion_ready_pair.get("hypothesis_id")
        joint_promotion_ready_state = joint_promotion_ready_pair.get("readiness_state")
        joint_recovery_candidate_id = joint_recovery_pair.get("experiment_id")
        joint_recovery_hypothesis_id = joint_recovery_pair.get("hypothesis_id")
        joint_recovery_failure_mode = joint_recovery_pair.get("failure_mode")
        joint_recovery_state = joint_recovery_pair.get("recovery_state")
        backlog_alternative_anchor = candidate_transition.get("backlog_alternative_anchor") or {}
        hypothesis_alternative_anchor = candidate_transition.get("hypothesis_alternative_anchor") or {}
        hypothesis_alternative_scope = candidate_transition.get("hypothesis_alternative_scope")
        backlog_alternative_id = backlog_alternative_anchor.get("experiment_id")
        backlog_alternative_reason = backlog_alternative_anchor.get("reason")
        backlog_alternative_score_signals = backlog_alternative_anchor.get("score_signals") or {}
        backlog_alternative_suppressed_by = backlog_alternative_anchor.get("suppressed_by")
        backlog_alternative_frontier_age = backlog_alternative_anchor.get("frontier_age")
        backlog_alternative_frontier_trend = backlog_alternative_anchor.get("frontier_trend")
        hypothesis_alternative_id = hypothesis_alternative_anchor.get("hypothesis_id")
        hypothesis_alternative_reason = hypothesis_alternative_anchor.get("reason")
        hypothesis_alternative_score_signals = hypothesis_alternative_anchor.get("score_signals") or {}
        hypothesis_alternative_suppressed_by = hypothesis_alternative_anchor.get("suppressed_by")
        hypothesis_alternative_frontier_age = hypothesis_alternative_anchor.get("frontier_age")
        hypothesis_alternative_frontier_trend = hypothesis_alternative_anchor.get("frontier_trend")
        if transition_mode == "recovery":
            mode_detail = []
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id:
                if "joint_recovery_pair" not in expansion_focus_areas:
                    expansion_focus_areas.append("joint_recovery_pair")
            if expansion_confidence_action:
                mode_detail.append(f"expansion confidence action {expansion_confidence_action}")
                if expansion_confidence_action not in expansion_focus_areas:
                    expansion_focus_areas.append(expansion_confidence_action)
            if backlog_action:
                mode_detail.append(f"backlog recommendation {backlog_action}")
            if backlog_action_mode:
                mode_detail.append(f"backlog action mode {backlog_action_mode}")
            if hypothesis_action:
                mode_detail.append(f"hypothesis recommendation {hypothesis_action}")
            if hypothesis_action_mode:
                mode_detail.append(f"hypothesis action mode {hypothesis_action_mode}")
            if dominant_failure_mode:
                mode_detail.append(f"dominant failure mode {dominant_failure_mode}")
            if hypothesis_projection_experiment_id:
                mode_detail.append(
                    f"hypothesis projection from experiment {hypothesis_projection_experiment_id}"
                )
            if hypothesis_selection_source:
                mode_detail.append(f"hypothesis selection source {hypothesis_selection_source}")
            if hypothesis_selection_mode:
                mode_detail.append(f"hypothesis selection mode {hypothesis_selection_mode}")
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id:
                detail = f"joint recovery pair {joint_recovery_candidate_id}/{joint_recovery_hypothesis_id}"
                if joint_recovery_state:
                    detail = f"{detail} is {joint_recovery_state}"
                if joint_recovery_failure_mode:
                    detail = f"{detail} for {joint_recovery_failure_mode}"
                mode_detail.append(detail)
            if backlog_selection_score_signals:
                signal_fragments = []
                if backlog_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_selection_score_signals['status']}")
                if backlog_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_selection_score_signals['phase']}")
                if backlog_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_selection_score_signals['phase_strength']}"
                    )
                if backlog_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_selection_score_signals['trajectory_signal']}"
                    )
                if backlog_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    mode_detail.append(
                        f"selected anchor score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_selection_score_signals:
                signal_fragments = []
                if hypothesis_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_selection_score_signals['status']}")
                if hypothesis_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_selection_score_signals['phase']}")
                if hypothesis_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_selection_score_signals['phase_strength']}"
                    )
                if hypothesis_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_selection_score_signals['trajectory_signal']}"
                    )
                if hypothesis_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    mode_detail.append(
                        f"selected hypothesis anchor score signals {', '.join(signal_fragments)}"
                    )
            if used_backlog_frontier_pressure:
                mode_detail.append("backlog frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_backlog" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_backlog")
            if used_hypothesis_frontier_pressure:
                mode_detail.append("hypothesis frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_hypothesis" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_hypothesis")
            if backlog_alternative_id and backlog_alternative_suppressed_by:
                detail = (
                    f"backlog alternative {backlog_alternative_id} is currently suppressed by "
                    f"{backlog_alternative_suppressed_by}"
                )
                if backlog_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif backlog_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if backlog_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif backlog_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif backlog_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if backlog_alternative_reason:
                    detail = f"{detail} ({backlog_alternative_reason})"
                mode_detail.append(detail)
            if backlog_alternative_id and backlog_alternative_score_signals:
                signal_fragments = []
                if backlog_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_alternative_score_signals['status']}")
                if backlog_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_alternative_score_signals['phase']}")
                if backlog_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_alternative_score_signals['phase_strength']}"
                    )
                if backlog_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_alternative_score_signals['trajectory_signal']}"
                    )
                if backlog_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    mode_detail.append(
                        f"alternative {backlog_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_alternative_id and hypothesis_alternative_suppressed_by:
                hypothesis_alternative_label = (
                    "active hypothesis alternative"
                    if hypothesis_alternative_scope == "active_frontier"
                    else "hypothesis alternative"
                )
                detail = (
                    f"{hypothesis_alternative_label} {hypothesis_alternative_id} is currently suppressed by "
                    f"{hypothesis_alternative_suppressed_by}"
                )
                if hypothesis_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif hypothesis_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if hypothesis_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif hypothesis_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif hypothesis_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if hypothesis_alternative_reason:
                    detail = f"{detail} ({hypothesis_alternative_reason})"
                mode_detail.append(detail)
            if hypothesis_alternative_id and hypothesis_alternative_score_signals:
                signal_fragments = []
                if hypothesis_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_alternative_score_signals['status']}")
                if hypothesis_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_alternative_score_signals['phase']}")
                if hypothesis_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_alternative_score_signals['phase_strength']}"
                    )
                if hypothesis_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_alternative_score_signals['trajectory_signal']}"
                    )
                if hypothesis_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    mode_detail.append(
                        f"alternative {hypothesis_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            if (
                anchor_coherence == "divergent"
                and anchor_coherence_expected_hypothesis_ids
                and anchor_coherence_selected_hypothesis_id
            ):
                mode_detail.append(
                    "anchor coherence expected "
                    f"{', '.join(anchor_coherence_expected_hypothesis_ids)} but selected "
                    f"{anchor_coherence_selected_hypothesis_id}"
                )
            if mode_detail:
                expansion_transition_reason = (
                    " The candidate transition follows expansion-state recovery guidance: "
                    f"{'; '.join(mode_detail)}."
                )
            if effective_action == "REFINE" and failed_check_types:
                fallback_clause = (
                    " The candidate transition uses fallback recovery guidance derived from the known failed check "
                    f"types: {'; '.join(failed_check_types)}."
                )
                if "fallback recovery guidance derived from the known failed check types" not in expansion_transition_reason:
                    expansion_transition_reason = f"{expansion_transition_reason}{fallback_clause}"
            objective_details = []
            if dominant_failure_mode:
                objective_details.append(f"prioritize {dominant_failure_mode} recovery")
            if backlog_action:
                objective_details.append(backlog_action)
            if backlog_action_mode:
                objective_details.append(f"execute {backlog_action_mode}")
            if hypothesis_action:
                objective_details.append(hypothesis_action)
            if hypothesis_action_mode:
                objective_details.append(f"execute {hypothesis_action_mode}")
            if hypothesis_projection_experiment_id:
                objective_details.append(
                    f"use hypothesis context projected from experiment {hypothesis_projection_experiment_id}"
                )
            if hypothesis_selection_mode:
                objective_details.append(
                    f"keep the {hypothesis_selection_mode} hypothesis context active"
                )
            if backlog_selection_score_signals:
                signal_hint = []
                if backlog_selection_score_signals.get("status"):
                    signal_hint.append(backlog_selection_score_signals["status"])
                if backlog_selection_score_signals.get("phase"):
                    signal_hint.append(backlog_selection_score_signals["phase"])
                if backlog_selection_score_signals.get("phase_strength"):
                    signal_hint.append(backlog_selection_score_signals["phase_strength"])
                if backlog_selection_score_signals.get("trajectory_signal"):
                    signal_hint.append(backlog_selection_score_signals["trajectory_signal"])
                if signal_hint:
                    objective_details.append(
                        f"using a {' / '.join(signal_hint)} selected anchor"
                    )
            if hypothesis_selection_score_signals:
                signal_hint = []
                if hypothesis_selection_score_signals.get("status"):
                    signal_hint.append(hypothesis_selection_score_signals["status"])
                if hypothesis_selection_score_signals.get("phase"):
                    signal_hint.append(hypothesis_selection_score_signals["phase"])
                if hypothesis_selection_score_signals.get("phase_strength"):
                    signal_hint.append(hypothesis_selection_score_signals["phase_strength"])
                if hypothesis_selection_score_signals.get("trajectory_signal"):
                    signal_hint.append(hypothesis_selection_score_signals["trajectory_signal"])
                if signal_hint:
                    objective_details.append(
                        f"using a {' / '.join(signal_hint)} selected hypothesis anchor"
                    )
            if backlog_alternative_id:
                age_prefix = ""
                if backlog_alternative_frontier_age == "persistent":
                    age_prefix = "persistent "
                elif backlog_alternative_frontier_age == "new":
                    age_prefix = "newly-entered "
                alternative_clause = (
                    f"keep {backlog_alternative_id} in reserve as a {age_prefix}backlog alternative"
                )
                if backlog_alternative_frontier_trend == "rising":
                    alternative_clause = f"{alternative_clause} that is rising in the frontier"
                elif backlog_alternative_frontier_trend == "holding":
                    alternative_clause = f"{alternative_clause} that is holding its frontier position"
                elif backlog_alternative_frontier_trend == "slipping":
                    alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                signal_hint = []
                if backlog_alternative_score_signals.get("phase"):
                    signal_hint.append(backlog_alternative_score_signals["phase"])
                if backlog_alternative_score_signals.get("phase_strength"):
                    signal_hint.append(backlog_alternative_score_signals["phase_strength"])
                if backlog_alternative_score_signals.get("trajectory_signal"):
                    signal_hint.append(backlog_alternative_score_signals["trajectory_signal"])
                if signal_hint:
                    alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                if backlog_alternative_suppressed_by:
                    alternative_clause = (
                        f"{alternative_clause} while it remains suppressed by {backlog_alternative_suppressed_by}"
                    )
                objective_details.append(alternative_clause)
            if hypothesis_alternative_id:
                age_prefix = ""
                if hypothesis_alternative_frontier_age == "persistent":
                    age_prefix = "persistent "
                elif hypothesis_alternative_frontier_age == "new":
                    age_prefix = "newly-entered "
                alternative_kind = (
                    "active hypothesis alternative"
                    if hypothesis_alternative_scope == "active_frontier"
                    else "hypothesis alternative"
                )
                alternative_clause = (
                    f"keep {hypothesis_alternative_id} in reserve as a {age_prefix}{alternative_kind}"
                )
                if hypothesis_alternative_frontier_trend == "rising":
                    alternative_clause = f"{alternative_clause} that is rising in the frontier"
                elif hypothesis_alternative_frontier_trend == "holding":
                    alternative_clause = f"{alternative_clause} that is holding its frontier position"
                elif hypothesis_alternative_frontier_trend == "slipping":
                    alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                signal_hint = []
                if hypothesis_alternative_score_signals.get("phase"):
                    signal_hint.append(hypothesis_alternative_score_signals["phase"])
                if hypothesis_alternative_score_signals.get("phase_strength"):
                    signal_hint.append(hypothesis_alternative_score_signals["phase_strength"])
                if hypothesis_alternative_score_signals.get("trajectory_signal"):
                    signal_hint.append(hypothesis_alternative_score_signals["trajectory_signal"])
                if signal_hint:
                    alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                if hypothesis_alternative_suppressed_by:
                    alternative_clause = (
                        f"{alternative_clause} while it remains suppressed by {hypothesis_alternative_suppressed_by}"
                    )
                objective_details.append(alternative_clause)
            if objective_details:
                expansion_objective_suffix = (
                    " Use the new candidate as the recovery anchor and "
                    f"{'; '.join(objective_details)}."
                )
            if dominant_failure_mode and dominant_failure_mode not in expansion_focus_areas:
                expansion_focus_areas.append(dominant_failure_mode)
            if backlog_action and backlog_action not in expansion_focus_areas:
                expansion_focus_areas.append(backlog_action)
            if backlog_action_mode and backlog_action_mode not in expansion_focus_areas:
                expansion_focus_areas.append(backlog_action_mode)
            if hypothesis_action and hypothesis_action not in expansion_focus_areas:
                expansion_focus_areas.append(hypothesis_action)
            if hypothesis_action_mode and hypothesis_action_mode not in expansion_focus_areas:
                expansion_focus_areas.append(hypothesis_action_mode)
        elif transition_mode == "continuation":
            phase_details = []
            if backlog_phase_signal:
                phase_details.append(f"backlog phase {backlog_phase_signal}")
                if backlog_phase_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_phase_signal)
            if backlog_phase_strength_signal:
                phase_details.append(f"backlog phase strength {backlog_phase_strength_signal}")
                if backlog_phase_strength_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_phase_strength_signal)
            if backlog_trajectory_signal:
                phase_details.append(f"backlog trajectory {backlog_trajectory_signal}")
                if backlog_trajectory_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_trajectory_signal)
            if hypothesis_phase_signal:
                phase_details.append(f"hypothesis phase {hypothesis_phase_signal}")
                if hypothesis_phase_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_phase_signal)
            if hypothesis_phase_strength_signal:
                phase_details.append(f"hypothesis phase strength {hypothesis_phase_strength_signal}")
                if hypothesis_phase_strength_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_phase_strength_signal)
            if hypothesis_trajectory_signal:
                phase_details.append(f"hypothesis trajectory {hypothesis_trajectory_signal}")
                if hypothesis_trajectory_signal not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_trajectory_signal)
            if backlog_action:
                phase_details.append(f"backlog recommendation {backlog_action}")
                if backlog_action not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_action)
            if backlog_action_mode:
                phase_details.append(f"backlog action mode {backlog_action_mode}")
                if backlog_action_mode not in expansion_focus_areas:
                    expansion_focus_areas.append(backlog_action_mode)
            if hypothesis_action:
                phase_details.append(f"hypothesis recommendation {hypothesis_action}")
                if hypothesis_action not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_action)
            if hypothesis_action_mode:
                phase_details.append(f"hypothesis action mode {hypothesis_action_mode}")
                if hypothesis_action_mode not in expansion_focus_areas:
                    expansion_focus_areas.append(hypothesis_action_mode)
            if expansion_confidence_action:
                phase_details.append(f"expansion confidence action {expansion_confidence_action}")
                if expansion_confidence_action not in expansion_focus_areas:
                    expansion_focus_areas.append(expansion_confidence_action)
            if (
                anchor_coherence == "divergent"
                and anchor_coherence_expected_hypothesis_ids
                and anchor_coherence_selected_hypothesis_id
            ):
                phase_details.append(
                    "anchor coherence expected "
                    f"{', '.join(anchor_coherence_expected_hypothesis_ids)} but selected "
                    f"{anchor_coherence_selected_hypothesis_id}"
                )
            if backlog_selection_source:
                phase_details.append(f"selection source {backlog_selection_source}")
            if backlog_selection_mode:
                phase_details.append(f"selection mode {backlog_selection_mode}")
            if backlog_selection_score_signals:
                signal_fragments = []
                if backlog_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_selection_score_signals['status']}")
                if backlog_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_selection_score_signals['phase']}")
                if backlog_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_selection_score_signals['phase_strength']}"
                    )
                if backlog_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_selection_score_signals['trajectory_signal']}"
                    )
                if backlog_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"selected anchor score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_selection_score_signals:
                signal_fragments = []
                if hypothesis_selection_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_selection_score_signals['status']}")
                if hypothesis_selection_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_selection_score_signals['phase']}")
                if hypothesis_selection_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_selection_score_signals['phase_strength']}"
                    )
                if hypothesis_selection_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_selection_score_signals['trajectory_signal']}"
                    )
                if hypothesis_selection_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_selection_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"selected hypothesis anchor score signals {', '.join(signal_fragments)}"
                    )
            if used_backlog_frontier_pressure:
                phase_details.append("backlog frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_backlog" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_backlog")
            if used_hypothesis_frontier_pressure:
                phase_details.append("hypothesis frontier pressure influenced the selected candidate transition")
                if "frontier_pressure_hypothesis" not in expansion_focus_areas:
                    expansion_focus_areas.append("frontier_pressure_hypothesis")
            backlog_alternative_reason = backlog_alternative_anchor.get("reason")
            if backlog_alternative_id and backlog_alternative_suppressed_by:
                detail = (
                    f"backlog alternative {backlog_alternative_id} is currently suppressed by "
                    f"{backlog_alternative_suppressed_by}"
                )
                if backlog_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif backlog_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if backlog_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif backlog_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif backlog_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if backlog_alternative_reason:
                    detail = f"{detail} ({backlog_alternative_reason})"
                phase_details.append(detail)
            if backlog_alternative_id and backlog_alternative_score_signals:
                signal_fragments = []
                if backlog_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {backlog_alternative_score_signals['status']}")
                if backlog_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {backlog_alternative_score_signals['phase']}")
                if backlog_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {backlog_alternative_score_signals['phase_strength']}"
                    )
                if backlog_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {backlog_alternative_score_signals['trajectory_signal']}"
                    )
                if backlog_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {backlog_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"alternative {backlog_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            hypothesis_alternative_reason = hypothesis_alternative_anchor.get("reason")
            if hypothesis_alternative_id and hypothesis_alternative_suppressed_by:
                hypothesis_alternative_label = (
                    "active hypothesis alternative"
                    if hypothesis_alternative_scope == "active_frontier"
                    else "hypothesis alternative"
                )
                detail = (
                    f"{hypothesis_alternative_label} {hypothesis_alternative_id} is currently suppressed by "
                    f"{hypothesis_alternative_suppressed_by}"
                )
                if hypothesis_alternative_frontier_age == "persistent":
                    detail = f"{detail} and remains persistent in the frontier"
                elif hypothesis_alternative_frontier_age == "new":
                    detail = f"{detail} and is newly entering the frontier"
                if hypothesis_alternative_frontier_trend == "rising":
                    detail = f"{detail} while rising in the frontier"
                elif hypothesis_alternative_frontier_trend == "holding":
                    detail = f"{detail} while holding its frontier position"
                elif hypothesis_alternative_frontier_trend == "slipping":
                    detail = f"{detail} while slipping in the frontier"
                if hypothesis_alternative_reason:
                    detail = f"{detail} ({hypothesis_alternative_reason})"
                phase_details.append(detail)
            if hypothesis_alternative_id and hypothesis_alternative_score_signals:
                signal_fragments = []
                if hypothesis_alternative_score_signals.get("status"):
                    signal_fragments.append(f"status {hypothesis_alternative_score_signals['status']}")
                if hypothesis_alternative_score_signals.get("phase"):
                    signal_fragments.append(f"phase {hypothesis_alternative_score_signals['phase']}")
                if hypothesis_alternative_score_signals.get("phase_strength"):
                    signal_fragments.append(
                        f"phase strength {hypothesis_alternative_score_signals['phase_strength']}"
                    )
                if hypothesis_alternative_score_signals.get("trajectory_signal"):
                    signal_fragments.append(
                        f"trajectory {hypothesis_alternative_score_signals['trajectory_signal']}"
                    )
                if hypothesis_alternative_score_signals.get("action_mode"):
                    signal_fragments.append(
                        f"action mode {hypothesis_alternative_score_signals['action_mode']}"
                    )
                if signal_fragments:
                    phase_details.append(
                        f"alternative {hypothesis_alternative_id} score signals {', '.join(signal_fragments)}"
                    )
            if hypothesis_projection_experiment_id:
                phase_details.append(
                    f"hypothesis projection from experiment {hypothesis_projection_experiment_id}"
                )
            if hypothesis_selection_source:
                phase_details.append(f"hypothesis selection source {hypothesis_selection_source}")
            if hypothesis_selection_mode:
                phase_details.append(f"hypothesis selection mode {hypothesis_selection_mode}")
            backlog_recommendation_state_hint = backlog_recommendation_drivers.get("recommendation_state_hint")
            if backlog_recommendation_state_hint:
                phase_details.append(f"backlog recommendation state hint {backlog_recommendation_state_hint}")
            hypothesis_recommendation_state_hint = hypothesis_recommendation_drivers.get("recommendation_state_hint")
            if hypothesis_recommendation_state_hint:
                phase_details.append(
                    f"hypothesis recommendation state hint {hypothesis_recommendation_state_hint}"
                )
            if pending_promotion_candidate_id:
                phase_details.append(f"pending promotion candidate {pending_promotion_candidate_id}")
            if pending_promotion_hypothesis_id:
                phase_details.append(f"pending promotion hypothesis {pending_promotion_hypothesis_id}")
            if joint_pending_candidate_id and joint_pending_hypothesis_id:
                detail = f"joint pending promotion pair {joint_pending_candidate_id}/{joint_pending_hypothesis_id}"
                if joint_pending_state:
                    detail = f"{detail} is {joint_pending_state}"
                phase_details.append(detail)
            if pending_promotion_gate_blockers:
                phase_details.append(
                    f"pending promotion gate blockers {', '.join(pending_promotion_gate_blockers)}"
                )
            if promotion_ready_candidate_id:
                phase_details.append(f"promotion-ready candidate {promotion_ready_candidate_id}")
            if promotion_ready_hypothesis_id:
                phase_details.append(f"promotion-ready hypothesis {promotion_ready_hypothesis_id}")
            if joint_promotion_ready_candidate_id and joint_promotion_ready_hypothesis_id:
                detail = (
                    "joint promotion-ready pair "
                    f"{joint_promotion_ready_candidate_id}/{joint_promotion_ready_hypothesis_id}"
                )
                if joint_promotion_ready_state:
                    detail = f"{detail} is {joint_promotion_ready_state}"
                phase_details.append(detail)
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id:
                detail = f"joint recovery pair {joint_recovery_candidate_id}/{joint_recovery_hypothesis_id}"
                if joint_recovery_state:
                    detail = f"{detail} is {joint_recovery_state}"
                if joint_recovery_failure_mode:
                    detail = f"{detail} for {joint_recovery_failure_mode}"
                phase_details.append(detail)
            if phase_details:
                expansion_transition_reason = (
                    " The candidate transition follows phase-aware expansion guidance: "
                    f"{'; '.join(phase_details)}."
                )
                trajectory_reason_fragments = []
                if backlog_trajectory_signal:
                    trajectory_reason_fragments.append(f"backlog trajectory {backlog_trajectory_signal}")
                if hypothesis_trajectory_signal:
                    trajectory_reason_fragments.append(f"hypothesis trajectory {hypothesis_trajectory_signal}")
                if trajectory_reason_fragments:
                    expansion_transition_reason = (
                        f"{expansion_transition_reason} Trajectory-aware continuation signals: "
                        f"{'; '.join(trajectory_reason_fragments)}."
                    )
            if effective_action == "CONTINUE":
                continuation_details = []
                if backlog_phase_signal == "accelerating":
                    prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                    continuation_details.append(f"build on the {prefix}accelerating backlog trajectory")
                elif backlog_phase_signal == "recovering":
                    prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                    continuation_details.append(f"continue the {prefix}backlog recovery trajectory")
                elif backlog_phase_signal == "stable":
                    prefix = f"{backlog_phase_strength_signal}-confidence " if backlog_phase_strength_signal else ""
                    continuation_details.append(f"preserve the {prefix}stable backlog trajectory")
                if hypothesis_phase_signal == "accelerating":
                    prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                    continuation_details.append(f"build on the {prefix}accelerating hypothesis trajectory")
                elif hypothesis_phase_signal == "recovering":
                    prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                    continuation_details.append(f"continue the {prefix}recovering hypothesis trajectory")
                elif hypothesis_phase_signal == "stable":
                    prefix = f"{hypothesis_phase_strength_signal}-confidence " if hypothesis_phase_strength_signal else ""
                    continuation_details.append(f"preserve the {prefix}stable hypothesis trajectory")
                if backlog_trajectory_signal == "newly_recovering":
                    continuation_details.append("focus on the newly_recovering backlog trajectory")
                elif backlog_trajectory_signal == "strong_recovery":
                    continuation_details.append("build on the strong_recovery backlog trajectory")
                if hypothesis_trajectory_signal == "stale_stable":
                    continuation_details.append("avoid relying only on the stale_stable hypothesis trajectory")
                if backlog_recommendation_state_hint:
                    continuation_details.append(
                        f"guided by the {backlog_recommendation_state_hint}"
                    )
                if hypothesis_recommendation_state_hint:
                    continuation_details.append(
                        f"guided by the {hypothesis_recommendation_state_hint}"
                    )
                if backlog_selection_source:
                    selection_clause = f"selected from {backlog_selection_source}"
                    if backlog_selection_mode:
                        selection_clause = f"{selection_clause} via {backlog_selection_mode}"
                    continuation_details.append(selection_clause)
                if backlog_selection_score_signals:
                    signal_hint = []
                    if backlog_selection_score_signals.get("status"):
                        signal_hint.append(backlog_selection_score_signals["status"])
                    if backlog_selection_score_signals.get("phase"):
                        signal_hint.append(backlog_selection_score_signals["phase"])
                    if backlog_selection_score_signals.get("phase_strength"):
                        signal_hint.append(backlog_selection_score_signals["phase_strength"])
                    if backlog_selection_score_signals.get("trajectory_signal"):
                        signal_hint.append(backlog_selection_score_signals["trajectory_signal"])
                    if signal_hint:
                        continuation_details.append(
                            f"using a {' / '.join(signal_hint)} selected anchor"
                        )
                if hypothesis_selection_score_signals:
                    signal_hint = []
                    if hypothesis_selection_score_signals.get("status"):
                        signal_hint.append(hypothesis_selection_score_signals["status"])
                    if hypothesis_selection_score_signals.get("phase"):
                        signal_hint.append(hypothesis_selection_score_signals["phase"])
                    if hypothesis_selection_score_signals.get("phase_strength"):
                        signal_hint.append(hypothesis_selection_score_signals["phase_strength"])
                    if hypothesis_selection_score_signals.get("trajectory_signal"):
                        signal_hint.append(hypothesis_selection_score_signals["trajectory_signal"])
                    if signal_hint:
                        continuation_details.append(
                            f"using a {' / '.join(signal_hint)} selected hypothesis anchor"
                        )
                if used_backlog_frontier_pressure:
                    continuation_details.append("Preserve the pressure-driven backlog reprioritization signal")
                if used_hypothesis_frontier_pressure:
                    continuation_details.append("Preserve the pressure-driven hypothesis reprioritization signal")
                if backlog_alternative_id:
                    age_prefix = ""
                    if backlog_alternative_frontier_age == "persistent":
                        age_prefix = "persistent "
                    elif backlog_alternative_frontier_age == "new":
                        age_prefix = "newly-entered "
                    alternative_clause = f"Keep {backlog_alternative_id} in reserve as a {age_prefix}backlog alternative"
                    if backlog_alternative_frontier_trend == "rising":
                        alternative_clause = f"{alternative_clause} that is rising in the frontier"
                    elif backlog_alternative_frontier_trend == "holding":
                        alternative_clause = f"{alternative_clause} that is holding its frontier position"
                    elif backlog_alternative_frontier_trend == "slipping":
                        alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                    signal_hint = []
                    if backlog_alternative_score_signals.get("phase"):
                        signal_hint.append(backlog_alternative_score_signals["phase"])
                    if backlog_alternative_score_signals.get("phase_strength"):
                        signal_hint.append(backlog_alternative_score_signals["phase_strength"])
                    if backlog_alternative_score_signals.get("trajectory_signal"):
                        signal_hint.append(backlog_alternative_score_signals["trajectory_signal"])
                    if signal_hint:
                        alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                    if backlog_alternative_suppressed_by:
                        alternative_clause = (
                            f"{alternative_clause} while it remains suppressed by {backlog_alternative_suppressed_by}"
                        )
                    continuation_details.append(alternative_clause)
                if hypothesis_projection_experiment_id:
                    continuation_details.append(
                        f"use hypothesis context projected from experiment {hypothesis_projection_experiment_id}"
                    )
                if hypothesis_selection_mode:
                    continuation_details.append(
                        f"keep the {hypothesis_selection_mode} hypothesis context active"
                    )
                if hypothesis_alternative_id:
                    age_prefix = ""
                    if hypothesis_alternative_frontier_age == "persistent":
                        age_prefix = "persistent "
                    elif hypothesis_alternative_frontier_age == "new":
                        age_prefix = "newly-entered "
                    alternative_kind = (
                        "active hypothesis alternative"
                        if hypothesis_alternative_scope == "active_frontier"
                        else "hypothesis alternative"
                    )
                    alternative_clause = f"Keep {hypothesis_alternative_id} in reserve as a {age_prefix}{alternative_kind}"
                    if hypothesis_alternative_frontier_trend == "rising":
                        alternative_clause = f"{alternative_clause} that is rising in the frontier"
                    elif hypothesis_alternative_frontier_trend == "holding":
                        alternative_clause = f"{alternative_clause} that is holding its frontier position"
                    elif hypothesis_alternative_frontier_trend == "slipping":
                        alternative_clause = f"{alternative_clause} that is slipping in the frontier"
                    signal_hint = []
                    if hypothesis_alternative_score_signals.get("phase"):
                        signal_hint.append(hypothesis_alternative_score_signals["phase"])
                    if hypothesis_alternative_score_signals.get("phase_strength"):
                        signal_hint.append(hypothesis_alternative_score_signals["phase_strength"])
                    if hypothesis_alternative_score_signals.get("trajectory_signal"):
                        signal_hint.append(hypothesis_alternative_score_signals["trajectory_signal"])
                    if signal_hint:
                        alternative_clause = f"{alternative_clause} with {' / '.join(signal_hint)} signals"
                    if hypothesis_alternative_suppressed_by:
                        alternative_clause = (
                            f"{alternative_clause} while it remains suppressed by {hypothesis_alternative_suppressed_by}"
                        )
                    continuation_details.append(alternative_clause)
                if continuation_details:
                    expansion_objective_suffix = (
                        " Continue with phase-aware expansion guidance and "
                        f"{'; '.join(continuation_details)}."
                    )
                action_mode_details = []
                if backlog_action_mode:
                    action_mode_details.append(f"execute the backlog action mode {backlog_action_mode}")
                if hypothesis_action_mode:
                    action_mode_details.append(f"execute the hypothesis action mode {hypothesis_action_mode}")
                if action_mode_details:
                    expansion_objective_suffix = (
                        f"{expansion_objective_suffix} {'; '.join(action_mode_details)}."
                        if expansion_objective_suffix
                        else f" Execute {'; '.join(action_mode_details)}."
                    )
            if expansion_confidence_action == "validate_low_confidence_anchor" and effective_action == "CONTINUE":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Validate the anchor before broader expansion."
                    if expansion_objective_suffix
                    else " Validate the anchor before broader expansion."
                )
                if "validate_before_expansion" not in expansion_focus_areas:
                    expansion_focus_areas.append("validate_before_expansion")
            if expansion_confidence_action == "reconcile_anchor_signals" and effective_action == "CONTINUE":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Reconcile backlog and hypothesis signals before broader expansion."
                    if expansion_objective_suffix
                    else " Reconcile backlog and hypothesis signals before broader expansion."
                )
                if "reconcile_anchor_signals" not in expansion_focus_areas:
                    expansion_focus_areas.append("reconcile_anchor_signals")
            if expansion_confidence_action == "resolve_persistent_action_mode_divergence" and effective_action == "CONTINUE":
                divergence_clause = "Resolve the persistent action-mode divergence before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {divergence_clause}"
                    if divergence_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {divergence_clause}"
                if "reconcile_anchor_signals" not in expansion_focus_areas:
                    expansion_focus_areas.append("reconcile_anchor_signals")
                if "persistent_action_mode_divergence_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_action_mode_divergence_resolution")
            if expansion_confidence_action == "resolve_persistent_coordination_divergence" and effective_action == "CONTINUE":
                divergence_clause = "Resolve the persistent coordination divergence before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {divergence_clause}"
                    if divergence_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {divergence_clause}"
                if "reconcile_anchor_signals" not in expansion_focus_areas:
                    expansion_focus_areas.append("reconcile_anchor_signals")
                if "persistent_coordination_divergence_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_coordination_divergence_resolution")
            if expansion_confidence_action == "resolve_persistent_joint_reserve_memory" and effective_action == "CONTINUE":
                reserve_clause = "Resolve the persistent joint reserve memory before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {reserve_clause}"
                    if reserve_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {reserve_clause}"
                if "persistent_joint_reserve_memory_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_joint_reserve_memory_resolution")
            if expansion_confidence_action == "resolve_persistent_anchor_divergence" and effective_action == "CONTINUE":
                divergence_clause = "Resolve the persistent anchor divergence before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {divergence_clause}"
                    if divergence_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {divergence_clause}"
                if "reconcile_anchor_signals" not in expansion_focus_areas:
                    expansion_focus_areas.append("reconcile_anchor_signals")
                if "persistent_anchor_divergence_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_anchor_divergence_resolution")
            if expansion_confidence_action == "resolve_persistent_pending_promotion_pair" and effective_action == "CONTINUE":
                investigation_clause = (
                    "Resolve the persistently blocked promotion pair before broader expansion."
                )
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "persistent_pending_promotion_pair_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_pending_promotion_pair_resolution")
            if expansion_confidence_action == "investigate_pending_promotion_pair" and effective_action == "CONTINUE":
                investigation_clause = "Investigate the blocked promotion pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "pending_promotion_pair_investigation" not in expansion_focus_areas:
                    expansion_focus_areas.append("pending_promotion_pair_investigation")
            if expansion_confidence_action == "investigate_pending_promotions" and effective_action == "CONTINUE":
                investigation_clause = "Investigate the blocked promotion signals before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {investigation_clause}"
                    if investigation_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {investigation_clause}"
                if "pending_promotion_investigation" not in expansion_focus_areas:
                    expansion_focus_areas.append("pending_promotion_investigation")
            if expansion_confidence_action == "stabilize_persistent_joint_recovery_pair" and effective_action == "CONTINUE":
                recovery_clause = "Stabilize the persistently aligned recovery pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {recovery_clause}"
                if "persistent_joint_recovery_pair_stabilization" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_joint_recovery_pair_stabilization")
            if expansion_confidence_action == "preserve_joint_recovery_pair" and effective_action == "CONTINUE":
                recovery_clause = "Preserve the aligned recovery pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {recovery_clause}"
                if "joint_recovery_pair" not in expansion_focus_areas:
                    expansion_focus_areas.append("joint_recovery_pair")
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id and effective_action == "CONTINUE":
                recovery_clause = "Preserve the aligned recovery pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {recovery_clause}"
                if "joint_recovery_pair" not in expansion_focus_areas:
                    expansion_focus_areas.append("joint_recovery_pair")
            if expansion_confidence_action == "promote_ready_challengers" and effective_action == "CONTINUE":
                promotion_clause = "Promote the gate-cleared challenger anchors before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {promotion_clause}"
                    if promotion_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {promotion_clause}"
                if "promotion_ready_execution" not in expansion_focus_areas:
                    expansion_focus_areas.append("promotion_ready_execution")
            if expansion_confidence_action == "advance_persistent_promotion_ready_pair" and effective_action == "CONTINUE":
                promotion_clause = "Advance the persistently gate-cleared challenger pair before broader expansion."
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {promotion_clause}"
                    if promotion_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                ) if expansion_objective_suffix else f" {promotion_clause}"
                if "persistent_promotion_ready_pair_advancement" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_promotion_ready_pair_advancement")
        elif effective_action == "REFINE":
            fallback_details = []
            if failed_check_types:
                for check_type in failed_check_types:
                    if check_type in STRUCTURED_REFINEMENT_GUIDANCE:
                        fallback_details.append(f"prioritize {check_type} recovery")
            if fallback_details:
                expansion_objective_suffix = (
                    "Use the new candidate as the recovery anchor and "
                    f"{'; '.join(fallback_details)}."
                )
                expansion_transition_reason = (
                    " The candidate transition uses fallback recovery guidance derived from the known failed check types: "
                    f"{'; '.join(failed_check_types)}."
                )
            else:
                expansion_objective_suffix = "Use the new candidate as the recovery anchor."
            if joint_recovery_candidate_id and joint_recovery_hypothesis_id:
                recovery_detail = (
                    f" The candidate transition preserves joint recovery pair "
                    f"{joint_recovery_candidate_id}/{joint_recovery_hypothesis_id}"
                )
                if joint_recovery_state:
                    recovery_detail = f"{recovery_detail} is {joint_recovery_state}"
                if joint_recovery_failure_mode:
                    recovery_detail = f"{recovery_detail} for {joint_recovery_failure_mode}"
                recovery_detail = f"{recovery_detail}."
                if recovery_detail not in expansion_transition_reason:
                    expansion_transition_reason = f"{expansion_transition_reason}{recovery_detail}"
                recovery_clause = (
                    "Stabilize the persistently aligned recovery pair before broader expansion."
                    if expansion_confidence_action == "stabilize_persistent_joint_recovery_pair"
                    or joint_recovery_state == "persistent"
                    else "Preserve the aligned recovery pair before broader expansion."
                )
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} {recovery_clause}"
                    if recovery_clause not in expansion_objective_suffix
                    else expansion_objective_suffix
                )
                focus_area = (
                    "persistent_joint_recovery_pair_stabilization"
                    if expansion_confidence_action == "stabilize_persistent_joint_recovery_pair"
                    or joint_recovery_state == "persistent"
                    else "joint_recovery_pair"
                )
                if focus_area not in expansion_focus_areas:
                    expansion_focus_areas.append(focus_area)

        if effective_action == "REFINE" and not expansion_objective_suffix:
            fallback_details = []
            if failed_check_types:
                for check_type in failed_check_types:
                    if check_type in STRUCTURED_REFINEMENT_GUIDANCE:
                        fallback_details.append(f"prioritize {check_type} recovery")
            if fallback_details:
                expansion_objective_suffix = (
                    "Use the new candidate as the recovery anchor and "
                    f"{'; '.join(fallback_details)}."
                )
                if "fallback recovery guidance derived from the known failed check types" not in expansion_transition_reason:
                    expansion_transition_reason = (
                        f"{expansion_transition_reason}"
                        " The candidate transition uses fallback recovery guidance derived from the known failed check types: "
                        f"{'; '.join(failed_check_types)}."
                    )
            else:
                expansion_objective_suffix = "Use the new candidate as the recovery anchor."
            if (
                expansion_confidence_action == "stabilize_persistent_joint_recovery_pair"
                and "expansion confidence action stabilize_persistent_joint_recovery_pair" not in expansion_transition_reason
            ):
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition preserves the expansion confidence action "
                    "stabilize_persistent_joint_recovery_pair."
                )

    if effective_action == "REFINE":
        structured_focus_areas: list[str] = []
        for check_type in failed_check_types:
            if check_type in STRUCTURED_REFINEMENT_GUIDANCE and check_type not in structured_focus_areas:
                structured_focus_areas.append(check_type)

        if structured_focus_areas:
            reason_themes = [
                STRUCTURED_REFINEMENT_GUIDANCE[check_type]["reason"]
                for check_type in structured_focus_areas
            ]
            objective_themes = [
                STRUCTURED_REFINEMENT_GUIDANCE[check_type]["objective"]
                for check_type in structured_focus_areas
            ]
            priority_prefix = "High priority: " if rework_priority == "high" else ""
            return NextIterationPlan(
                next_objective=(
                    f"{base_objective}\n\n"
                    "Refine the previous attempt. "
                    f"{priority_prefix}"
                    f"Focus on these remediation goals: {' '.join(objective_themes)}"
                    f"{(' ' + expansion_objective_suffix) if expansion_objective_suffix else ''}"
                ),
                strategy="refine",
                reason=(
                    f"{priority_prefix}"
                    "Previous round requested refinement to "
                    f"{'; '.join(reason_themes)}."
                    f"{transition_reason}"
                    f"{expansion_transition_reason}"
                ),
                focus_areas=structured_focus_areas + [
                    item for item in expansion_focus_areas if item not in structured_focus_areas
                ],
            )

        suffix = ", ".join(failures) if failures else "the gaps surfaced in the previous attempt"
        return NextIterationPlan(
            next_objective=(
                f"{base_objective}\n\nRefine the previous attempt. Explicitly address: {suffix}."
                f"{(' ' + expansion_objective_suffix) if expansion_objective_suffix else ''}"
            ),
            strategy="refine",
            reason=(
                f"Previous round requested refinement because: {suffix}."
                f"{transition_reason}"
                f"{expansion_transition_reason}"
            ),
            focus_areas=(failures or ["stabilize_previous_attempt"])
            + [item for item in expansion_focus_areas if item not in (failures or ["stabilize_previous_attempt"])],
        )

    if effective_action == "CONTINUE":
        detail = summary or "the successful outputs from the previous round"
        reconcile_coherence_clause = ""
        if (
            anchor_coherence == "divergent"
            and anchor_coherence_expected_hypothesis_ids
            and anchor_coherence_selected_hypothesis_id
        ):
            reconcile_coherence_clause = (
                " anchor coherence expected "
                f"{', '.join(anchor_coherence_expected_hypothesis_ids)} but selected "
                f"{anchor_coherence_selected_hypothesis_id}."
            )
        if backlog_trajectory_signal:
            if f"backlog trajectory {backlog_trajectory_signal}" not in expansion_transition_reason:
                expansion_transition_reason = (
                    f"{expansion_transition_reason} Trajectory-aware continuation signals: backlog trajectory {backlog_trajectory_signal}."
                    if expansion_transition_reason
                    else f" Trajectory-aware continuation signals: backlog trajectory {backlog_trajectory_signal}."
                )
            if backlog_trajectory_signal not in expansion_focus_areas:
                expansion_focus_areas.append(backlog_trajectory_signal)
            if backlog_trajectory_signal == "newly_recovering":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Focus on the newly_recovering backlog trajectory."
                    if expansion_objective_suffix
                    else " Focus on the newly_recovering backlog trajectory."
                )
            elif backlog_trajectory_signal == "strong_recovery":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Build on the strong_recovery backlog trajectory."
                    if expansion_objective_suffix
                    else " Build on the strong_recovery backlog trajectory."
                )
        if hypothesis_trajectory_signal:
            if f"hypothesis trajectory {hypothesis_trajectory_signal}" not in expansion_transition_reason:
                expansion_transition_reason = (
                    f"{expansion_transition_reason} Trajectory-aware continuation signals: hypothesis trajectory {hypothesis_trajectory_signal}."
                    if expansion_transition_reason
                    else f" Trajectory-aware continuation signals: hypothesis trajectory {hypothesis_trajectory_signal}."
                )
            if hypothesis_trajectory_signal not in expansion_focus_areas:
                expansion_focus_areas.append(hypothesis_trajectory_signal)
            if hypothesis_trajectory_signal == "stale_stable":
                expansion_objective_suffix = (
                    f"{expansion_objective_suffix} Avoid relying only on the stale_stable hypothesis trajectory."
                    if expansion_objective_suffix
                    else " Avoid relying only on the stale_stable hypothesis trajectory."
                )
        if expansion_confidence_action == "reconcile_anchor_signals":
            if "reconcile_anchor_signals" not in expansion_focus_areas:
                expansion_focus_areas.append("reconcile_anchor_signals")
            if anchor_divergence_memory.get("divergence_state") == "persistent":
                if "persistent_anchor_divergence_resolution" not in expansion_focus_areas:
                    expansion_focus_areas.append("persistent_anchor_divergence_resolution")
            expansion_objective_suffix = (
                f"{expansion_objective_suffix} Reconcile backlog and hypothesis signals before broader expansion."
                if expansion_objective_suffix
                else " Reconcile backlog and hypothesis signals before broader expansion."
            )
            if "expansion confidence action reconcile_anchor_signals" not in expansion_transition_reason:
                divergence_clause = ""
                if anchor_divergence_memory.get("divergence_state") == "persistent":
                    divergence_clause = " persistent unresolved anchor divergence."
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition follows phase-aware expansion guidance: "
                    "expansion confidence action reconcile_anchor_signals."
                    f"{divergence_clause}{reconcile_coherence_clause}"
                    if not expansion_transition_reason
                    else f"{expansion_transition_reason} "
                    "The continuation path explicitly preserves reconcile_anchor_signals guidance."
                    f"{divergence_clause}{reconcile_coherence_clause}"
                )
        if expansion_confidence_action == "resolve_persistent_action_mode_divergence":
            if "reconcile_anchor_signals" not in expansion_focus_areas:
                expansion_focus_areas.append("reconcile_anchor_signals")
            if "persistent_action_mode_divergence_resolution" not in expansion_focus_areas:
                expansion_focus_areas.append("persistent_action_mode_divergence_resolution")
            action_mode_divergence_memory = candidate_transition.get("action_mode_divergence_memory") or {}
            backlog_divergent_action_mode = action_mode_divergence_memory.get("backlog_action_mode")
            hypothesis_divergent_action_mode = action_mode_divergence_memory.get("hypothesis_action_mode")
            action_mode_clause = " persistent unresolved action-mode divergence."
            if backlog_divergent_action_mode and hypothesis_divergent_action_mode:
                action_mode_clause = (
                    " persistent unresolved action-mode divergence between "
                    f"{backlog_divergent_action_mode} and {hypothesis_divergent_action_mode}."
                )
            if "expansion confidence action resolve_persistent_action_mode_divergence" not in expansion_transition_reason:
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition follows phase-aware expansion guidance: "
                    "expansion confidence action resolve_persistent_action_mode_divergence."
                    f"{action_mode_clause}"
                    if not expansion_transition_reason
                    else f"{expansion_transition_reason} "
                    "The continuation path explicitly preserves resolve_persistent_action_mode_divergence guidance."
                    f"{action_mode_clause}"
                )
        if expansion_confidence_action == "resolve_persistent_coordination_divergence":
            if "reconcile_anchor_signals" not in expansion_focus_areas:
                expansion_focus_areas.append("reconcile_anchor_signals")
            if "persistent_coordination_divergence_resolution" not in expansion_focus_areas:
                expansion_focus_areas.append("persistent_coordination_divergence_resolution")
            coordination_divergence = candidate_transition.get("persistent_coordination_divergence") or {}
            backlog_divergent_action_mode = coordination_divergence.get("backlog_action_mode")
            hypothesis_divergent_action_mode = coordination_divergence.get("hypothesis_action_mode")
            coordination_clause = " persistent unresolved coordination divergence."
            if backlog_divergent_action_mode and hypothesis_divergent_action_mode:
                coordination_clause = (
                    " persistent unresolved coordination divergence;"
                    " action-mode divergence between "
                    f"{backlog_divergent_action_mode} and {hypothesis_divergent_action_mode}."
                )
            if "persistent unresolved coordination divergence" not in expansion_transition_reason:
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition follows phase-aware expansion guidance: "
                    "expansion confidence action resolve_persistent_coordination_divergence."
                    f"{coordination_clause}{reconcile_coherence_clause}"
                    if not expansion_transition_reason
                    else f"{expansion_transition_reason} "
                    "The continuation path explicitly preserves resolve_persistent_coordination_divergence guidance."
                    f"{coordination_clause}{reconcile_coherence_clause}"
                )
        if expansion_confidence_action == "resolve_persistent_joint_reserve_memory":
            if "persistent_joint_reserve_memory_resolution" not in expansion_focus_areas:
                expansion_focus_areas.append("persistent_joint_reserve_memory_resolution")
            joint_reserve_memory = candidate_transition.get("persistent_joint_reserve_memory") or {}
            reserve_experiment_id = joint_reserve_memory.get("experiment_id")
            reserve_hypothesis_id = joint_reserve_memory.get("hypothesis_id")
            reserve_clause = " persistent joint reserve memory."
            if reserve_experiment_id and reserve_hypothesis_id:
                reserve_clause = (
                    " persistent joint reserve memory for "
                    f"{reserve_experiment_id}/{reserve_hypothesis_id}."
                )
            if "persistent joint reserve memory" not in expansion_transition_reason:
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition follows phase-aware expansion guidance: "
                    "expansion confidence action resolve_persistent_joint_reserve_memory."
                    f"{reserve_clause}"
                    if not expansion_transition_reason
                    else f"{expansion_transition_reason} "
                    "The continuation path explicitly preserves resolve_persistent_joint_reserve_memory guidance."
                    f"{reserve_clause}"
                )
        if expansion_confidence_action == "resolve_persistent_anchor_divergence" and effective_action == "CONTINUE":
            divergence_clause = "Resolve the persistent anchor divergence before broader expansion."
            expansion_objective_suffix = (
                f"{expansion_objective_suffix} {divergence_clause}"
                if divergence_clause not in expansion_objective_suffix
                else expansion_objective_suffix
            ) if expansion_objective_suffix else f" {divergence_clause}"
            if "reconcile_anchor_signals" not in expansion_focus_areas:
                expansion_focus_areas.append("reconcile_anchor_signals")
            if "persistent_anchor_divergence_resolution" not in expansion_focus_areas:
                expansion_focus_areas.append("persistent_anchor_divergence_resolution")
            if "expansion confidence action resolve_persistent_anchor_divergence" not in expansion_transition_reason:
                divergence_detail = " persistent unresolved anchor divergence."
                expansion_transition_reason = (
                    f"{expansion_transition_reason}"
                    " The candidate transition follows phase-aware expansion guidance: "
                    "expansion confidence action resolve_persistent_anchor_divergence."
                    f"{divergence_detail}{reconcile_coherence_clause}"
                    if not expansion_transition_reason
                    else f"{expansion_transition_reason} "
                    "The continuation path explicitly preserves resolve_persistent_anchor_divergence guidance."
                    f"{divergence_detail}{reconcile_coherence_clause}"
                )
        if (
            expansion_confidence_action in {"reconcile_anchor_signals", "resolve_persistent_anchor_divergence"}
            and anchor_divergence_memory.get("divergence_state") == "persistent"
            and "persistent unresolved anchor divergence" not in expansion_transition_reason
        ):
            expansion_transition_reason = (
                f"{expansion_transition_reason} persistent unresolved anchor divergence."
                if expansion_transition_reason
                else " persistent unresolved anchor divergence."
            )
        action_mode_divergence_memory = (candidate_transition or {}).get("action_mode_divergence_memory") or {}
        if (
            expansion_confidence_action == "resolve_persistent_action_mode_divergence"
            and action_mode_divergence_memory.get("divergence_state") == "persistent"
            and "persistent unresolved action-mode divergence" not in expansion_transition_reason
        ):
            backlog_divergent_action_mode = action_mode_divergence_memory.get("backlog_action_mode")
            hypothesis_divergent_action_mode = action_mode_divergence_memory.get("hypothesis_action_mode")
            action_mode_divergence_detail = "persistent unresolved action-mode divergence"
            if backlog_divergent_action_mode and hypothesis_divergent_action_mode:
                action_mode_divergence_detail = (
                    "persistent unresolved action-mode divergence between "
                    f"{backlog_divergent_action_mode} and {hypothesis_divergent_action_mode}"
                )
            expansion_transition_reason = (
                f"{expansion_transition_reason} {action_mode_divergence_detail}."
                if expansion_transition_reason
                else f" {action_mode_divergence_detail}."
            )
        return NextIterationPlan(
            next_objective=(
                f"{base_objective}\n\nContinue from the previous successful round. Build on: {detail}"
                f"{(' ' + expansion_objective_suffix) if expansion_objective_suffix else ''}"
            ),
            strategy="continue",
            reason=(
                f"Previous round succeeded and exposed a usable continuation point: {detail}."
                f"{transition_reason}"
                f"{expansion_transition_reason}"
            ),
            focus_areas=["build_on_success"] + [item for item in expansion_focus_areas if item != "build_on_success"],
        )

    if recommended_action in {"ESCALATE", "STOP", "PIVOT"}:
        return NextIterationPlan(
            next_objective=base_objective,
            strategy="hold",
            reason=(
                f"Verifier recommended {recommended_action}, "
                "so the base objective is retained pending review."
            ),
            focus_areas=[],
        )

    return NextIterationPlan(
        next_objective=base_objective,
        strategy="hold",
        reason=f"Previous decision was {effective_action or 'unknown'}, so the base objective is retained.",
        focus_areas=[],
    )


def evolve_objective(base_objective: str, last_record: dict | None) -> str:
    return plan_next_iteration(base_objective, last_record).next_objective


def plan_next_iteration_with_candidate_transition(
    base_objective: str,
    last_record: dict | None,
    *,
    previous_objective: str | None,
    transition_context: dict | None = None,
) -> NextIterationPlan:
    changed = bool(transition_context) or (bool(previous_objective) and previous_objective != base_objective)
    return _plan_next_iteration(
        base_objective,
        last_record,
        candidate_transition={
            "changed": changed,
            "from_objective": previous_objective,
            "to_objective": base_objective,
            **(transition_context or {}),
        },
    )
