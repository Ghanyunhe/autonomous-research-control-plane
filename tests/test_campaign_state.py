from __future__ import annotations

from controlplane.state import campaign_state


def test_assess_resume_readiness_reports_missing_latest_iteration() -> None:
    assert campaign_state.assess_resume_readiness(None) == {
        "resume_ready": False,
        "reasons": ["latest_iteration_missing"],
    }


def test_assess_resume_readiness_reports_missing_planning_signals() -> None:
    assert campaign_state.assess_resume_readiness({"worker_result": {"summary": "partial output"}}) == {
        "resume_ready": False,
        "reasons": ["missing_decision", "missing_verification"],
    }


def test_assess_resume_readiness_accepts_minimal_planning_record() -> None:
    assert campaign_state.assess_resume_readiness(
        {
            "decision": "CONTINUE",
            "verification": {"status": "accept"},
        }
    ) == {
        "resume_ready": True,
        "reasons": [],
    }


def test_build_campaign_summary_carries_resume_signals() -> None:
    summary = campaign_state.build_campaign_summary(
        research_question="Does X help Y?",
        iteration_number=3,
        operator_summary={
            "outcome": "accepted",
            "next_step": "Continue execution from the current objective or successful outputs.",
        },
        verification={"status": "accept", "failed_check_types": []},
        resume_metadata={"requested": True, "source_iteration": 2},
        resume_assessment={"resume_ready": True, "reasons": []},
    )

    assert summary == {
        "research_question": "Does X help Y?",
        "status_headline": "The campaign has completed 3 rounds for the current research question.",
        "latest_outcome": "accepted",
        "next_step": "Continue execution from the current objective or successful outputs.",
        "latest_failed_check_types": [],
        "blocking_issue": None,
        "resume_ready": True,
        "resume_reasons": [],
        "resumed_from_iteration": 2,
    }


def test_build_campaign_summary_surfaces_latest_failure_categories() -> None:
    summary = campaign_state.build_campaign_summary(
        research_question="Does X help Y?",
        iteration_number=2,
        operator_summary={
            "outcome": "needs_refinement",
            "next_step": "Refine the previous attempt and recover the missing artifacts.",
        },
        verification={
            "status": "rework",
            "failed_check_types": ["artifact_presence", "scientific_validity"],
        },
        resume_metadata=None,
        resume_assessment={"resume_ready": True, "reasons": []},
    )

    assert summary == {
        "research_question": "Does X help Y?",
        "status_headline": "The campaign has completed 2 rounds for the current research question.",
        "latest_outcome": "needs_refinement",
        "next_step": "Refine the previous attempt and recover the missing artifacts.",
        "latest_failed_check_types": ["artifact_presence", "scientific_validity"],
        "blocking_issue": "artifact_gap",
        "resume_ready": True,
        "resume_reasons": [],
    }


def test_build_backlog_summary_surfaces_best_and_blocked_candidates() -> None:
    summary = campaign_state.build_backlog_summary(
        {
            "source_type": "file",
            "source_path": "/tmp/demo/backlog.json",
            "candidate_count": 3,
            "active_candidate": {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "hypothesis_links": ["h_exp_best"],
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_best",
                    "objective": "Selected backlog objective",
                    "status": "promising",
                    "times_selected": 2,
                    "last_outcome": "accept",
                },
                {
                    "experiment_id": "exp_blocked",
                    "objective": "Blocked backlog objective",
                    "status": "blocked",
                    "times_selected": 1,
                    "last_outcome": "rework",
                },
                {
                    "experiment_id": "exp_unproven",
                    "objective": "Unproven backlog objective",
                    "status": "unproven",
                    "times_selected": 0,
                    "last_outcome": None,
                },
            ],
            "selection_ready": True,
            "last_selection": {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "selection_iteration": 2,
                    "selection_rationale": {
                        "source": "durable_state",
                        "selection_mode": "tracked_reprioritization",
                        "used_linked_hypothesis_state": True,
                        "used_expansion_recommendations": True,
                        "phase": "stable",
                        "phase_strength": "medium",
                        "frontier_trend": "holding",
                    },
                },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_best",
                    "objective": "Selected backlog objective",
                    "status": "promising",
                    "times_selected": 2,
                    "last_outcome": "accept",
                },
                {
                    "experiment_id": "exp_blocked",
                    "objective": "Blocked backlog objective",
                    "status": "blocked",
                    "times_selected": 1,
                    "last_outcome": "rework",
                },
                {
                    "experiment_id": "exp_unproven",
                    "objective": "Unproven backlog objective",
                    "status": "unproven",
                    "times_selected": 0,
                    "last_outcome": None,
                },
            ],
            "backlog_evolution_summary": {
                "ranked_candidates": [
                    {
                        "experiment_id": "exp_best",
                        "score_band": "high",
                        "reason": "accelerating high-confidence anchor",
                        "action_mode": "scale_confident_anchor",
                        "suppressed_by": None,
                    },
                    {
                        "experiment_id": "exp_shadow",
                        "score_band": "medium",
                        "reason": "recovering medium-confidence anchor",
                        "action_mode": "stabilize_recovery",
                        "suppressed_by": "weaker_phase_strength",
                    },
                ]
            },
        }
    )

    assert summary == {
        "selection_ready": True,
        "active_experiment_id": "exp_best",
        "active_objective": "Selected backlog objective",
        "promising_candidates": ["exp_best"],
        "blocked_candidates": ["exp_blocked"],
        "unproven_candidates": ["exp_unproven"],
        "recommended_anchor_experiment_id": "exp_best",
        "recommended_anchor_status": "promising",
        "recommended_anchor_selection_context": {
            "experiment_id": "exp_best",
            "selection_iteration": 2,
            "source": "durable_state",
            "selection_mode": "tracked_reprioritization",
            "used_linked_hypothesis_state": True,
            "used_expansion_recommendations": True,
            "phase": "stable",
            "phase_strength": "medium",
            "frontier_trend": "holding",
            "selection_state_hint": "stable / medium selected anchor",
            "anchor_trend_hint": "holding selected anchor",
        },
        "alternative_anchor_context": {
            "experiment_id": "exp_shadow",
            "score_band": "medium",
            "reason": "recovering medium-confidence anchor",
            "action_mode": "stabilize_recovery",
            "suppressed_by": "weaker_phase_strength",
        },
    }


def test_build_backlog_evolution_summary_surfaces_trends_and_next_action() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "active_candidate": {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_best",
                    "status": "promising",
                    "current_accept_streak": 3,
                    "current_rework_streak": 0,
                },
                {
                    "experiment_id": "exp_blocked",
                    "status": "blocked",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
                {
                    "experiment_id": "exp_recovering",
                    "status": "mixed",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_candidates": ["exp_best"],
        "regressing_candidates": ["exp_blocked"],
        "recovery_candidates": ["exp_recovering"],
        "accelerating_candidates": [],
        "stable_candidates": [],
        "recommended_experiment_id": "exp_best",
        "recommended_action": "promote_promising_candidate",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "status": "promising",
                "recommendation_state_hint": "promising recommended anchor",
            },
        "ranked_candidates": [
            {
                "experiment_id": "exp_best",
                "score_band": "low",
                "reason": "stable low-confidence anchor",
                "action_mode": "validate_low_confidence_anchor",
                "score_signals": {
                    "status": "promising",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "suppressed_by": None,
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
            {
                "experiment_id": "exp_blocked",
                "score_band": "low",
                "reason": "regressing medium-confidence anchor",
                "action_mode": "recover_regressing_anchor",
                "score_signals": {
                    "status": "blocked",
                    "phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "recover_regressing_anchor",
                },
                "suppressed_by": "action_mode_misalignment",
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
            {
                "experiment_id": "exp_recovering",
                "score_band": "medium",
                "reason": "recovering medium-confidence anchor",
                "action_mode": "stabilize_recovery",
                "score_signals": {
                    "status": "mixed",
                    "phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_recovery",
                    "action_mode": "stabilize_recovery",
                },
                "suppressed_by": "weaker_phase_strength",
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
        ],
        "status_headline": "A promising backlog candidate is advancing, but some candidates still need recovery.",
    }


def test_build_backlog_evolution_summary_prefers_unblocked_alternative_when_only_regressing_candidates_have_history() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "tracked_candidates": [
                {
                    "experiment_id": "exp_blocked",
                    "status": "blocked",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
                {
                    "experiment_id": "exp_unproven",
                    "status": "unproven",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_candidates": [],
        "regressing_candidates": ["exp_blocked"],
        "recovery_candidates": [],
        "accelerating_candidates": [],
        "stable_candidates": [],
        "recommended_experiment_id": "exp_unproven",
        "recommended_action": "recover_regressing_candidate",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "status": "unproven",
                "recommendation_state_hint": "unproven recommended anchor",
            },
            "ranked_candidates": [
                {
                    "experiment_id": "exp_blocked",
                    "score_band": "low",
                    "reason": "regressing medium-confidence anchor",
                    "action_mode": "recover_regressing_anchor",
                    "score_signals": {
                        "status": "blocked",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_regressing_anchor",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "experiment_id": "exp_unproven",
                    "score_band": "low",
                    "reason": "unproven low-confidence anchor",
                    "action_mode": "observe_insufficient_signal",
                    "score_signals": {
                        "status": "unproven",
                        "phase": "unproven",
                        "phase_strength": "low",
                        "trajectory_signal": "unproven",
                        "action_mode": "observe_insufficient_signal",
                    },
                    "suppressed_by": "action_mode_misalignment",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        "status_headline": "The campaign's active backlog candidates are regressing and should shift toward a healthier candidate.",
    }


def test_build_hypothesis_summary_surfaces_supported_and_unstable_hypotheses() -> None:
    summary = campaign_state.build_hypothesis_summary(
        {
            "active_hypotheses": ["h_supported"],
            "last_selection": {
                "hypothesis_links": ["h_supported", "h_unknown"],
                "selection_iteration": 2,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "projected_from_experiment_id": "exp_best",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                },
            },
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "status": "supported",
                    "times_selected": 2,
                    "last_outcome": "accept",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "times_selected": 2,
                    "last_outcome": "rework",
                },
                {
                    "hypothesis_id": "h_unknown",
                    "status": "unknown",
                    "times_selected": 0,
                    "last_outcome": None,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "active_hypotheses": ["h_supported"],
        "supported_hypotheses": ["h_supported"],
        "unstable_hypotheses": ["h_unstable"],
        "mixed_hypotheses": [],
        "unknown_hypotheses": ["h_unknown"],
        "recommended_hypothesis_id": "h_supported",
        "recommended_hypothesis_status": "supported",
        "ranked_active_hypotheses": [
            {
                "hypothesis_id": "h_supported",
                "status": "supported",
                "evolution_phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
                "suppressed_by": None,
                "frontier_age": "new",
                "frontier_trend": "rising",
            }
        ],
        "recommended_hypothesis_selection_context": {
            "selection_iteration": 2,
            "source": "backlog_candidate_links",
            "selection_mode": "selected_candidate_projection",
            "projected_from_experiment_id": "exp_best",
            "used_backlog_context": True,
            "used_expansion_recommendations": False,
        },
    }


def test_build_hypothesis_summary_surfaces_active_alternative_context() -> None:
    summary = campaign_state.build_hypothesis_summary(
        {
            "active_hypotheses": ["h_supported", "h_unstable"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "status": "supported",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "reroute_for_stronger_evidence",
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["active_alternative_context"] == {
        "hypothesis_id": "h_unstable",
        "status": "unstable",
        "evolution_phase": "regressing",
        "phase_strength": "medium",
        "trajectory_signal": "continuing_regression",
        "action_mode": "reroute_for_stronger_evidence",
        "suppressed_by": "action_mode_misalignment",
        "frontier_age": "new",
        "frontier_trend": "rising",
        "alternative_state_hint": "unstable / regressing / medium / continuing_regression reserve active hypothesis anchor",
    }


def test_build_hypothesis_evolution_summary_surfaces_trends_and_next_action() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "active_hypotheses": ["h_supported"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "status": "supported",
                    "current_accept_streak": 3,
                    "current_rework_streak": 0,
                },
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
                {
                    "hypothesis_id": "h_mixed",
                    "status": "mixed",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_hypotheses": ["h_supported"],
        "regressing_hypotheses": ["h_unstable"],
        "recovery_hypotheses": ["h_mixed"],
        "accelerating_hypotheses": [],
        "stable_hypotheses": [],
        "recommended_hypothesis_id": "h_supported",
        "recommended_action": "promote_supported_hypothesis",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "status": "supported",
                "recommendation_state_hint": "supported recommended hypothesis anchor",
            },
            "ranked_hypotheses": [
                {
                    "hypothesis_id": "h_mixed",
                    "score_band": "medium",
                    "reason": "recovering medium-confidence anchor",
                    "action_mode": "stabilize_recovery",
                    "score_signals": {
                        "status": "mixed",
                        "phase": "recovering",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_recovery",
                        "action_mode": "stabilize_recovery",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_supported",
                    "score_band": "low",
                    "reason": "stable low-confidence anchor",
                    "action_mode": "validate_low_confidence_anchor",
                    "score_signals": {
                        "status": "supported",
                        "phase": "stable",
                        "phase_strength": "low",
                        "trajectory_signal": "stale_stable",
                        "action_mode": "validate_low_confidence_anchor",
                    },
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "score_band": "low",
                    "reason": "regressing medium-confidence anchor",
                    "action_mode": "recover_regressing_anchor",
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_regressing_anchor",
                    },
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        "status_headline": "A supported hypothesis is advancing, but some hypotheses still need stabilization.",
    }


def test_build_backlog_evolution_summary_surfaces_phase_aware_groups() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "tracked_candidates": [
                {
                    "experiment_id": "exp_accel",
                    "status": "promising",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                },
                {
                    "experiment_id": "exp_stable",
                    "status": "promising",
                    "evolution_phase": "stable",
                    "phase_strength": "medium",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
                {
                    "experiment_id": "exp_recovering",
                    "status": "mixed",
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                },
                {
                    "experiment_id": "exp_regressing",
                    "status": "blocked",
                    "evolution_phase": "regressing",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["accelerating_candidates"] == ["exp_accel"]
    assert summary["stable_candidates"] == ["exp_stable"]
    assert summary["phase_strength_signal"] == "high"
    assert summary["recovery_candidates"] == ["exp_recovering"]
    assert summary["regressing_candidates"] == ["exp_regressing"]


def test_build_hypothesis_evolution_summary_surfaces_phase_aware_groups() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_accel",
                    "status": "supported",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                },
                {
                    "hypothesis_id": "h_stable",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "phase_strength": "medium",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
                {
                    "hypothesis_id": "h_recovering",
                    "status": "mixed",
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                },
                {
                    "hypothesis_id": "h_regressing",
                    "status": "unstable",
                    "evolution_phase": "regressing",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["accelerating_hypotheses"] == ["h_accel"]
    assert summary["stable_hypotheses"] == ["h_stable"]
    assert summary["phase_strength_signal"] == "high"
    assert summary["recovery_hypotheses"] == ["h_recovering"]
    assert summary["regressing_hypotheses"] == ["h_regressing"]


def test_build_hypothesis_evolution_summary_prefers_non_unstable_alternative_when_only_regressing_hypotheses_have_history() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "active_hypotheses": ["h_unstable"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                },
                {
                    "hypothesis_id": "h_unknown",
                    "status": "unknown",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_hypotheses": [],
        "regressing_hypotheses": ["h_unstable"],
        "recovery_hypotheses": [],
        "accelerating_hypotheses": [],
        "stable_hypotheses": [],
        "recommended_hypothesis_id": "h_unknown",
        "recommended_action": "stabilize_regressing_hypothesis",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "status": "unknown",
                "recommendation_state_hint": "unknown recommended hypothesis anchor",
            },
            "ranked_hypotheses": [
                {
                    "hypothesis_id": "h_unknown",
                    "score_band": "low",
                    "reason": "unproven low-confidence anchor",
                    "action_mode": "observe_insufficient_signal",
                    "score_signals": {
                        "status": "unknown",
                        "phase": "unproven",
                        "phase_strength": "low",
                        "trajectory_signal": "unproven",
                        "action_mode": "observe_insufficient_signal",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "score_band": "low",
                    "reason": "regressing medium-confidence anchor",
                    "action_mode": "recover_regressing_anchor",
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_regressing_anchor",
                    },
                    "suppressed_by": "action_mode_misalignment",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        "status_headline": "The campaign's active hypothesis signals are regressing and should shift toward a healthier hypothesis anchor.",
    }


def test_build_backlog_evolution_summary_treats_mixed_regressing_candidates_as_regressing() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "active_candidate": {
                "experiment_id": "exp_decay",
                "objective": "Decaying objective",
                "hypothesis_links": ["h_decay"],
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_decay",
                    "status": "mixed",
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                },
                {
                    "experiment_id": "exp_alt",
                    "status": "promising",
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["regressing_candidates"] == ["exp_decay"]
    assert summary["recommended_experiment_id"] == "exp_alt"
    assert summary["recommended_action"] == "recover_regressing_candidate"
    assert "regressing" in summary["status_headline"]


def test_build_hypothesis_evolution_summary_treats_mixed_regressing_hypotheses_as_regressing() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "active_hypotheses": ["h_decay"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_decay",
                    "status": "mixed",
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                },
                {
                    "hypothesis_id": "h_alt",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["regressing_hypotheses"] == ["h_decay"]
    assert summary["recommended_hypothesis_id"] == "h_alt"
    assert summary["recommended_action"] == "stabilize_regressing_hypothesis"
    assert "regressing" in summary["status_headline"]


def test_build_backlog_evolution_summary_ignores_inactive_mixed_regressing_reserve_candidates() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "active_candidate": {
                "experiment_id": "exp_alt",
                "objective": "Healthier objective",
                "hypothesis_links": ["h_alt"],
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_decay",
                    "status": "mixed",
                    "evolution_phase": "regressing",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                },
                {
                    "experiment_id": "exp_alt",
                    "status": "promising",
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["regressing_candidates"] == []
    assert summary["recommended_experiment_id"] == "exp_alt"
    assert summary["recommended_action"] == "promote_promising_candidate"
    assert summary["status_headline"] == "A promising backlog candidate is advancing and ready to promote."


def test_build_hypothesis_evolution_summary_ignores_inactive_mixed_regressing_reserve_hypotheses() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "active_hypotheses": ["h_alt"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_decay",
                    "status": "mixed",
                    "evolution_phase": "regressing",
                    "phase_strength": "low",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                },
                {
                    "hypothesis_id": "h_alt",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary["regressing_hypotheses"] == []
    assert summary["recommended_hypothesis_id"] == "h_alt"
    assert summary["recommended_action"] == "promote_supported_hypothesis"
    assert summary["status_headline"] == "A supported hypothesis is advancing and ready to promote."


def test_build_backlog_evolution_summary_mentions_dominant_failure_mode_when_regressing() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "tracked_candidates": [
                {
                    "experiment_id": "exp_blocked",
                    "status": "blocked",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                    "dominant_failure_mode": "scientific_validity",
                    "action_mode": "reroute_for_stronger_evidence",
                },
                {
                    "experiment_id": "exp_unproven",
                    "status": "unproven",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                    "action_mode": "observe_insufficient_signal",
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_candidates": [],
        "regressing_candidates": ["exp_blocked"],
        "recovery_candidates": [],
        "accelerating_candidates": [],
        "stable_candidates": [],
        "recommended_experiment_id": "exp_unproven",
        "recommended_action": "recover_regressing_candidate",
        "recommended_action_mode": "observe_insufficient_signal",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "action_mode": "observe_insufficient_signal",
                "status": "unproven",
                "recommendation_state_hint": "unproven / observe_insufficient_signal recommended anchor",
            },
            "ranked_candidates": [
                {
                    "experiment_id": "exp_blocked",
                    "score_band": "low",
                    "reason": "regressing medium-confidence anchor",
                    "action_mode": "reroute_for_stronger_evidence",
                    "score_signals": {
                        "status": "blocked",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "reroute_for_stronger_evidence",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "experiment_id": "exp_unproven",
                    "score_band": "low",
                    "reason": "unproven low-confidence anchor",
                    "action_mode": "observe_insufficient_signal",
                    "score_signals": {
                        "status": "unproven",
                        "phase": "unproven",
                        "phase_strength": "low",
                        "trajectory_signal": "unproven",
                        "action_mode": "observe_insufficient_signal",
                    },
                    "suppressed_by": "action_mode_misalignment",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        "dominant_failure_mode": "scientific_validity",
        "status_headline": "The campaign's active backlog candidates are regressing due to scientific_validity failures and should shift toward a healthier candidate.",
    }


def test_build_campaign_backlog_derives_evolution_phase_for_tracked_candidates() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "tracked_candidates": [
                {
                    "experiment_id": "exp_accelerating",
                    "objective": "Accelerating objective",
                    "hypothesis_links": ["h1"],
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "accept",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                    ],
                },
                {
                    "experiment_id": "exp_regressing",
                    "objective": "Regressing objective",
                    "hypothesis_links": ["h2"],
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "rework",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {
                            "selection_iteration": 2,
                            "outcome": "rework",
                            "failed_check_types": ["scientific_validity"],
                        },
                        {
                            "selection_iteration": 3,
                            "outcome": "rework",
                            "failed_check_types": ["scientific_validity"],
                        },
                    ],
                },
            ],
        },
        selected_candidate={
            "experiment_id": "exp_accelerating",
            "objective": "Accelerating objective",
            "hypothesis_links": ["h1"],
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=3,
        verification={"status": "accept"},
    )

    tracked = {item["experiment_id"]: item for item in backlog["tracked_candidates"]}
    assert tracked["exp_accelerating"]["evolution_phase"] == "accelerating"
    assert tracked["exp_accelerating"]["phase_strength"] == "medium"
    assert tracked["exp_regressing"]["evolution_phase"] == "regressing"
    assert tracked["exp_regressing"]["phase_strength"] == "medium"


def test_build_hypothesis_evolution_summary_mentions_dominant_failure_mode_when_regressing() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "active_hypotheses": ["h_unstable"],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                    "dominant_failure_mode": "artifact_presence",
                    "action_mode": "recover_missing_artifacts",
                },
                {
                    "hypothesis_id": "h_unknown",
                    "status": "unknown",
                    "current_accept_streak": 0,
                    "current_rework_streak": 0,
                    "action_mode": "observe_insufficient_signal",
                },
            ],
            "selection_ready": True,
        }
    )

    assert summary == {
        "selection_ready": True,
        "advancing_hypotheses": [],
        "regressing_hypotheses": ["h_unstable"],
        "recovery_hypotheses": [],
        "accelerating_hypotheses": [],
        "stable_hypotheses": [],
        "recommended_hypothesis_id": "h_unknown",
        "recommended_action": "stabilize_regressing_hypothesis",
        "recommended_action_mode": "observe_insufficient_signal",
            "recommended_trajectory_signal": "unproven",
            "recommendation_drivers": {
                "action_mode": "observe_insufficient_signal",
                "status": "unknown",
                "recommendation_state_hint": "unknown / observe_insufficient_signal recommended hypothesis anchor",
            },
            "ranked_hypotheses": [
                {
                    "hypothesis_id": "h_unknown",
                    "score_band": "low",
                    "reason": "unproven low-confidence anchor",
                    "action_mode": "observe_insufficient_signal",
                    "score_signals": {
                        "status": "unknown",
                        "phase": "unproven",
                        "phase_strength": "low",
                        "trajectory_signal": "unproven",
                        "action_mode": "observe_insufficient_signal",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "score_band": "low",
                    "reason": "regressing medium-confidence anchor",
                    "action_mode": "recover_missing_artifacts",
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_missing_artifacts",
                    },
                    "suppressed_by": "action_mode_misalignment",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        "dominant_failure_mode": "artifact_presence",
        "status_headline": "The campaign's active hypothesis signals are regressing due to artifact_presence failures and should shift toward a healthier hypothesis anchor.",
    }


def test_build_backlog_evolution_summary_surfaces_pending_promotion_pressure() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "selection_ready": True,
            "tracked_candidates": [
                {
                    "experiment_id": "exp_leader",
                    "status": "promising",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "established_stable",
                    "action_mode": "maintain_viable_anchor",
                },
                {
                    "experiment_id": "exp_alt",
                    "status": "promising",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 3,
                    "recommended_id": "exp_leader",
                    "ranked_ids": ["exp_leader", "exp_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising+promotion_blocked+promotion_pending",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "exp_alt",
                        "promotion_pressure_streak": 2,
                        "promotion_pressure_state": "persistent",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": False,
                        "promotion_gate_blocker": "challenger_recent_rework",
                    },
                }
            ],
        }
    )

    assert summary["recommended_experiment_id"] == "exp_alt"
    assert summary["recommended_action"] == "investigate_pending_candidate_promotion"
    assert summary["pending_promotion_candidate_id"] == "exp_alt"
    assert summary["pending_promotion_gate_blocker"] == "challenger_recent_rework"
    assert summary["pending_promotion_pressure_streak"] == 2
    assert summary["status_headline"] == (
        "A rising backlog challenger has been blocked from promotion across consecutive rounds and should be investigated before promotion."
    )


def test_build_hypothesis_evolution_summary_surfaces_pending_promotion_pressure() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "selection_ready": True,
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_leader",
                    "status": "supported",
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "established_stable",
                    "action_mode": "maintain_viable_anchor",
                },
                {
                    "hypothesis_id": "h_alt",
                    "status": "supported",
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "promote_emerging_anchor",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 3,
                    "recommended_id": "h_leader",
                    "ranked_ids": ["h_leader", "h_alt"],
                    "movement_summary": "leader_held+promotion_blocked+promotion_pending",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "h_alt",
                        "promotion_pressure_streak": 2,
                        "promotion_pressure_state": "persistent",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": False,
                        "promotion_gate_blocker": "challenger_recent_rework",
                    },
                }
            ],
        }
    )

    assert summary["recommended_hypothesis_id"] == "h_alt"
    assert summary["recommended_action"] == "investigate_pending_hypothesis_promotion"
    assert summary["pending_promotion_hypothesis_id"] == "h_alt"
    assert summary["pending_promotion_gate_blocker"] == "challenger_recent_rework"
    assert summary["pending_promotion_pressure_streak"] == 2
    assert summary["status_headline"] == (
        "A rising hypothesis challenger has been blocked from promotion across consecutive rounds and should be investigated before promotion."
    )


def test_build_backlog_evolution_summary_surfaces_promotion_ready_challenger() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "selection_ready": True,
            "tracked_candidates": [
                {
                    "experiment_id": "exp_leader",
                    "status": "mixed",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "recover_regressing_anchor",
                },
                {
                    "experiment_id": "exp_alt",
                    "status": "promising",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 3,
                    "recommended_id": "exp_leader",
                    "ranked_ids": ["exp_leader", "exp_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "exp_alt",
                        "promotion_pressure_streak": 2,
                        "promotion_pressure_state": "persistent",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": True,
                    },
                }
            ],
        }
    )

    assert summary["recommended_experiment_id"] == "exp_alt"
    assert summary["recommended_action"] == "promote_ready_candidate"
    assert summary["promotion_ready_candidate_id"] == "exp_alt"
    assert summary["promotion_ready_pressure_streak"] == 2
    assert summary["status_headline"] == (
        "A rising backlog challenger has cleared the promotion gate and should now be promoted over the decaying leader."
    )


def test_build_hypothesis_evolution_summary_surfaces_promotion_ready_challenger() -> None:
    summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "selection_ready": True,
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_leader",
                    "status": "mixed",
                    "current_accept_streak": 0,
                    "current_rework_streak": 2,
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "recover_regressing_anchor",
                },
                {
                    "hypothesis_id": "h_alt",
                    "status": "supported",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "recovering",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_recovery",
                    "action_mode": "promote_emerging_anchor",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 3,
                    "recommended_id": "h_leader",
                    "ranked_ids": ["h_leader", "h_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "h_alt",
                        "promotion_pressure_streak": 2,
                        "promotion_pressure_state": "persistent",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": True,
                    },
                }
            ],
        }
    )

    assert summary["recommended_hypothesis_id"] == "h_alt"
    assert summary["recommended_action"] == "promote_ready_hypothesis"
    assert summary["promotion_ready_hypothesis_id"] == "h_alt"
    assert summary["promotion_ready_pressure_streak"] == 2
    assert summary["status_headline"] == (
        "A rising hypothesis challenger has cleared the promotion gate and should now be promoted over the decaying leader."
    )


def test_build_campaign_backlog_derives_action_mode_for_tracked_candidates() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "tracked_candidates": [
                {
                    "experiment_id": "exp_accel",
                    "objective": "Accelerating objective",
                    "hypothesis_links": ["h1"],
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "accept",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                        {"selection_iteration": 3, "outcome": "accept"},
                    ],
                },
                {
                    "experiment_id": "exp_regress",
                    "objective": "Regressing objective",
                    "hypothesis_links": ["h2"],
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "rework",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {
                            "selection_iteration": 2,
                            "outcome": "rework",
                            "failed_check_types": ["scientific_validity"],
                        },
                        {
                            "selection_iteration": 3,
                            "outcome": "rework",
                            "failed_check_types": ["scientific_validity"],
                        },
                    ],
                },
            ],
        },
        selected_candidate={
            "experiment_id": "exp_accel",
            "objective": "Accelerating objective",
            "hypothesis_links": ["h1"],
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=4,
        verification={"status": "accept"},
    )

    tracked = {item["experiment_id"]: item for item in backlog["tracked_candidates"]}
    assert tracked["exp_accel"]["action_mode"] == "scale_confident_anchor"
    assert tracked["exp_regress"]["action_mode"] == "reroute_for_stronger_evidence"


def test_build_campaign_hypotheses_derives_action_mode_for_tracked_hypotheses() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "accept",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                    ],
                },
                {
                    "hypothesis_id": "h_regressing",
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "rework",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {
                            "selection_iteration": 2,
                            "outcome": "rework",
                            "failed_check_types": ["artifact_presence"],
                        },
                        {
                            "selection_iteration": 3,
                            "outcome": "rework",
                            "failed_check_types": ["artifact_presence"],
                        },
                    ],
                },
            ]
        },
        hypothesis_links=["h_supported"],
        verification={"status": "accept"},
        iteration_number=3,
    )

    tracked = {item["hypothesis_id"]: item for item in hypotheses["tracked_hypotheses"]}
    assert tracked["h_supported"]["action_mode"] == "promote_emerging_anchor"
    assert tracked["h_regressing"]["action_mode"] == "recover_missing_artifacts"


def test_build_campaign_hypotheses_derives_evolution_phase_for_tracked_hypotheses() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "accept",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                    ],
                },
                {
                    "hypothesis_id": "h_unstable",
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "rework",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {
                            "selection_iteration": 2,
                            "outcome": "rework",
                            "failed_check_types": ["artifact_presence"],
                        },
                        {
                            "selection_iteration": 3,
                            "outcome": "rework",
                            "failed_check_types": ["artifact_presence"],
                        },
                    ],
                },
            ]
        },
        hypothesis_links=["h_supported"],
        verification={"status": "accept"},
        iteration_number=3,
    )

    tracked = {item["hypothesis_id"]: item for item in hypotheses["tracked_hypotheses"]}
    assert tracked["h_supported"]["evolution_phase"] == "accelerating"
    assert tracked["h_supported"]["phase_strength"] == "medium"
    assert tracked["h_unstable"]["evolution_phase"] == "regressing"
    assert tracked["h_unstable"]["phase_strength"] == "medium"


def test_build_campaign_backlog_derives_phase_strength_for_tracked_candidates() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "tracked_candidates": [
                {
                    "experiment_id": "exp_high",
                    "objective": "High confidence accelerating objective",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                        {"selection_iteration": 3, "outcome": "accept"},
                    ],
                },
                {
                    "experiment_id": "exp_low",
                    "objective": "Low confidence accelerating objective",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                    ],
                },
            ],
        },
        selected_candidate={
            "experiment_id": "exp_high",
            "objective": "High confidence accelerating objective",
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=3,
        verification={"status": "accept"},
    )

    tracked = {item["experiment_id"]: item for item in backlog["tracked_candidates"]}
    assert tracked["exp_high"]["evolution_phase"] == "accelerating"
    assert tracked["exp_high"]["phase_strength"] == "high"
    assert tracked["exp_low"]["evolution_phase"] == "stable"
    assert tracked["exp_low"]["phase_strength"] == "low"


def test_build_campaign_hypotheses_derives_phase_strength_for_tracked_hypotheses() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_high",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "accept"},
                        {"selection_iteration": 3, "outcome": "accept"},
                    ],
                },
                {
                    "hypothesis_id": "h_low",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                    ],
                },
            ]
        },
        hypothesis_links=["h_high"],
        verification={"status": "accept"},
        iteration_number=3,
    )

    tracked = {item["hypothesis_id"]: item for item in hypotheses["tracked_hypotheses"]}
    assert tracked["h_high"]["evolution_phase"] == "accelerating"
    assert tracked["h_high"]["phase_strength"] == "high"
    assert tracked["h_low"]["evolution_phase"] == "stable"
    assert tracked["h_low"]["phase_strength"] == "low"


def test_build_campaign_backlog_derives_trajectory_signal_for_tracked_candidates() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "tracked_candidates": [
                {
                    "experiment_id": "exp_new_recovery",
                    "objective": "Newly recovering objective",
                    "history": [
                        {
                            "selection_iteration": 1,
                            "outcome": "rework",
                            "failed_check_types": ["artifact_presence"],
                        }
                    ],
                },
                {
                    "experiment_id": "exp_stale_stable",
                    "objective": "Stale stable objective",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                    ],
                },
            ],
        },
        selected_candidate={
            "experiment_id": "exp_new_recovery",
            "objective": "Newly recovering objective",
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=3,
        verification={"status": "accept"},
    )

    tracked = {item["experiment_id"]: item for item in backlog["tracked_candidates"]}
    assert tracked["exp_new_recovery"]["evolution_phase"] == "recovering"
    assert tracked["exp_stale_stable"]["evolution_phase"] == "stable"

    summary = campaign_state.build_backlog_evolution_summary(backlog)
    assert summary["recommended_experiment_id"] == "exp_new_recovery"
    assert summary["recommended_trajectory_signal"] == "newly_recovering"


def test_build_backlog_evolution_summary_surfaces_trajectory_signal() -> None:
    summary = campaign_state.build_backlog_evolution_summary(
        {
            "selection_ready": True,
            "tracked_candidates": [
                {
                    "experiment_id": "exp_new_recovery",
                    "status": "mixed",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "stabilize_recovery",
                },
                {
                    "experiment_id": "exp_stale_stable",
                    "status": "promising",
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
            ],
        }
    )

    assert summary["recommended_experiment_id"] == "exp_new_recovery"
    assert summary["recommended_trajectory_signal"] == "newly_recovering"


def test_build_evolution_summaries_surface_recommendation_drivers() -> None:
    backlog_summary = campaign_state.build_backlog_evolution_summary(
        {
            "selection_ready": True,
            "tracked_candidates": [
                {
                    "experiment_id": "exp_new_recovery",
                    "status": "mixed",
                    "accept_count": 1,
                    "rework_count": 1,
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "stabilize_recovery",
                    "frontier_trend": "rising",
                    "hypothesis_links": ["h_stale"],
                },
            ],
        }
    )
    hypothesis_summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "selection_ready": True,
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_stale",
                    "status": "supported",
                    "accept_count": 1,
                    "rework_count": 0,
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                    "frontier_trend": "holding",
                },
            ],
        }
    )

    assert backlog_summary["recommendation_drivers"] == {
        "phase": "recovering",
        "phase_strength": "medium",
        "trajectory_signal": "newly_recovering",
        "action_mode": "stabilize_recovery",
        "status": "mixed",
        "recommendation_state_hint": "mixed / recovering / medium / newly_recovering / stabilize_recovery recommended anchor",
        "anchor_trend_hint": "rising recommended anchor",
    }
    assert hypothesis_summary["recommendation_drivers"] == {
        "phase": "stable",
        "phase_strength": "low",
        "trajectory_signal": "stale_stable",
        "action_mode": "validate_low_confidence_anchor",
        "status": "supported",
        "recommendation_state_hint": "supported / stable / low / stale_stable / validate_low_confidence_anchor recommended hypothesis anchor",
        "anchor_trend_hint": "holding recommended hypothesis anchor",
    }


def test_build_expansion_summary_combines_backlog_and_hypothesis_signals() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "active_experiment_id": "exp_best",
            "active_objective": "Selected backlog objective",
            "promising_candidates": ["exp_best"],
            "blocked_candidates": ["exp_blocked"],
            "unproven_candidates": [],
            "recommended_anchor_experiment_id": "exp_best",
            "recommended_anchor_status": "promising",
            "recommended_anchor_selection_context": {
                "experiment_id": "exp_best",
                "selection_iteration": 3,
                "source": "durable_state",
                "selection_mode": "tracked_reprioritization",
                "used_linked_hypothesis_state": True,
                "used_expansion_recommendations": True,
                "score_signals": {
                    "status": "promising",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "anchor_trend_hint": "holding selected anchor",
            },
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "advancing_candidates": ["exp_best"],
            "regressing_candidates": ["exp_blocked"],
            "recovery_candidates": [],
            "recommended_experiment_id": "exp_best",
            "recommended_action": "promote_promising_candidate",
            "dominant_failure_mode": None,
            "status_headline": "A promising backlog candidate is advancing, but some candidates still need recovery.",
        },
        hypothesis_summary={
            "selection_ready": True,
            "active_hypotheses": ["h_supported"],
            "supported_hypotheses": ["h_supported"],
            "unstable_hypotheses": ["h_unstable"],
            "mixed_hypotheses": [],
            "unknown_hypotheses": [],
            "recommended_hypothesis_id": "h_supported",
            "recommended_hypothesis_status": "supported",
            "ranked_active_hypotheses": [
                {
                    "hypothesis_id": "h_supported",
                    "status": "supported",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_unstable",
                    "status": "unstable",
                    "evolution_phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "reroute_for_stronger_evidence",
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
            "recommended_hypothesis_selection_context": {
                "selection_iteration": 4,
                "source": "backlog_candidate_links",
                "selection_mode": "selected_candidate_projection",
                "projected_from_experiment_id": "exp_best",
                "used_backlog_context": True,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "supported",
                    "phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
                "selection_state_hint": "supported / accelerating / high / strong_acceleration selected hypothesis anchor",
                "anchor_trend_hint": "rising selected hypothesis anchor",
            },
            "active_alternative_context": {
                "hypothesis_id": "h_unstable",
                "status": "unstable",
                "evolution_phase": "regressing",
                "phase_strength": "medium",
                "trajectory_signal": "continuing_regression",
                "action_mode": "reroute_for_stronger_evidence",
                "suppressed_by": "action_mode_misalignment",
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "advancing_hypotheses": ["h_supported"],
            "regressing_hypotheses": ["h_unstable"],
            "recovery_hypotheses": [],
            "recommended_hypothesis_id": "h_supported",
            "recommended_action": "promote_supported_hypothesis",
            "dominant_failure_mode": None,
            "status_headline": "A supported hypothesis is advancing, but some hypotheses still need stabilization.",
        },
    )

    assert summary == {
        "expansion_ready": True,
        "recommended_experiment_id": "exp_best",
        "recommended_hypothesis_id": "h_supported",
        "risk_flags": ["blocked_backlog_candidates", "unstable_hypotheses"],
        "next_expansion_action": "stabilize_hypotheses",
        "status_headline": "The campaign has reusable anchors, but unstable hypotheses still need stabilization.",
        "recommended_backlog_action": "promote_promising_candidate",
        "recommended_hypothesis_action": "promote_supported_hypothesis",
        "backlog_phase_signal": "regressing",
        "hypothesis_phase_signal": "regressing",
        "backlog_selection_context": {
            "experiment_id": "exp_best",
            "selection_iteration": 3,
            "source": "durable_state",
            "selection_mode": "tracked_reprioritization",
            "used_linked_hypothesis_state": True,
            "used_expansion_recommendations": True,
            "score_signals": {
                "status": "promising",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "anchor_trend_hint": "holding selected anchor",
        },
        "hypothesis_selection_context": {
            "selection_iteration": 4,
            "source": "backlog_candidate_links",
            "selection_mode": "selected_candidate_projection",
            "projected_from_experiment_id": "exp_best",
            "used_backlog_context": True,
            "used_expansion_recommendations": False,
            "score_signals": {
                "status": "supported",
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
            },
            "selection_state_hint": "supported / accelerating / high / strong_acceleration selected hypothesis anchor",
            "anchor_trend_hint": "rising selected hypothesis anchor",
        },
        "hypothesis_ranked_active_alternatives": [
            {
                "hypothesis_id": "h_supported",
                "status": "supported",
                "evolution_phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
                "suppressed_by": None,
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
            {
                "hypothesis_id": "h_unstable",
                "status": "unstable",
                "evolution_phase": "regressing",
                "phase_strength": "medium",
                "trajectory_signal": "continuing_regression",
                "action_mode": "reroute_for_stronger_evidence",
                "suppressed_by": "weaker_phase_strength",
                "frontier_age": "new",
                "frontier_trend": "rising",
            },
        ],
        "hypothesis_active_alternative_context": {
            "hypothesis_id": "h_unstable",
            "status": "unstable",
            "evolution_phase": "regressing",
            "phase_strength": "medium",
            "trajectory_signal": "continuing_regression",
            "action_mode": "reroute_for_stronger_evidence",
            "suppressed_by": "action_mode_misalignment",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
    }


def test_build_expansion_summary_surfaces_phase_aware_recommendation_context() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_accel",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_accel"],
            "stable_candidates": ["exp_stable"],
            "advancing_candidates": ["exp_accel"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_accel",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_accel",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": ["h_accel"],
            "stable_hypotheses": ["h_stable"],
            "advancing_hypotheses": ["h_accel"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_accel",
            "recommended_action": "promote_supported_hypothesis",
            "recommended_action_mode": "promote_emerging_anchor",
        },
    )

    assert summary["recommended_experiment_id"] == "exp_accel"
    assert summary["recommended_hypothesis_id"] == "h_accel"
    assert summary["next_expansion_action"] == "promote_high_confidence_anchor"
    assert summary["backlog_phase_signal"] == "accelerating"
    assert summary["hypothesis_phase_signal"] == "accelerating"
    assert summary["backlog_phase_strength_signal"] == "high"
    assert summary["hypothesis_phase_strength_signal"] == "medium"
    assert summary["recommended_backlog_action_mode"] == "scale_confident_anchor"
    assert summary["recommended_hypothesis_action_mode"] == "promote_emerging_anchor"
    assert summary["action_mode_alignment"] == "aligned"


def test_build_expansion_summary_surfaces_pending_promotion_actions() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_alt",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_alt"],
            "stable_candidates": ["exp_leader"],
            "advancing_candidates": ["exp_leader"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_alt",
            "recommended_action": "investigate_pending_candidate_promotion",
            "pending_promotion_candidate_id": "exp_alt",
            "pending_promotion_gate_blocker": "challenger_recent_rework",
            "pending_promotion_pressure_streak": 2,
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_alt",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": [],
            "stable_hypotheses": ["h_leader"],
            "advancing_hypotheses": ["h_leader"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": ["h_alt"],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_alt",
            "recommended_action": "investigate_pending_hypothesis_promotion",
            "pending_promotion_hypothesis_id": "h_alt",
            "pending_promotion_gate_blocker": "challenger_recent_rework",
            "pending_promotion_pressure_streak": 2,
        },
    )

    assert summary["next_expansion_action"] == "resolve_persistent_pending_promotion_pair"
    assert summary["status_headline"] == (
        "The campaign has a persistently blocked challenger pair and should resolve that stalled promotion path before broader expansion."
    )
    assert summary["recommended_backlog_action"] == "investigate_pending_candidate_promotion"
    assert summary["recommended_hypothesis_action"] == "investigate_pending_hypothesis_promotion"
    assert summary["pending_promotion_candidate_id"] == "exp_alt"
    assert summary["pending_promotion_hypothesis_id"] == "h_alt"
    assert summary["pending_promotion_gate_blockers"] == ["challenger_recent_rework"]
    assert summary["joint_pending_promotion_pair"] == {
        "experiment_id": "exp_alt",
        "hypothesis_id": "h_alt",
        "gate_blockers": ["challenger_recent_rework"],
        "pressure_streak": 2,
        "pending_state": "persistent",
    }


def test_build_expansion_summary_surfaces_promotion_ready_actions() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_alt",
            "recommended_anchor_hypothesis_links": ["h_alt"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_alt"],
            "stable_candidates": [],
            "advancing_candidates": ["exp_alt"],
            "regressing_candidates": ["exp_leader"],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_alt",
            "recommended_action": "promote_ready_candidate",
            "promotion_ready_candidate_id": "exp_alt",
            "promotion_ready_pressure_streak": 2,
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_alt",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": [],
            "stable_hypotheses": [],
            "advancing_hypotheses": ["h_alt"],
            "regressing_hypotheses": ["h_leader"],
            "recovery_hypotheses": ["h_alt"],
            "phase_strength_signal": "high",
            "recommended_hypothesis_id": "h_alt",
            "recommended_action": "promote_ready_hypothesis",
            "promotion_ready_hypothesis_id": "h_alt",
            "promotion_ready_pressure_streak": 2,
        },
    )

    assert summary["next_expansion_action"] == "advance_persistent_promotion_ready_pair"
    assert summary["status_headline"] == (
        "The campaign has a persistently gate-cleared challenger pair and should advance that promotion path before broader expansion."
    )
    assert summary["recommended_backlog_action"] == "promote_ready_candidate"
    assert summary["recommended_hypothesis_action"] == "promote_ready_hypothesis"
    assert summary["promotion_ready_candidate_id"] == "exp_alt"
    assert summary["promotion_ready_hypothesis_id"] == "h_alt"
    assert summary["joint_promotion_ready_pair"] == {
        "experiment_id": "exp_alt",
        "hypothesis_id": "h_alt",
        "pressure_streak": 2,
        "readiness_state": "persistent",
    }


def test_build_expansion_summary_surfaces_joint_recovery_pair_context() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_recover",
            "recommended_anchor_hypothesis_links": ["h_recover"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": [],
            "stable_candidates": [],
            "advancing_candidates": [],
            "regressing_candidates": ["exp_old"],
            "recovery_candidates": ["exp_recover"],
            "phase_strength_signal": "medium",
            "recommended_experiment_id": "exp_recover",
            "recommended_action": "recover_regressing_candidate",
            "recommended_action_mode": "reroute_for_stronger_evidence",
            "dominant_failure_mode": "scientific_validity",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_recover",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": [],
            "stable_hypotheses": [],
            "advancing_hypotheses": [],
            "regressing_hypotheses": ["h_old"],
            "recovery_hypotheses": ["h_recover"],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_recover",
            "recommended_action": "stabilize_regressing_hypothesis",
            "recommended_action_mode": "reroute_for_stronger_evidence",
            "dominant_failure_mode": "scientific_validity",
        },
    )

    assert summary["next_expansion_action"] == "stabilize_persistent_joint_recovery_pair"
    assert summary["status_headline"] == (
        "The campaign has a persistently aligned recovery pair and should stabilize that recovery path before broader expansion."
    )
    assert summary["joint_recovery_pair"] == {
        "experiment_id": "exp_recover",
        "hypothesis_id": "h_recover",
        "failure_mode": "scientific_validity",
        "recovery_state": "persistent",
        "recovery_streak": 2,
    }


def test_build_expansion_summary_surfaces_recommendation_drivers() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_accel",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_accel"],
            "stable_candidates": [],
            "advancing_candidates": ["exp_accel"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_accel",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
            "recommended_trajectory_signal": "strong_acceleration",
            "ranked_candidates": [
                {
                    "experiment_id": "exp_accel",
                    "score_band": "high",
                    "reason": "accelerating high-confidence anchor",
                    "action_mode": "scale_confident_anchor",
                    "score_signals": {
                        "status": "promising",
                        "phase": "accelerating",
                        "phase_strength": "high",
                        "trajectory_signal": "strong_acceleration",
                        "action_mode": "scale_confident_anchor",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "experiment_id": "exp_recovery",
                    "score_band": "medium",
                    "reason": "recovering medium-confidence anchor",
                    "action_mode": "stabilize_recovery",
                    "score_signals": {
                        "status": "mixed",
                        "phase": "recovering",
                        "phase_strength": "medium",
                        "trajectory_signal": "newly_recovering",
                        "action_mode": "stabilize_recovery",
                    },
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
            "recommendation_drivers": {
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
                "status": "promising",
            },
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_accel",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": ["h_accel"],
            "stable_hypotheses": [],
            "advancing_hypotheses": ["h_accel"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_accel",
            "recommended_action": "promote_supported_hypothesis",
            "recommended_action_mode": "promote_emerging_anchor",
            "recommended_trajectory_signal": "newly_accelerating",
            "ranked_hypotheses": [
                {
                    "hypothesis_id": "h_accel",
                    "score_band": "high",
                    "reason": "accelerating medium-confidence anchor",
                    "action_mode": "promote_emerging_anchor",
                    "score_signals": {
                        "status": "supported",
                        "phase": "accelerating",
                        "phase_strength": "medium",
                        "trajectory_signal": "newly_accelerating",
                        "action_mode": "promote_emerging_anchor",
                    },
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "hypothesis_id": "h_shadow",
                    "score_band": "low",
                    "reason": "stable low-confidence anchor",
                    "action_mode": "validate_low_confidence_anchor",
                    "score_signals": {
                        "status": "unknown",
                        "phase": "stable",
                        "phase_strength": "low",
                        "trajectory_signal": "stale_stable",
                        "action_mode": "validate_low_confidence_anchor",
                    },
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
            "recommendation_drivers": {
                "phase": "accelerating",
                "phase_strength": "medium",
                "trajectory_signal": "newly_accelerating",
                "action_mode": "promote_emerging_anchor",
                "status": "supported",
            },
        },
    )

    assert summary["backlog_recommendation_drivers"] == {
        "phase": "accelerating",
        "phase_strength": "high",
        "trajectory_signal": "strong_acceleration",
        "action_mode": "scale_confident_anchor",
        "status": "promising",
    }
    assert summary["hypothesis_recommendation_drivers"] == {
        "phase": "accelerating",
        "phase_strength": "medium",
        "trajectory_signal": "newly_accelerating",
        "action_mode": "promote_emerging_anchor",
        "status": "supported",
    }
    assert summary["backlog_ranked_alternatives"] == [
        {
            "experiment_id": "exp_accel",
            "score_band": "high",
            "reason": "accelerating high-confidence anchor",
            "action_mode": "scale_confident_anchor",
            "score_signals": {
                "status": "promising",
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
            },
            "suppressed_by": None,
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "experiment_id": "exp_recovery",
            "score_band": "medium",
            "reason": "recovering medium-confidence anchor",
            "action_mode": "stabilize_recovery",
            "score_signals": {
                "status": "mixed",
                "phase": "recovering",
                "phase_strength": "medium",
                "trajectory_signal": "newly_recovering",
                "action_mode": "stabilize_recovery",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
    ]
    assert summary["backlog_alternative_context"] == {
        "experiment_id": "exp_recovery",
        "score_band": "medium",
        "reason": "recovering medium-confidence anchor",
        "action_mode": "stabilize_recovery",
        "score_signals": {
            "status": "mixed",
            "phase": "recovering",
            "phase_strength": "medium",
            "trajectory_signal": "newly_recovering",
            "action_mode": "stabilize_recovery",
        },
        "suppressed_by": "weaker_phase_strength",
        "frontier_age": "new",
        "frontier_trend": "rising",
        "alternative_state_hint": "mixed / recovering / medium / newly_recovering reserve anchor",
    }
    assert summary["hypothesis_ranked_alternatives"] == [
        {
            "hypothesis_id": "h_accel",
            "score_band": "high",
            "reason": "accelerating medium-confidence anchor",
            "action_mode": "promote_emerging_anchor",
            "score_signals": {
                "status": "supported",
                "phase": "accelerating",
                "phase_strength": "medium",
                "trajectory_signal": "newly_accelerating",
                "action_mode": "promote_emerging_anchor",
            },
            "suppressed_by": None,
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "hypothesis_id": "h_shadow",
            "score_band": "low",
            "reason": "stable low-confidence anchor",
            "action_mode": "validate_low_confidence_anchor",
            "score_signals": {
                "status": "unknown",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
    ]
    assert summary["hypothesis_alternative_context"] == {
        "hypothesis_id": "h_shadow",
        "score_band": "low",
        "reason": "stable low-confidence anchor",
        "action_mode": "validate_low_confidence_anchor",
        "score_signals": {
            "status": "unknown",
            "phase": "stable",
            "phase_strength": "low",
            "trajectory_signal": "stale_stable",
            "action_mode": "validate_low_confidence_anchor",
        },
        "suppressed_by": "weaker_phase_strength",
        "frontier_age": "new",
        "frontier_trend": "rising",
        "alternative_state_hint": "unknown / stable / low / stale_stable reserve hypothesis anchor",
    }


def test_build_evolution_summaries_surface_ranked_alternatives() -> None:
    backlog_summary = campaign_state.build_backlog_evolution_summary(
        {
            "selection_ready": True,
            "tracked_candidates": [
                {
                    "experiment_id": "exp_primary",
                    "status": "promising",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
                {
                    "experiment_id": "exp_recovery",
                    "status": "mixed",
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "stabilize_recovery",
                },
                {
                    "experiment_id": "exp_blocked",
                    "status": "blocked",
                    "evolution_phase": "regressing",
                    "phase_strength": "high",
                    "trajectory_signal": "deep_regression",
                    "action_mode": "reroute_for_stronger_evidence",
                },
            ],
        }
    )
    hypothesis_summary = campaign_state.build_hypothesis_evolution_summary(
        {
            "selection_ready": True,
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_primary",
                    "status": "supported",
                    "evolution_phase": "accelerating",
                    "phase_strength": "high",
                    "trajectory_signal": "strong_acceleration",
                    "action_mode": "scale_confident_anchor",
                },
                {
                    "hypothesis_id": "h_watch",
                    "status": "mixed",
                    "evolution_phase": "recovering",
                    "phase_strength": "medium",
                    "trajectory_signal": "newly_recovering",
                    "action_mode": "stabilize_recovery",
                },
                {
                    "hypothesis_id": "h_weak",
                    "status": "unstable",
                    "evolution_phase": "regressing",
                    "phase_strength": "high",
                    "trajectory_signal": "deep_regression",
                    "action_mode": "reroute_for_stronger_evidence",
                },
            ],
        }
    )

    assert backlog_summary["ranked_candidates"] == [
        {
            "experiment_id": "exp_primary",
            "score_band": "high",
            "reason": "accelerating high-confidence anchor",
            "action_mode": "scale_confident_anchor",
            "score_signals": {
                "status": "promising",
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
            },
            "suppressed_by": None,
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "experiment_id": "exp_recovery",
            "score_band": "medium",
            "reason": "recovering medium-confidence anchor",
            "action_mode": "stabilize_recovery",
            "score_signals": {
                "status": "mixed",
                "phase": "recovering",
                "phase_strength": "medium",
                "trajectory_signal": "newly_recovering",
                "action_mode": "stabilize_recovery",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "experiment_id": "exp_blocked",
            "score_band": "low",
            "reason": "regressing high-confidence anchor",
            "action_mode": "reroute_for_stronger_evidence",
            "score_signals": {
                "status": "blocked",
                "phase": "regressing",
                "phase_strength": "high",
                "trajectory_signal": "deep_regression",
                "action_mode": "reroute_for_stronger_evidence",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
    ]
    assert hypothesis_summary["ranked_hypotheses"] == [
        {
            "hypothesis_id": "h_primary",
            "score_band": "high",
            "reason": "accelerating high-confidence anchor",
            "action_mode": "scale_confident_anchor",
            "score_signals": {
                "status": "supported",
                "phase": "accelerating",
                "phase_strength": "high",
                "trajectory_signal": "strong_acceleration",
                "action_mode": "scale_confident_anchor",
            },
            "suppressed_by": None,
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "hypothesis_id": "h_watch",
            "score_band": "medium",
            "reason": "recovering medium-confidence anchor",
            "action_mode": "stabilize_recovery",
            "score_signals": {
                "status": "mixed",
                "phase": "recovering",
                "phase_strength": "medium",
                "trajectory_signal": "newly_recovering",
                "action_mode": "stabilize_recovery",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
        {
            "hypothesis_id": "h_weak",
            "score_band": "low",
            "reason": "regressing high-confidence anchor",
            "action_mode": "reroute_for_stronger_evidence",
            "score_signals": {
                "status": "unstable",
                "phase": "regressing",
                "phase_strength": "high",
                "trajectory_signal": "deep_regression",
                "action_mode": "reroute_for_stronger_evidence",
            },
            "suppressed_by": "weaker_phase_strength",
            "frontier_age": "new",
            "frontier_trend": "rising",
        },
    ]


def test_build_expansion_summary_uses_low_confidence_validation_for_weak_accelerating_anchor() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_probe",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_probe"],
            "stable_candidates": [],
            "advancing_candidates": ["exp_probe"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "low",
            "recommended_experiment_id": "exp_probe",
            "recommended_action": "promote_promising_candidate",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_probe",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": ["h_probe"],
            "stable_hypotheses": [],
            "advancing_hypotheses": ["h_probe"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "phase_strength_signal": "low",
            "recommended_hypothesis_id": "h_probe",
            "recommended_action": "promote_supported_hypothesis",
        },
    )

    assert summary["next_expansion_action"] == "validate_low_confidence_anchor"
    assert "low-confidence" in summary["status_headline"]


def test_build_expansion_summary_reconciles_divergent_action_modes() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_growth",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_growth"],
            "stable_candidates": [],
            "advancing_candidates": ["exp_growth"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_growth",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_recovery",
            "unstable_hypotheses": [],
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": [],
            "stable_hypotheses": [],
            "advancing_hypotheses": [],
            "regressing_hypotheses": [],
            "recovery_hypotheses": ["h_recovery"],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_recovery",
            "recommended_action": "stabilize_recovering_hypothesis",
            "recommended_action_mode": "recover_missing_artifacts",
        },
    )

    assert summary["action_mode_alignment"] == "divergent"
    assert summary["next_expansion_action"] == "reconcile_anchor_signals"


def test_build_expansion_summary_persists_action_mode_divergence_memory() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_growth",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "accelerating_candidates": ["exp_growth"],
            "stable_candidates": [],
            "advancing_candidates": ["exp_growth"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "phase_strength_signal": "high",
            "recommended_experiment_id": "exp_growth",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_recovery",
            "unstable_hypotheses": [],
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "accelerating_hypotheses": [],
            "stable_hypotheses": [],
            "advancing_hypotheses": [],
            "regressing_hypotheses": [],
            "recovery_hypotheses": ["h_recovery"],
            "phase_strength_signal": "medium",
            "recommended_hypothesis_id": "h_recovery",
            "recommended_action": "stabilize_recovering_hypothesis",
            "recommended_action_mode": "recover_missing_artifacts",
        },
        previous_summary={
            "action_mode_alignment": "divergent",
            "action_mode_divergence_memory": {
                "backlog_action_mode": "scale_confident_anchor",
                "hypothesis_action_mode": "recover_missing_artifacts",
                "divergence_streak": 1,
                "divergence_state": "new",
            },
        },
    )

    assert summary["action_mode_alignment"] == "divergent"
    assert summary["next_expansion_action"] == "resolve_persistent_action_mode_divergence"
    assert summary["action_mode_divergence_memory"] == {
        "backlog_action_mode": "scale_confident_anchor",
        "hypothesis_action_mode": "recover_missing_artifacts",
        "divergence_streak": 2,
        "divergence_state": "persistent",
    }


def test_build_backlog_summary_surfaces_recommended_anchor_hypothesis_links() -> None:
    summary = campaign_state.build_backlog_summary(
        {
            "selection_ready": True,
            "active_candidate": {
                "experiment_id": "exp_primary",
                "objective": "Primary objective",
                "hypothesis_links": ["h_primary"],
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_primary",
                    "objective": "Primary objective",
                    "hypothesis_links": ["h_primary"],
                    "status": "promising",
                },
                {
                    "experiment_id": "exp_alt",
                    "objective": "Alternative objective",
                    "hypothesis_links": ["h_alt"],
                    "status": "unproven",
                },
            ],
        }
    )

    assert summary["recommended_anchor_experiment_id"] == "exp_primary"
    assert summary["recommended_anchor_hypothesis_links"] == ["h_primary"]


def test_build_backlog_summary_prefers_active_promising_anchor_as_recommended() -> None:
    summary = campaign_state.build_backlog_summary(
        {
            "selection_ready": True,
            "active_candidate": {
                "experiment_id": "exp_coherent",
                "objective": "Coherent objective",
                "hypothesis_links": ["h_match"],
            },
            "tracked_candidates": [
                {
                    "experiment_id": "exp_mismatch",
                    "objective": "Mismatch objective",
                    "hypothesis_links": ["h_other"],
                    "status": "promising",
                },
                {
                    "experiment_id": "exp_coherent",
                    "objective": "Coherent objective",
                    "hypothesis_links": ["h_match"],
                    "status": "promising",
                },
            ],
        }
    )

    assert summary["active_experiment_id"] == "exp_coherent"
    assert summary["recommended_anchor_experiment_id"] == "exp_coherent"
    assert summary["recommended_anchor_hypothesis_links"] == ["h_match"]


def test_build_expansion_summary_reconciles_divergent_anchor_coherence() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_primary",
            "recommended_anchor_hypothesis_links": ["h_primary"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "recommended_experiment_id": "exp_primary",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "validate_low_confidence_anchor",
            "advancing_candidates": ["exp_primary"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "accelerating_candidates": [],
            "stable_candidates": ["exp_primary"],
            "phase_strength_signal": "low",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
            "recommended_action": "promote_supported_hypothesis",
            "recommended_action_mode": "validate_low_confidence_anchor",
            "advancing_hypotheses": ["h_other"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "accelerating_hypotheses": [],
            "stable_hypotheses": ["h_other"],
            "phase_strength_signal": "low",
        },
    )

    assert summary["action_mode_alignment"] == "aligned"
    assert summary["anchor_coherence"] == "divergent"
    assert summary["recommended_experiment_id"] == "exp_primary"
    assert summary["recommended_hypothesis_id"] == "h_other"
    assert summary["next_expansion_action"] == "reconcile_anchor_signals"
    assert summary["anchor_coherence_expected_hypothesis_ids"] == ["h_primary"]
    assert summary["anchor_coherence_selected_hypothesis_id"] == "h_other"
    assert "recommended backlog anchor and hypothesis anchor should be reconciled" in summary["status_headline"]
    assert "reconcile" in summary["status_headline"].lower()
    assert summary["recommended_backlog_action_mode"] == "validate_low_confidence_anchor"
    assert summary["recommended_hypothesis_action_mode"] == "validate_low_confidence_anchor"


def test_build_expansion_summary_persists_anchor_divergence_memory() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_primary",
            "recommended_anchor_hypothesis_links": ["h_primary"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "recommended_experiment_id": "exp_primary",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "validate_low_confidence_anchor",
            "advancing_candidates": ["exp_primary"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "accelerating_candidates": [],
            "stable_candidates": ["exp_primary"],
            "phase_strength_signal": "low",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
            "recommended_action": "promote_supported_hypothesis",
            "recommended_action_mode": "validate_low_confidence_anchor",
            "advancing_hypotheses": ["h_other"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "accelerating_hypotheses": [],
            "stable_hypotheses": ["h_other"],
            "phase_strength_signal": "low",
        },
        previous_summary={
            "next_expansion_action": "reconcile_anchor_signals",
            "anchor_coherence": "divergent",
            "anchor_coherence_expected_hypothesis_ids": ["h_primary"],
            "anchor_coherence_selected_hypothesis_id": "h_other",
            "anchor_divergence_memory": {
                "expected_hypothesis_ids": ["h_primary"],
                "selected_hypothesis_id": "h_other",
                "divergence_streak": 1,
                "divergence_state": "new",
            },
        },
    )

    assert summary["anchor_coherence"] == "divergent"
    assert summary["next_expansion_action"] == "resolve_persistent_anchor_divergence"
    assert summary["anchor_divergence_memory"] == {
        "expected_hypothesis_ids": ["h_primary"],
        "selected_hypothesis_id": "h_other",
        "divergence_streak": 2,
        "divergence_state": "persistent",
    }


def test_build_expansion_summary_promotes_persistent_coordination_divergence() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_primary",
            "recommended_anchor_hypothesis_links": ["h_primary"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "recommended_experiment_id": "exp_primary",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
            "advancing_candidates": ["exp_primary"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "accelerating_candidates": ["exp_primary"],
            "stable_candidates": [],
            "phase_strength_signal": "high",
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_other",
            "recommended_action": "stabilize_recovering_hypothesis",
            "recommended_action_mode": "recover_missing_artifacts",
            "advancing_hypotheses": [],
            "regressing_hypotheses": [],
            "recovery_hypotheses": ["h_other"],
            "accelerating_hypotheses": [],
            "stable_hypotheses": [],
            "phase_strength_signal": "medium",
        },
        previous_summary={
            "next_expansion_action": "reconcile_anchor_signals",
            "anchor_coherence": "divergent",
            "anchor_coherence_expected_hypothesis_ids": ["h_primary"],
            "anchor_coherence_selected_hypothesis_id": "h_other",
            "anchor_divergence_memory": {
                "expected_hypothesis_ids": ["h_primary"],
                "selected_hypothesis_id": "h_other",
                "divergence_streak": 1,
                "divergence_state": "new",
            },
            "action_mode_alignment": "divergent",
            "action_mode_divergence_memory": {
                "backlog_action_mode": "scale_confident_anchor",
                "hypothesis_action_mode": "recover_missing_artifacts",
                "divergence_streak": 1,
                "divergence_state": "new",
            },
        },
    )

    assert summary["next_expansion_action"] == "resolve_persistent_coordination_divergence"
    assert summary["persistent_coordination_divergence"] == {
        "expected_hypothesis_ids": ["h_primary"],
        "selected_hypothesis_id": "h_other",
        "backlog_action_mode": "scale_confident_anchor",
        "hypothesis_action_mode": "recover_missing_artifacts",
        "divergence_streak": 2,
        "divergence_state": "persistent",
    }


def test_build_expansion_summary_promotes_persistent_joint_reserve_memory() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "recommended_anchor_experiment_id": "exp_primary",
            "recommended_anchor_hypothesis_links": ["h_reserve"],
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "recommended_experiment_id": "exp_primary",
            "recommended_action": "promote_promising_candidate",
            "recommended_action_mode": "scale_confident_anchor",
            "advancing_candidates": ["exp_primary"],
            "regressing_candidates": [],
            "recovery_candidates": [],
            "accelerating_candidates": ["exp_primary"],
            "stable_candidates": [],
            "phase_strength_signal": "high",
            "ranked_candidates": [
                {
                    "experiment_id": "exp_primary",
                    "score_band": "high",
                    "reason": "accelerating high-confidence anchor",
                    "action_mode": "scale_confident_anchor",
                },
                {
                    "experiment_id": "exp_reserve",
                    "score_band": "medium",
                    "reason": "recovering reserve anchor",
                    "action_mode": "promote_emerging_anchor",
                    "suppressed_by": "stale_trajectory",
                    "frontier_age": "persistent",
                    "frontier_trend": "rising",
                    "hypothesis_links": ["h_reserve"],
                },
            ],
        },
        hypothesis_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_primary",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "recommended_hypothesis_id": "h_primary",
            "recommended_action": "promote_supported_hypothesis",
            "recommended_action_mode": "promote_emerging_anchor",
            "advancing_hypotheses": ["h_primary"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "accelerating_hypotheses": ["h_primary"],
            "stable_hypotheses": [],
            "phase_strength_signal": "medium",
            "ranked_hypotheses": [
                {
                    "hypothesis_id": "h_primary",
                    "score_band": "high",
                    "reason": "accelerating primary hypothesis",
                    "action_mode": "promote_emerging_anchor",
                },
                {
                    "hypothesis_id": "h_reserve",
                    "score_band": "medium",
                    "reason": "recovering reserve hypothesis",
                    "action_mode": "promote_emerging_anchor",
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "persistent",
                    "frontier_trend": "rising",
                },
            ],
        },
    )

    assert summary["next_expansion_action"] == "resolve_persistent_joint_reserve_memory"
    assert summary["persistent_joint_reserve_memory"] == {
        "experiment_id": "exp_reserve",
        "hypothesis_id": "h_reserve",
        "backlog_frontier_age": "persistent",
        "backlog_frontier_trend": "rising",
        "backlog_suppressed_by": "stale_trajectory",
        "hypothesis_frontier_age": "persistent",
        "hypothesis_frontier_trend": "rising",
        "hypothesis_suppressed_by": "weaker_phase_strength",
        "reserve_state": "persistent",
    }


def test_build_expansion_summary_specializes_actions_for_dominant_failure_modes() -> None:
    summary = campaign_state.build_expansion_summary(
        backlog_summary={
            "selection_ready": True,
            "blocked_candidates": ["exp_blocked"],
            "recommended_anchor_experiment_id": "exp_healthier",
        },
        backlog_evolution_summary={
            "selection_ready": True,
            "advancing_candidates": [],
            "regressing_candidates": ["exp_blocked"],
            "recovery_candidates": [],
            "recommended_experiment_id": "exp_healthier",
            "recommended_action": "recover_regressing_candidate",
            "dominant_failure_mode": "scientific_validity",
            "status_headline": "Blocked due to scientific_validity failures.",
        },
        hypothesis_summary={
            "selection_ready": True,
            "unstable_hypotheses": [],
            "recommended_hypothesis_id": "h_supported",
        },
        hypothesis_evolution_summary={
            "selection_ready": True,
            "advancing_hypotheses": ["h_supported"],
            "regressing_hypotheses": [],
            "recovery_hypotheses": [],
            "recommended_hypothesis_id": "h_supported",
            "recommended_action": "promote_supported_hypothesis",
            "dominant_failure_mode": None,
            "status_headline": "A supported hypothesis is advancing and ready to promote.",
        },
    )

    assert summary == {
        "expansion_ready": True,
        "recommended_experiment_id": "exp_healthier",
        "recommended_hypothesis_id": "h_supported",
        "risk_flags": [
            "blocked_backlog_candidates",
            "blocked_backlog_candidates:scientific_validity",
        ],
        "next_expansion_action": "unblock_backlog_candidates_scientific_validity",
        "status_headline": "The campaign has reusable anchors, but blocked backlog candidates still need stronger scientific validity.",
        "recommended_backlog_action": "recover_regressing_candidate",
        "recommended_hypothesis_action": "promote_supported_hypothesis",
        "backlog_phase_signal": "regressing",
        "backlog_dominant_failure_mode": "scientific_validity",
    }


def test_build_status_snapshot_surfaces_campaign_and_expansion_state() -> None:
    snapshot = campaign_state.build_status_snapshot(
        campaign_dir="/tmp/demo",
        state={
            "campaign_id": "demo",
            "iterations_run": 2,
            "campaign_lifecycle": "in_progress",
            "campaign_summary": {
                "research_question": "Does X help Y?",
                "status_headline": "The campaign has completed 2 rounds for the current research question.",
                "latest_outcome": "accepted",
                "next_step": "Continue execution from the current objective or successful outputs.",
                "latest_failed_check_types": [],
                "blocking_issue": None,
                "resume_ready": True,
                "resume_reasons": [],
            },
            "expansion_summary": {
                "expansion_ready": True,
                "recommended_experiment_id": "exp_best",
                "recommended_hypothesis_id": "h_exp_best",
                "risk_flags": [],
                "next_expansion_action": "promote_recommended_anchor",
                "status_headline": "The campaign has a promising backlog anchor and a supported hypothesis anchor.",
                "recommended_hypothesis_action": "promote_supported_hypothesis",
            },
            "backlog_summary": {
                "selection_ready": True,
                "active_experiment_id": "exp_best",
                "active_objective": "Analyze the strongest candidate.",
                "promising_candidates": ["exp_best"],
                "blocked_candidates": ["exp_blocked"],
                "unproven_candidates": [],
                "recommended_anchor_experiment_id": "exp_best",
                "recommended_anchor_status": "promising",
            },
            "hypothesis_summary": {
                "selection_ready": True,
                "active_hypotheses": ["h_exp_best"],
                "supported_hypotheses": ["h_exp_best"],
                "unstable_hypotheses": [],
                "mixed_hypotheses": [],
                "unknown_hypotheses": [],
                "recommended_hypothesis_id": "h_exp_best",
                "recommended_hypothesis_status": "supported",
            },
            "memory_summary": {
                "preferred_artifact": "result_note.md",
                "evidence_summary": "The latest accepted round found a positive directional effect.",
                "accepted_memory_ready": True,
            },
            "continuation_anchor": {
                "anchor_artifact": "result_note.md",
                "anchor_objective": "Analyze the strongest candidate.",
                "anchor_summary": "The latest accepted round found a positive directional effect.",
                "anchor_ready": True,
            },
            "resume_assessment": {
                "resume_ready": True,
                "reasons": [],
            },
        },
        latest_iteration={
            "iteration": 2,
            "objective": "Analyze the strongest accepted result.",
            "decision": "CONTINUE",
            "task_results": [
                {
                    "task_id": "task_exp_cli_001_review",
                    "deliverable_paths": [],
                },
                {
                    "task_id": "task_exp_cli_001_impl",
                    "deliverable_paths": ["metrics.json", "result_note.md"],
                },
            ],
            "worker_result": {
                "task_id": "task_exp_cli_001_impl",
                "worker_id": "claude_code",
                "status": "success",
                "deliverable_paths": ["metrics.json", "result_note.md"],
                "summary": "Synthesized the strongest accepted result into metrics and a research note.",
            },
            "artifacts": {
                "deliverable_paths": ["metrics.json", "result_note.md"],
            },
            "verification": {
                "status": "accept",
                "failed_check_types": [],
                "rework_priority": "none",
            },
            "task_intent": {
                "task_type": "analysis",
                "worker_requirements": "any",
                "acceptance_emphasis": "scientific_validity",
            },
            "brain_plan": {
                "strategy": "continue",
                "next_objective": "Analyze the strongest accepted result.",
                "reason": "Continue from the strongest accepted result.",
                "focus_areas": ["analysis"],
            },
            "governance": {
                "decision": "CONTINUE",
                "reason": "Verification accepted the latest round, so the campaign can continue.",
                "basis": {
                    "verification_status": "accept",
                    "rework_priority": "none",
                    "failure_streak": 0,
                    "experiments_run": 2,
                },
            },
            "round_summary": {
                "decision": "CONTINUE",
                "task_type": "analysis",
                "acceptance_emphasis": "scientific_validity",
                "verification_status": "accept",
                "next_action_reason": "Continue from the strongest accepted result.",
            },
            "operator_summary": {
                "headline": "Review the previous successful output through an analysis step.",
                "outcome": "accepted",
                "why": "The round satisfied its verification checks.",
                "next_step": "Continue execution from the current objective or successful outputs.",
            },
        },
    )

    assert snapshot == {
        "service": "autonomous_research_campaign",
        "status": "ready",
        "campaign_dir": "/tmp/demo",
        "campaign_id": "demo",
        "iterations_run": 2,
        "campaign_lifecycle": "in_progress",
        "campaign_summary": {
            "research_question": "Does X help Y?",
            "status_headline": "The campaign has completed 2 rounds for the current research question.",
            "latest_outcome": "accepted",
            "next_step": "Continue execution from the current objective or successful outputs.",
            "latest_failed_check_types": [],
            "blocking_issue": None,
            "resume_ready": True,
            "resume_reasons": [],
        },
        "expansion_summary": {
            "expansion_ready": True,
            "recommended_experiment_id": "exp_best",
            "recommended_hypothesis_id": "h_exp_best",
            "risk_flags": [],
            "next_expansion_action": "promote_recommended_anchor",
            "status_headline": "The campaign has a promising backlog anchor and a supported hypothesis anchor.",
            "recommended_hypothesis_action": "promote_supported_hypothesis",
        },
        "backlog_summary": {
            "selection_ready": True,
            "active_experiment_id": "exp_best",
            "active_objective": "Analyze the strongest candidate.",
            "promising_candidates": ["exp_best"],
            "blocked_candidates": ["exp_blocked"],
            "unproven_candidates": [],
            "recommended_anchor_experiment_id": "exp_best",
            "recommended_anchor_status": "promising",
        },
        "backlog_evolution_summary": None,
        "hypothesis_summary": {
            "selection_ready": True,
            "active_hypotheses": ["h_exp_best"],
            "supported_hypotheses": ["h_exp_best"],
            "unstable_hypotheses": [],
            "mixed_hypotheses": [],
            "unknown_hypotheses": [],
            "recommended_hypothesis_id": "h_exp_best",
            "recommended_hypothesis_status": "supported",
        },
        "hypothesis_evolution_summary": None,
        "memory_summary": {
            "preferred_artifact": "result_note.md",
            "evidence_summary": "The latest accepted round found a positive directional effect.",
            "accepted_memory_ready": True,
        },
        "continuation_anchor": {
            "anchor_artifact": "result_note.md",
            "anchor_objective": "Analyze the strongest candidate.",
            "anchor_summary": "The latest accepted round found a positive directional effect.",
            "anchor_ready": True,
        },
        "resume_assessment": {
            "resume_ready": True,
            "reasons": [],
        },
        "latest_round": {
            "iteration": 2,
            "objective": "Analyze the strongest accepted result.",
            "decision": "CONTINUE",
            "task_results": [
                {
                    "task_id": "task_exp_cli_001_review",
                    "deliverable_paths": [],
                },
                {
                    "task_id": "task_exp_cli_001_impl",
                    "deliverable_paths": ["metrics.json", "result_note.md"],
                },
            ],
            "worker_result": {
                "task_id": "task_exp_cli_001_impl",
                "worker_id": "claude_code",
                "status": "success",
                "deliverable_paths": ["metrics.json", "result_note.md"],
                "summary": "Synthesized the strongest accepted result into metrics and a research note.",
            },
            "artifacts": {
                "deliverable_paths": ["metrics.json", "result_note.md"],
            },
            "verification": {
                "status": "accept",
                "failed_check_types": [],
                "rework_priority": "none",
            },
            "task_intent": {
                "task_type": "analysis",
                "worker_requirements": "any",
                "acceptance_emphasis": "scientific_validity",
            },
            "brain_plan": {
                "strategy": "continue",
                "next_objective": "Analyze the strongest accepted result.",
                "reason": "Continue from the strongest accepted result.",
                "focus_areas": ["analysis"],
            },
            "governance": {
                "decision": "CONTINUE",
                "reason": "Verification accepted the latest round, so the campaign can continue.",
                "basis": {
                    "verification_status": "accept",
                    "rework_priority": "none",
                    "failure_streak": 0,
                    "experiments_run": 2,
                },
            },
            "round_summary": {
                "decision": "CONTINUE",
                "task_type": "analysis",
                "acceptance_emphasis": "scientific_validity",
                "verification_status": "accept",
                "next_action_reason": "Continue from the strongest accepted result.",
            },
            "operator_summary": {
                "headline": "Review the previous successful output through an analysis step.",
                "outcome": "accepted",
                "why": "The round satisfied its verification checks.",
                "next_step": "Continue execution from the current objective or successful outputs.",
            },
        },
    }


def test_build_status_snapshot_preserves_pending_promotion_expansion_guidance() -> None:
    snapshot = campaign_state.build_status_snapshot(
        campaign_dir="/tmp/demo",
        state={
            "campaign_id": "demo",
            "iterations_run": 3,
            "campaign_lifecycle": "in_progress",
            "campaign_summary": {
                "research_question": "Does X help Y?",
                "status_headline": "The campaign has completed 3 rounds for the current research question.",
                "latest_outcome": "needs_refinement",
                "next_step": "Investigate why the rising challenger is still blocked.",
                "latest_failed_check_types": ["scientific_validity"],
                "blocking_issue": "scientific_validity",
                "resume_ready": True,
                "resume_reasons": [],
            },
            "expansion_summary": {
                "expansion_ready": True,
                "recommended_experiment_id": "exp_alt",
                "recommended_hypothesis_id": "h_alt",
                "risk_flags": [],
                "next_expansion_action": "investigate_pending_promotions",
                "status_headline": "The campaign has rising challenger anchors that remain blocked from promotion and should investigate those blockers before broader expansion.",
                "recommended_backlog_action": "investigate_pending_candidate_promotion",
                "recommended_hypothesis_action": "investigate_pending_hypothesis_promotion",
                "pending_promotion_candidate_id": "exp_alt",
                "pending_promotion_hypothesis_id": "h_alt",
                "pending_promotion_gate_blockers": ["challenger_recent_rework"],
            },
            "backlog_summary": {"selection_ready": True},
            "hypothesis_summary": {"selection_ready": True},
            "memory_summary": {"accepted_memory_ready": False},
            "continuation_anchor": {"anchor_ready": False},
            "resume_assessment": {
                "resume_ready": True,
                "reasons": [],
            },
        },
        latest_iteration=None,
    )

    assert snapshot["expansion_summary"]["next_expansion_action"] == "investigate_pending_promotions"
    assert snapshot["expansion_summary"]["recommended_backlog_action"] == "investigate_pending_candidate_promotion"
    assert snapshot["expansion_summary"]["recommended_hypothesis_action"] == "investigate_pending_hypothesis_promotion"
    assert snapshot["expansion_summary"]["pending_promotion_gate_blockers"] == ["challenger_recent_rework"]


def test_build_campaign_backlog_defaults_to_empty_state() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate=None,
        backlog_source=None,
        candidate_count=None,
    )

    assert backlog == {
        "source_type": None,
        "source_path": None,
        "candidate_count": 0,
        "active_candidate": None,
        "last_selection": None,
        "selection_history": [],
        "tracked_candidates": [],
        "selection_ready": False,
    }


def test_build_campaign_backlog_tracks_selected_candidate_and_source() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
    )

    assert backlog == {
        "source_type": "file",
        "source_path": "/tmp/demo/backlog.json",
        "candidate_count": 2,
        "active_candidate": {
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
        },
        "last_selection": {
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "selection_iteration": 0,
        },
        "selection_history": [
            {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "hypothesis_links": ["h_exp_best"],
                "selection_iteration": 0,
            }
        ],
        "frontier_history": [],
        "tracked_candidates": [
            {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "hypothesis_links": ["h_exp_best"],
                "expected_information_gain": None,
                "risk_reduction": None,
                "cost_score": None,
                "times_selected": 1,
                "last_selected_iteration": 0,
                "last_outcome": None,
                "history": [
                    {
                        "selection_iteration": 0,
                        "outcome": None,
                    }
                ],
                "accept_count": 0,
                "rework_count": 0,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 0,
                "status": "unproven",
                "evolution_phase": "unproven",
                "phase_strength": "low",
                "action_mode": "observe_insufficient_signal",
            }
        ],
        "selection_ready": True,
    }


def test_build_campaign_backlog_persists_selection_rationale() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "selection_rationale": {
                "source": "backlog_file",
                "selection_mode": "planner_scored",
                "used_linked_hypothesis_state": False,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "unproven",
                    "phase": "unproven",
                    "phase_strength": "low",
                    "action_mode": "observe_insufficient_signal",
                },
                "ranked_alternatives": [
                    {
                        "experiment_id": "exp_best",
                        "score_band": "high",
                        "reason": "stable high-confidence anchor",
                        "action_mode": "scale_confident_anchor",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    },
                    {
                        "experiment_id": "exp_alt",
                        "score_band": "medium",
                        "reason": "recovering medium-confidence anchor",
                        "action_mode": "promote_emerging_anchor",
                        "suppressed_by": "weaker_phase_strength",
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    },
                ],
            },
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
    )

    assert backlog["last_selection"] == {
        "experiment_id": "exp_best",
        "objective": "Selected backlog objective",
        "hypothesis_links": ["h_exp_best"],
        "selection_iteration": 0,
        "selection_rationale": {
            "source": "backlog_file",
            "selection_mode": "planner_scored",
            "used_linked_hypothesis_state": False,
            "used_expansion_recommendations": False,
            "score_signals": {
                "status": "unproven",
                "phase": "unproven",
                "phase_strength": "low",
                "action_mode": "observe_insufficient_signal",
            },
            "ranked_alternatives": [
                {
                    "experiment_id": "exp_best",
                    "score_band": "high",
                    "reason": "stable high-confidence anchor",
                    "action_mode": "scale_confident_anchor",
                    "suppressed_by": None,
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
                {
                    "experiment_id": "exp_alt",
                    "score_band": "medium",
                    "reason": "recovering medium-confidence anchor",
                    "action_mode": "promote_emerging_anchor",
                    "suppressed_by": "weaker_phase_strength",
                    "frontier_age": "new",
                    "frontier_trend": "rising",
                },
            ],
        },
    }
    assert backlog["selection_history"] == [
        {
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "selection_iteration": 0,
            "selection_rationale": {
                "source": "backlog_file",
                "selection_mode": "planner_scored",
                "used_linked_hypothesis_state": False,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "unproven",
                    "phase": "unproven",
                    "phase_strength": "low",
                    "action_mode": "observe_insufficient_signal",
                },
                "ranked_alternatives": [
                    {
                        "experiment_id": "exp_best",
                        "score_band": "high",
                        "reason": "stable high-confidence anchor",
                        "action_mode": "scale_confident_anchor",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    },
                    {
                        "experiment_id": "exp_alt",
                        "score_band": "medium",
                        "reason": "recovering medium-confidence anchor",
                        "action_mode": "promote_emerging_anchor",
                        "suppressed_by": "weaker_phase_strength",
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    },
                ],
            },
        }
    ]


def test_build_campaign_backlog_updates_frontier_trend_when_rank_changes() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "selection_history": [
                {
                    "experiment_id": "exp_best",
                    "selection_iteration": 1,
                    "selection_rationale": {
                        "ranked_alternatives": [
                            {"experiment_id": "exp_best"},
                            {"experiment_id": "exp_alt"},
                        ]
                    },
                }
            ]
        },
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "selection_rationale": {
                "ranked_alternatives": [
                    {"experiment_id": "exp_alt"},
                    {"experiment_id": "exp_best"},
                ]
            },
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
        iteration_number=2,
    )

    assert backlog["last_selection"]["selection_rationale"]["ranked_alternatives"] == [
        {
            "experiment_id": "exp_alt",
            "frontier_age": "persistent",
            "frontier_trend": "rising",
        },
        {
            "experiment_id": "exp_best",
            "frontier_age": "persistent",
            "frontier_trend": "slipping",
        },
    ]


def test_build_campaign_backlog_marks_frontier_trend_holding_when_rank_is_unchanged() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "selection_history": [
                {
                    "experiment_id": "exp_best",
                    "selection_iteration": 1,
                    "selection_rationale": {
                        "ranked_alternatives": [
                            {"experiment_id": "exp_best"},
                            {"experiment_id": "exp_alt"},
                        ]
                    },
                }
            ]
        },
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "selection_rationale": {
                "ranked_alternatives": [
                    {"experiment_id": "exp_best"},
                    {"experiment_id": "exp_alt"},
                ]
            },
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
        iteration_number=2,
    )

    assert backlog["last_selection"]["selection_rationale"]["ranked_alternatives"] == [
        {
            "experiment_id": "exp_best",
            "frontier_age": "persistent",
            "frontier_trend": "holding",
        },
        {
            "experiment_id": "exp_alt",
            "frontier_age": "persistent",
            "frontier_trend": "holding",
        },
    ]


def test_build_campaign_backlog_accumulates_selection_history_across_rounds() -> None:
    first = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
        iteration_number=1,
        verification={"status": "accept"},
    )

    second = campaign_state.build_campaign_backlog(
        previous_backlog=first,
        selected_candidate={
            "experiment_id": "exp_alt",
            "objective": "Alternative backlog objective",
            "hypothesis_links": ["h_exp_alt"],
            "expected_information_gain": 0.40,
            "risk_reduction": 0.30,
            "cost_score": 0.20,
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=2,
        verification={"status": "rework"},
    )

    assert second == {
        "source_type": "file",
        "source_path": "/tmp/demo/backlog.json",
        "candidate_count": 2,
        "active_candidate": {
            "experiment_id": "exp_alt",
            "objective": "Alternative backlog objective",
            "hypothesis_links": ["h_exp_alt"],
        },
        "last_selection": {
            "experiment_id": "exp_alt",
            "objective": "Alternative backlog objective",
            "hypothesis_links": ["h_exp_alt"],
            "selection_iteration": 2,
        },
        "selection_history": [
            {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "hypothesis_links": ["h_exp_best"],
                "selection_iteration": 1,
            },
            {
                "experiment_id": "exp_alt",
                "objective": "Alternative backlog objective",
                "hypothesis_links": ["h_exp_alt"],
                "selection_iteration": 2,
            },
        ],
        "frontier_history": [],
        "tracked_candidates": [
            {
                "experiment_id": "exp_alt",
                "objective": "Alternative backlog objective",
                "hypothesis_links": ["h_exp_alt"],
                "expected_information_gain": 0.40,
                "risk_reduction": 0.30,
                "cost_score": 0.20,
                "times_selected": 1,
                "last_selected_iteration": 2,
                "last_outcome": "rework",
                "history": [
                    {
                        "selection_iteration": 2,
                        "outcome": "rework",
                    }
                ],
                    "accept_count": 0,
                    "rework_count": 1,
                    "last_accept_iteration": None,
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "status": "blocked",
                    "evolution_phase": "regressing",
                    "phase_strength": "low",
                    "action_mode": "recover_regressing_anchor",
                },
                {
                "experiment_id": "exp_best",
                "objective": "Selected backlog objective",
                "hypothesis_links": ["h_exp_best"],
                "expected_information_gain": 0.80,
                "risk_reduction": 0.50,
                "cost_score": 0.20,
                "times_selected": 1,
                "last_selected_iteration": 1,
                "last_outcome": "accept",
                "history": [
                    {
                        "selection_iteration": 1,
                        "outcome": "accept",
                    }
                ],
                    "accept_count": 1,
                    "rework_count": 0,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "status": "promising",
                    "evolution_phase": "stable",
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                },
            ],
            "selection_ready": True,
    }


def test_build_campaign_backlog_updates_tracked_candidate_when_reselected() -> None:
    first = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=2,
        iteration_number=1,
        verification={"status": "accept"},
    )

    second = campaign_state.build_campaign_backlog(
        previous_backlog=first,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=3,
        verification={"status": "rework"},
    )

    assert second["tracked_candidates"] == [
        {
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
            "times_selected": 2,
            "last_selected_iteration": 3,
            "last_outcome": "rework",
            "history": [
                {
                    "selection_iteration": 1,
                    "outcome": "accept",
                },
                {
                    "selection_iteration": 3,
                    "outcome": "rework",
                },
            ],
            "accept_count": 1,
            "rework_count": 1,
            "last_accept_iteration": 1,
            "current_accept_streak": 0,
            "current_rework_streak": 1,
            "status": "mixed",
            "evolution_phase": "regressing",
            "phase_strength": "low",
            "action_mode": "recover_regressing_anchor",
        }
    ]


def test_build_campaign_hypotheses_defaults_to_empty_state() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=None,
        hypothesis_links=None,
        verification=None,
        iteration_number=0,
    )

    assert hypotheses == {
        "active_hypotheses": [],
        "last_selection": None,
        "selection_history": [],
        "frontier_history": [],
        "tracked_hypotheses": [],
        "selection_ready": False,
    }


def test_build_campaign_hypotheses_tracks_and_updates_selected_hypotheses() -> None:
    first = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=None,
        hypothesis_links=["h_exp_best"],
        verification={"status": "accept"},
        iteration_number=1,
    )

    second = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=first,
        hypothesis_links=["h_exp_best", "h_exp_alt"],
        verification={"status": "rework"},
        iteration_number=2,
    )

    assert first == {
        "active_hypotheses": ["h_exp_best"],
        "last_selection": {
            "hypothesis_links": ["h_exp_best"],
            "selection_iteration": 1,
            "selection_rationale": {
                "source": "backlog_candidate_links",
                "selection_mode": "selected_candidate_projection",
                "used_backlog_context": True,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "supported",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "ranked_active_hypotheses": [
                    {
                        "hypothesis_id": "h_exp_best",
                        "status": "supported",
                        "evolution_phase": "stable",
                        "phase_strength": "low",
                        "trajectory_signal": "stale_stable",
                        "action_mode": "validate_low_confidence_anchor",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    }
                ],
            },
        },
        "selection_history": [
            {
                "hypothesis_links": ["h_exp_best"],
                "selection_iteration": 1,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                    "score_signals": {
                        "status": "supported",
                        "phase": "stable",
                        "phase_strength": "low",
                        "trajectory_signal": "stale_stable",
                        "action_mode": "validate_low_confidence_anchor",
                    },
                    "ranked_active_hypotheses": [
                        {
                            "hypothesis_id": "h_exp_best",
                            "status": "supported",
                            "evolution_phase": "stable",
                            "phase_strength": "low",
                            "trajectory_signal": "stale_stable",
                            "action_mode": "validate_low_confidence_anchor",
                            "suppressed_by": None,
                            "frontier_age": "new",
                            "frontier_trend": "rising",
                        }
                    ],
                },
            }
        ],
        "frontier_history": [
            {
                "iteration": 1,
                "recommended_id": "h_exp_best",
                "ranked_ids": ["h_exp_best"],
                "movement_summary": "new_leader",
                "driver_snapshot": {
                    "status": "supported",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "pressure_snapshot": {
                    "leader_tenure": "new",
                    "challenger_pressure": "low",
                },
            }
        ],
        "tracked_hypotheses": [
            {
                "hypothesis_id": "h_exp_best",
                "times_selected": 1,
                "last_selected_iteration": 1,
                "last_outcome": "accept",
                "history": [
                    {
                        "selection_iteration": 1,
                        "outcome": "accept",
                    }
                ],
                "accept_count": 1,
                "rework_count": 0,
                "last_accept_iteration": 1,
                "current_accept_streak": 1,
                "current_rework_streak": 0,
                "status": "supported",
                "evolution_phase": "stable",
                "phase_strength": "low",
                "action_mode": "validate_low_confidence_anchor",
            }
        ],
        "selection_ready": True,
    }
    assert second == {
        "active_hypotheses": ["h_exp_best", "h_exp_alt"],
        "last_selection": {
            "hypothesis_links": ["h_exp_best", "h_exp_alt"],
            "selection_iteration": 2,
            "selection_rationale": {
                "source": "backlog_candidate_links",
                "selection_mode": "selected_candidate_projection",
                "used_backlog_context": True,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "low",
                    "trajectory_signal": "newly_regressing",
                    "action_mode": "recover_regressing_anchor",
                },
                "ranked_active_hypotheses": [
                    {
                        "hypothesis_id": "h_exp_alt",
                        "status": "unstable",
                        "evolution_phase": "regressing",
                        "phase_strength": "low",
                        "trajectory_signal": "newly_regressing",
                        "action_mode": "recover_regressing_anchor",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    },
                    {
                        "hypothesis_id": "h_exp_best",
                        "status": "mixed",
                        "evolution_phase": "regressing",
                        "phase_strength": "low",
                        "trajectory_signal": "newly_regressing",
                        "action_mode": "recover_regressing_anchor",
                        "suppressed_by": "stale_trajectory",
                        "frontier_age": "persistent",
                        "frontier_trend": "slipping",
                    },
                ],
            },
        },
        "selection_history": [
            {
                "hypothesis_links": ["h_exp_best"],
                "selection_iteration": 1,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                    "score_signals": {
                        "status": "supported",
                        "phase": "stable",
                        "phase_strength": "low",
                        "trajectory_signal": "stale_stable",
                        "action_mode": "validate_low_confidence_anchor",
                    },
                    "ranked_active_hypotheses": [
                        {
                            "hypothesis_id": "h_exp_best",
                            "status": "supported",
                            "evolution_phase": "stable",
                            "phase_strength": "low",
                            "trajectory_signal": "stale_stable",
                            "action_mode": "validate_low_confidence_anchor",
                            "suppressed_by": None,
                            "frontier_age": "new",
                            "frontier_trend": "rising",
                        }
                    ],
                },
            },
            {
                "hypothesis_links": ["h_exp_best", "h_exp_alt"],
                "selection_iteration": 2,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "low",
                        "trajectory_signal": "newly_regressing",
                        "action_mode": "recover_regressing_anchor",
                    },
                    "ranked_active_hypotheses": [
                        {
                            "hypothesis_id": "h_exp_alt",
                            "status": "unstable",
                            "evolution_phase": "regressing",
                            "phase_strength": "low",
                            "trajectory_signal": "newly_regressing",
                            "action_mode": "recover_regressing_anchor",
                            "suppressed_by": None,
                            "frontier_age": "new",
                            "frontier_trend": "rising",
                        },
                        {
                            "hypothesis_id": "h_exp_best",
                            "status": "mixed",
                            "evolution_phase": "regressing",
                            "phase_strength": "low",
                            "trajectory_signal": "newly_regressing",
                            "action_mode": "recover_regressing_anchor",
                            "suppressed_by": "stale_trajectory",
                            "frontier_age": "persistent",
                            "frontier_trend": "slipping",
                        },
                    ],
                },
            },
        ],
        "frontier_history": [
            {
                "iteration": 1,
                "recommended_id": "h_exp_best",
                "ranked_ids": ["h_exp_best"],
                "movement_summary": "new_leader",
                "driver_snapshot": {
                    "status": "supported",
                    "phase": "stable",
                    "phase_strength": "low",
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                },
                "pressure_snapshot": {
                    "leader_tenure": "new",
                    "challenger_pressure": "low",
                },
            },
            {
                "iteration": 2,
                "recommended_id": "h_exp_alt",
                "ranked_ids": ["h_exp_alt", "h_exp_best"],
                "movement_summary": "leader_replaced",
                "driver_snapshot": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "low",
                    "trajectory_signal": "newly_regressing",
                    "action_mode": "recover_regressing_anchor",
                },
                "pressure_snapshot": {
                    "leader_tenure": "new",
                    "challenger_pressure": "low",
                },
            },
        ],
        "tracked_hypotheses": [
            {
                "hypothesis_id": "h_exp_alt",
                "times_selected": 1,
                "last_selected_iteration": 2,
                "last_outcome": "rework",
                "history": [
                    {
                        "selection_iteration": 2,
                        "outcome": "rework",
                    }
                ],
                "accept_count": 0,
                "rework_count": 1,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 1,
                "status": "unstable",
                "evolution_phase": "regressing",
                "phase_strength": "low",
                "action_mode": "recover_regressing_anchor",
            },
            {
                "hypothesis_id": "h_exp_best",
                "times_selected": 2,
                "last_selected_iteration": 2,
                "last_outcome": "rework",
                "history": [
                    {
                        "selection_iteration": 1,
                        "outcome": "accept",
                    },
                    {
                        "selection_iteration": 2,
                        "outcome": "rework",
                    }
                ],
                "accept_count": 1,
                "rework_count": 1,
                "last_accept_iteration": 1,
                "current_accept_streak": 0,
                "current_rework_streak": 1,
                "status": "mixed",
                "evolution_phase": "regressing",
                "phase_strength": "low",
                "action_mode": "recover_regressing_anchor",
            },
        ],
        "selection_ready": True,
    }


def test_build_campaign_hypotheses_derives_unknown_status_for_unseen_hypothesis() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "active_hypotheses": [],
            "last_selection": None,
            "selection_history": [],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_unknown",
                    "times_selected": 0,
                    "last_selected_iteration": None,
                    "last_outcome": None,
                    "history": [],
                }
            ],
            "selection_ready": False,
        },
        hypothesis_links=None,
        verification=None,
        iteration_number=0,
    )

    assert hypotheses == {
        "active_hypotheses": [],
        "last_selection": None,
        "selection_history": [],
        "frontier_history": [],
        "tracked_hypotheses": [
            {
                "hypothesis_id": "h_unknown",
                "times_selected": 0,
                "last_selected_iteration": None,
                "last_outcome": None,
                "history": [],
                "accept_count": 0,
                "rework_count": 0,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 0,
                "status": "unknown",
                "evolution_phase": "unproven",
                "phase_strength": "low",
                "action_mode": "observe_insufficient_signal",
            }
        ],
        "selection_ready": False,
    }


def test_build_campaign_hypotheses_derives_current_streaks_from_history() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "active_hypotheses": [],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_trend",
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "rework",
                    "history": [
                        {"selection_iteration": 1, "outcome": "accept"},
                        {"selection_iteration": 2, "outcome": "rework"},
                        {"selection_iteration": 3, "outcome": "rework"},
                    ],
                }
            ],
            "selection_ready": True,
        },
        hypothesis_links=["h_trend"],
        verification={"status": "rework"},
        iteration_number=4,
    )

    assert hypotheses == {
        "active_hypotheses": ["h_trend"],
        "last_selection": {
            "hypothesis_links": ["h_trend"],
            "selection_iteration": 4,
            "selection_rationale": {
                "source": "backlog_candidate_links",
                "selection_mode": "selected_candidate_projection",
                "used_backlog_context": True,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "recover_regressing_anchor",
                },
                "ranked_active_hypotheses": [
                    {
                        "hypothesis_id": "h_trend",
                        "status": "unstable",
                        "evolution_phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_regressing_anchor",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    }
                ],
            },
        },
        "selection_history": [
            {
                "hypothesis_links": ["h_trend"],
                "selection_iteration": 4,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "medium",
                        "trajectory_signal": "continuing_regression",
                        "action_mode": "recover_regressing_anchor",
                    },
                    "ranked_active_hypotheses": [
                        {
                            "hypothesis_id": "h_trend",
                            "status": "unstable",
                            "evolution_phase": "regressing",
                            "phase_strength": "medium",
                            "trajectory_signal": "continuing_regression",
                            "action_mode": "recover_regressing_anchor",
                            "suppressed_by": None,
                            "frontier_age": "new",
                            "frontier_trend": "rising",
                        }
                    ],
                },
            }
        ],
        "frontier_history": [
            {
                "iteration": 4,
                "recommended_id": "h_trend",
                "ranked_ids": ["h_trend"],
                "movement_summary": "new_leader",
                "driver_snapshot": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "medium",
                    "trajectory_signal": "continuing_regression",
                    "action_mode": "recover_regressing_anchor",
                },
                "pressure_snapshot": {
                    "leader_tenure": "new",
                    "challenger_pressure": "low",
                },
            }
        ],
        "tracked_hypotheses": [
            {
                "hypothesis_id": "h_trend",
                "times_selected": 4,
                "last_selected_iteration": 4,
                "last_outcome": "rework",
                "history": [
                    {"selection_iteration": 1, "outcome": "accept"},
                    {"selection_iteration": 2, "outcome": "rework"},
                    {"selection_iteration": 3, "outcome": "rework"},
                    {"selection_iteration": 4, "outcome": "rework"},
                ],
                "accept_count": 1,
                "rework_count": 3,
                "last_accept_iteration": 1,
                "current_accept_streak": 0,
                "current_rework_streak": 3,
                "status": "unstable",
                "evolution_phase": "regressing",
                "phase_strength": "medium",
                "action_mode": "recover_regressing_anchor",
            }
        ],
        "selection_ready": True,
    }


def test_build_campaign_hypotheses_tracks_dominant_failure_mode_for_regressing_hypotheses() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=None,
        hypothesis_links=["h_failure"],
        verification={"status": "rework", "failed_check_types": ["artifact_presence"]},
        iteration_number=1,
    )

    assert hypotheses == {
        "active_hypotheses": ["h_failure"],
        "last_selection": {
            "hypothesis_links": ["h_failure"],
            "selection_iteration": 1,
            "selection_rationale": {
                "source": "backlog_candidate_links",
                "selection_mode": "selected_candidate_projection",
                "used_backlog_context": True,
                "used_expansion_recommendations": False,
                "score_signals": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "low",
                    "trajectory_signal": "newly_regressing",
                    "action_mode": "recover_missing_artifacts",
                },
                "ranked_active_hypotheses": [
                    {
                        "hypothesis_id": "h_failure",
                        "status": "unstable",
                        "evolution_phase": "regressing",
                        "phase_strength": "low",
                        "trajectory_signal": "newly_regressing",
                        "action_mode": "recover_missing_artifacts",
                        "suppressed_by": None,
                        "frontier_age": "new",
                        "frontier_trend": "rising",
                    }
                ],
            },
        },
        "selection_history": [
            {
                "hypothesis_links": ["h_failure"],
                "selection_iteration": 1,
                "selection_rationale": {
                    "source": "backlog_candidate_links",
                    "selection_mode": "selected_candidate_projection",
                    "used_backlog_context": True,
                    "used_expansion_recommendations": False,
                    "score_signals": {
                        "status": "unstable",
                        "phase": "regressing",
                        "phase_strength": "low",
                        "trajectory_signal": "newly_regressing",
                        "action_mode": "recover_missing_artifacts",
                    },
                    "ranked_active_hypotheses": [
                        {
                            "hypothesis_id": "h_failure",
                            "status": "unstable",
                            "evolution_phase": "regressing",
                            "phase_strength": "low",
                            "trajectory_signal": "newly_regressing",
                            "action_mode": "recover_missing_artifacts",
                            "suppressed_by": None,
                            "frontier_age": "new",
                            "frontier_trend": "rising",
                        }
                    ],
                },
            }
        ],
        "frontier_history": [
            {
                "iteration": 1,
                "recommended_id": "h_failure",
                "ranked_ids": ["h_failure"],
                "movement_summary": "new_leader",
                "driver_snapshot": {
                    "status": "unstable",
                    "phase": "regressing",
                    "phase_strength": "low",
                    "trajectory_signal": "newly_regressing",
                    "action_mode": "recover_missing_artifacts",
                },
                "pressure_snapshot": {
                    "leader_tenure": "new",
                    "challenger_pressure": "low",
                },
            }
        ],
        "tracked_hypotheses": [
            {
                "hypothesis_id": "h_failure",
                "times_selected": 1,
                "last_selected_iteration": 1,
                "last_outcome": "rework",
                "history": [
                    {
                        "selection_iteration": 1,
                        "outcome": "rework",
                        "failed_check_types": ["artifact_presence"],
                    }
                ],
                "accept_count": 0,
                "rework_count": 1,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 1,
                "status": "unstable",
                "evolution_phase": "regressing",
                "phase_strength": "low",
                "action_mode": "recover_missing_artifacts",
                "dominant_failure_mode": "artifact_presence",
            }
        ],
        "selection_ready": True,
    }


def test_build_campaign_backlog_derives_selection_statistics_from_history() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
        },
        backlog_source="/tmp/demo/backlog.json",
        candidate_count=1,
        iteration_number=1,
        verification={"status": "accept"},
    )

    refreshed = campaign_state.build_campaign_backlog(
        previous_backlog=backlog,
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
        },
        backlog_source=None,
        candidate_count=1,
        iteration_number=2,
        verification={"status": "rework"},
    )

    assert refreshed["tracked_candidates"] == [
        {
            "experiment_id": "exp_best",
            "objective": "Selected backlog objective",
            "hypothesis_links": ["h_exp_best"],
            "expected_information_gain": 0.80,
            "risk_reduction": 0.50,
            "cost_score": 0.20,
            "times_selected": 2,
            "last_selected_iteration": 2,
            "last_outcome": "rework",
            "history": [
                {
                    "selection_iteration": 1,
                    "outcome": "accept",
                },
                {
                    "selection_iteration": 2,
                    "outcome": "rework",
                },
            ],
            "accept_count": 1,
            "rework_count": 1,
            "last_accept_iteration": 1,
            "current_accept_streak": 0,
            "current_rework_streak": 1,
            "status": "mixed",
            "evolution_phase": "regressing",
            "phase_strength": "low",
            "action_mode": "recover_regressing_anchor",
        }
    ]


def test_build_campaign_backlog_derives_current_streaks_from_history() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "tracked_candidates": [
                {
                    "experiment_id": "exp_trend",
                    "objective": "Trend objective",
                    "hypothesis_links": ["h_trend"],
                    "expected_information_gain": 0.7,
                    "risk_reduction": 0.5,
                    "cost_score": 0.2,
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "accept",
                    "history": [
                        {"selection_iteration": 1, "outcome": "rework"},
                        {"selection_iteration": 2, "outcome": "accept"},
                        {"selection_iteration": 3, "outcome": "accept"},
                    ],
                }
            ]
        },
        selected_candidate={
            "experiment_id": "exp_trend",
            "objective": "Trend objective",
            "hypothesis_links": ["h_trend"],
            "expected_information_gain": 0.7,
            "risk_reduction": 0.5,
            "cost_score": 0.2,
        },
        backlog_source=None,
        candidate_count=1,
        iteration_number=4,
        verification={"status": "accept"},
    )

    assert backlog["tracked_candidates"] == [
        {
            "experiment_id": "exp_trend",
            "objective": "Trend objective",
            "hypothesis_links": ["h_trend"],
            "expected_information_gain": 0.7,
            "risk_reduction": 0.5,
            "cost_score": 0.2,
            "times_selected": 4,
            "last_selected_iteration": 4,
            "last_outcome": "accept",
            "history": [
                {"selection_iteration": 1, "outcome": "rework"},
                {"selection_iteration": 2, "outcome": "accept"},
                {"selection_iteration": 3, "outcome": "accept"},
                {"selection_iteration": 4, "outcome": "accept"},
            ],
            "accept_count": 3,
            "rework_count": 1,
            "last_accept_iteration": 4,
            "current_accept_streak": 3,
                "current_rework_streak": 0,
                "status": "mixed",
                "evolution_phase": "recovering",
                "phase_strength": "high",
                "action_mode": "stabilize_recovery",
            }
        ]


def test_build_campaign_backlog_tracks_dominant_failure_mode_for_regressing_candidates() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate={
            "experiment_id": "exp_failure",
            "objective": "Failure-heavy objective",
            "hypothesis_links": ["h_failure"],
            "expected_information_gain": 0.6,
            "risk_reduction": 0.4,
            "cost_score": 0.2,
        },
        backlog_source=None,
        candidate_count=1,
        iteration_number=1,
        verification={"status": "rework", "failed_check_types": ["scientific_validity", "artifact_presence"]},
    )

    assert backlog["tracked_candidates"] == [
        {
            "experiment_id": "exp_failure",
            "objective": "Failure-heavy objective",
            "hypothesis_links": ["h_failure"],
            "expected_information_gain": 0.6,
            "risk_reduction": 0.4,
            "cost_score": 0.2,
            "times_selected": 1,
            "last_selected_iteration": 1,
            "last_outcome": "rework",
            "history": [
                {
                    "selection_iteration": 1,
                    "outcome": "rework",
                    "failed_check_types": ["scientific_validity", "artifact_presence"],
                }
            ],
                "accept_count": 0,
                "rework_count": 1,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 1,
                "status": "blocked",
                "evolution_phase": "regressing",
                "phase_strength": "low",
                "action_mode": "reroute_for_stronger_evidence",
                "dominant_failure_mode": "scientific_validity",
            }
        ]


def test_build_campaign_memory_tracks_latest_accepted_artifacts_and_summary() -> None:
    memory = campaign_state.build_campaign_memory(
        decision="CONTINUE",
        objective="Continue from a successful round.",
        worker_result={
            "summary": "The experiment produced a usable metric trend and a short explanation.",
            "deliverable_paths": ["metrics.json", "result_note.md"],
        },
        artifacts={"deliverable_paths": ["metrics.json", "result_note.md"]},
        verification={"status": "accept"},
        previous_memory=None,
    )

    assert memory == {
        "latest_accepted_objective": "Continue from a successful round.",
        "latest_accepted_summary": "The experiment produced a usable metric trend and a short explanation.",
        "latest_accepted_artifacts": ["metrics.json", "result_note.md"],
        "latest_accepted_iteration_outcome": "accept",
    }


def test_build_campaign_memory_preserves_previous_memory_on_rework() -> None:
    previous_memory = {
        "latest_accepted_objective": "Previous successful round.",
        "latest_accepted_summary": "Earlier accepted evidence.",
        "latest_accepted_artifacts": ["metrics.json"],
        "latest_accepted_iteration_outcome": "accept",
    }

    memory = campaign_state.build_campaign_memory(
        decision="REFINE",
        objective="Recover missing artifacts.",
        worker_result={"summary": "Partial output only", "deliverable_paths": ["partial.txt"]},
        artifacts={"deliverable_paths": ["partial.txt"]},
        verification={"status": "rework", "failed_check_types": ["artifact_presence"]},
        previous_memory=previous_memory,
    )

    assert memory == previous_memory


def test_build_campaign_memory_summary_prefers_result_note_when_available() -> None:
    summary = campaign_state.build_campaign_memory_summary(
        {
            "latest_accepted_objective": "Previous accepted objective.",
            "latest_accepted_summary": "Accepted evidence summary.",
            "latest_accepted_artifacts": ["metrics.json", "result_note.md"],
            "latest_accepted_iteration_outcome": "accept",
        }
    )

    assert summary == {
        "preferred_artifact": "result_note.md",
        "evidence_summary": "Accepted evidence summary.",
        "accepted_memory_ready": True,
    }


def test_build_campaign_memory_summary_handles_missing_accepted_artifacts() -> None:
    summary = campaign_state.build_campaign_memory_summary(
        {
            "latest_accepted_objective": "Initial objective.",
            "latest_accepted_summary": None,
            "latest_accepted_artifacts": [],
            "latest_accepted_iteration_outcome": None,
        }
    )

    assert summary == {
        "preferred_artifact": None,
        "evidence_summary": None,
        "accepted_memory_ready": False,
    }


def test_build_continuation_anchor_uses_preferred_artifact_and_summary() -> None:
    anchor = campaign_state.build_continuation_anchor(
        memory={
            "latest_accepted_objective": "Analyze previous results.",
            "latest_accepted_summary": "Accepted evidence summary.",
            "latest_accepted_artifacts": ["metrics.json", "result_note.md"],
            "latest_accepted_iteration_outcome": "accept",
        },
        memory_summary={
            "preferred_artifact": "result_note.md",
            "evidence_summary": "Accepted evidence summary.",
            "accepted_memory_ready": True,
        },
    )

    assert anchor == {
        "anchor_artifact": "result_note.md",
        "anchor_objective": "Analyze previous results.",
        "anchor_summary": "Accepted evidence summary.",
        "anchor_ready": True,
    }


def test_build_continuation_anchor_is_not_ready_without_accepted_memory() -> None:
    anchor = campaign_state.build_continuation_anchor(
        memory={
            "latest_accepted_objective": "Initial objective.",
            "latest_accepted_summary": None,
            "latest_accepted_artifacts": [],
            "latest_accepted_iteration_outcome": None,
        },
        memory_summary={
            "preferred_artifact": None,
            "evidence_summary": None,
            "accepted_memory_ready": False,
        },
    )

    assert anchor == {
        "anchor_artifact": None,
        "anchor_objective": "Initial objective.",
        "anchor_summary": None,
        "anchor_ready": False,
    }


def test_derive_campaign_lifecycle_distinguishes_not_started_stop_escalate_review_and_progress() -> None:
    assert campaign_state.derive_campaign_lifecycle(
        latest_outcome=None,
        last_decision=None,
        iterations_run=0,
    ) == "not_started"
    assert campaign_state.derive_campaign_lifecycle(
        latest_outcome="pending_review",
        last_decision="STOP",
        iterations_run=2,
    ) == "stopped"
    assert campaign_state.derive_campaign_lifecycle(
        latest_outcome="needs_refinement",
        last_decision="ESCALATE",
        iterations_run=2,
    ) == "escalated"
    assert campaign_state.derive_campaign_lifecycle(
        latest_outcome="pending_review",
        last_decision="CONTINUE",
        iterations_run=2,
    ) == "awaiting_review"
    assert campaign_state.derive_campaign_lifecycle(
        latest_outcome="accepted",
        last_decision="CONTINUE",
        iterations_run=3,
    ) == "in_progress"


def test_build_round_summary_captures_decision_task_and_reason() -> None:
    summary = campaign_state.build_round_summary(
        decision="CONTINUE",
        task_intent={
            "task_type": "code_and_run",
            "acceptance_emphasis": "balanced",
        },
        verification={"status": "accept"},
        brain_plan={"reason": "No prior iteration exists; start from the base objective."},
    )

    assert summary == {
        "decision": "CONTINUE",
        "task_type": "code_and_run",
        "acceptance_emphasis": "balanced",
        "verification_status": "accept",
        "next_action_reason": "No prior iteration exists; start from the base objective.",
    }


def test_build_operator_summary_distinguishes_acceptance_and_refinement_paths() -> None:
    accepted = campaign_state.build_operator_summary(
        task_intent={"task_type": "code_and_run", "acceptance_emphasis": "balanced"},
        verification={"status": "accept", "failed_check_types": []},
    )
    refine = campaign_state.build_operator_summary(
        task_intent={"task_type": "analysis", "acceptance_emphasis": "scientific_validity"},
        verification={"status": "rework", "failed_check_types": ["scientific_validity"]},
    )

    assert accepted == {
        "headline": "Run a code-and-run step for the current research question.",
        "outcome": "accepted",
        "why": "The round satisfied its verification checks.",
        "next_step": "Continue execution from the current objective or successful outputs.",
    }
    assert refine == {
        "headline": "Review the previous successful output through an analysis step.",
        "outcome": "needs_refinement",
        "why": "The round needs stronger scientific explanation before it can be accepted.",
        "next_step": "Refine the previous attempt with stronger evidence, explanation, or method quality.",
    }


def test_build_governance_summary_explains_stop_and_refine_paths() -> None:
    stop_summary = campaign_state.build_governance_summary(
        decision="STOP",
        state={"budget_status": {"experiments_run": 40}, "failure_status": {"failure_streak": 0}},
        verification={"status": "accept"},
        policy={"budgets": {"max_experiments": 40}, "escalation": {"consecutive_failures_threshold": 3}},
    )
    refine_summary = campaign_state.build_governance_summary(
        decision="REFINE",
        state={"budget_status": {"experiments_run": 2}, "failure_status": {"failure_streak": 1}},
        verification={"status": "rework", "rework_priority": "high"},
        policy={"budgets": {"max_experiments": 40}, "escalation": {"consecutive_failures_threshold": 3}},
    )

    assert stop_summary == {
        "decision": "STOP",
        "reason": "The campaign reached its configured experiment budget and must stop.",
        "basis": {
            "verification_status": "accept",
            "rework_priority": "none",
            "failure_streak": 0,
            "experiments_run": 40,
            "max_experiments": 40,
            "failure_threshold": 3,
        },
    }
    assert refine_summary == {
        "decision": "REFINE",
        "reason": "Verification requested rework before the campaign can continue.",
        "basis": {
            "verification_status": "rework",
            "rework_priority": "high",
            "failure_streak": 1,
            "experiments_run": 2,
            "max_experiments": 40,
            "failure_threshold": 3,
        },
    }


def test_build_campaign_backlog_persists_frontier_history_snapshot() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "selection_history": [],
            "tracked_candidates": [
                {
                    "experiment_id": "exp_old",
                    "objective": "Older objective",
                    "status": "mixed",
                    "history": [],
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                }
            ],
            "frontier_history": [
                {
                    "iteration": 1,
                    "recommended_id": "exp_old",
                    "ranked_ids": ["exp_old", "exp_shadow"],
                    "movement_summary": "leader_held",
                }
            ],
        },
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Best objective",
            "hypothesis_links": ["h_best"],
            "selection_rationale": {
                "source": "durable_state",
                "selection_mode": "tracked_reprioritization",
                "ranked_alternatives": [
                    {"experiment_id": "exp_best"},
                    {"experiment_id": "exp_alt"},
                ],
            },
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=2,
        verification={"status": "accept", "failed_check_types": []},
        candidate_pool=[
            {
                "experiment_id": "exp_best",
                "objective": "Best objective",
                "hypothesis_links": ["h_best"],
            },
            {
                "experiment_id": "exp_alt",
                "objective": "Alternative objective",
                "hypothesis_links": ["h_alt"],
            },
        ],
    )

    assert backlog["frontier_history"] == [
        {
            "iteration": 1,
            "recommended_id": "exp_old",
            "ranked_ids": ["exp_old", "exp_shadow"],
            "movement_summary": "leader_held",
            "driver_snapshot": {
                "status": "unproven",
                "phase": "unproven",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "observe_insufficient_signal",
            },
            "pressure_snapshot": {
                "leader_tenure": "new",
                "challenger_pressure": "low",
            },
        },
        {
            "iteration": 2,
            "recommended_id": "exp_best",
            "ranked_ids": ["exp_best", "exp_alt"],
            "movement_summary": "leader_replaced+nearest_alternative_rising",
            "driver_snapshot": {
                "status": "promising",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "pressure_snapshot": {
                "leader_tenure": "new",
                "challenger_pressure": "rising",
            },
        },
    ]


def test_build_campaign_hypotheses_persists_frontier_history_snapshot() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "selection_history": [],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_old",
                    "status": "mixed",
                    "history": [],
                    "trajectory_signal": "stale_stable",
                    "action_mode": "validate_low_confidence_anchor",
                }
            ],
            "frontier_history": [
                {
                    "iteration": 1,
                    "recommended_id": "h_old",
                    "ranked_ids": ["h_old", "h_shadow"],
                    "movement_summary": "leader_held",
                }
            ],
        },
        hypothesis_links=["h_best", "h_alt"],
        verification={"status": "accept", "failed_check_types": []},
        iteration_number=2,
        projected_from_experiment_id="exp_best",
    )

    assert hypotheses["frontier_history"] == [
        {
            "iteration": 1,
            "recommended_id": "h_old",
            "ranked_ids": ["h_old", "h_shadow"],
            "movement_summary": "leader_held",
            "driver_snapshot": {
                "status": "unknown",
                "phase": "unproven",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "observe_insufficient_signal",
            },
            "pressure_snapshot": {
                "leader_tenure": "new",
                "challenger_pressure": "low",
            },
        },
        {
            "iteration": 2,
            "recommended_id": "h_alt",
            "ranked_ids": ["h_alt", "h_best"],
            "movement_summary": "leader_replaced+nearest_alternative_rising",
            "driver_snapshot": {
                "status": "supported",
                "phase": "stable",
                "phase_strength": "low",
                "trajectory_signal": "stale_stable",
                "action_mode": "validate_low_confidence_anchor",
            },
            "pressure_snapshot": {
                "leader_tenure": "new",
                "challenger_pressure": "rising",
            },
        },
    ]


def test_build_campaign_hypotheses_persists_tracked_reprioritization_selection_context() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "selection_history": [
                {
                    "hypothesis_links": ["h_best"],
                    "selection_iteration": 1,
                    "selection_rationale": {
                        "source": "backlog_candidate_links",
                        "selection_mode": "selected_candidate_projection",
                        "used_backlog_context": True,
                        "used_expansion_recommendations": False,
                        "ranked_active_hypotheses": [
                            {
                                "hypothesis_id": "h_best",
                                "status": "supported",
                                "evolution_phase": "stable",
                                "phase_strength": "low",
                                "trajectory_signal": "stale_stable",
                                "action_mode": "validate_low_confidence_anchor",
                                "frontier_age": "persistent",
                                "frontier_trend": "holding",
                            },
                            {
                                "hypothesis_id": "h_alt",
                                "status": "supported",
                                "evolution_phase": "recovering",
                                "phase_strength": "medium",
                                "trajectory_signal": "newly_recovering",
                                "action_mode": "promote_emerging_anchor",
                                "frontier_age": "persistent",
                                "frontier_trend": "rising",
                            },
                        ],
                    },
                }
            ],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_best",
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 1, "outcome": "accept"}],
                    "accept_count": 1,
                    "rework_count": 0,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "trajectory_signal": "stale_stable",
                },
                {
                    "hypothesis_id": "h_alt",
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 1, "outcome": "accept"}],
                    "accept_count": 1,
                    "rework_count": 0,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 1,
                    "current_rework_streak": 0,
                    "phase_strength": "medium",
                    "action_mode": "promote_emerging_anchor",
                    "status": "supported",
                    "evolution_phase": "recovering",
                    "trajectory_signal": "newly_recovering",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 1,
                    "recommended_id": "h_best",
                    "ranked_ids": ["h_best", "h_alt"],
                    "movement_summary": "leader_held",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                    },
                }
            ],
        },
        hypothesis_links=["h_alt"],
        verification={"status": "accept", "failed_check_types": []},
        iteration_number=2,
        projected_from_experiment_id="exp_alt",
        selection_mode="tracked_reprioritization",
        used_frontier_pressure=True,
    )

    rationale = hypotheses["last_selection"]["selection_rationale"]
    assert rationale["source"] == "durable_state"
    assert rationale["selection_mode"] == "tracked_reprioritization"
    assert rationale["used_backlog_context"] is False
    assert rationale["used_frontier_pressure"] is True
    assert hypotheses["active_hypotheses"] == ["h_alt"]


def test_build_campaign_backlog_persists_promotion_gate_outcome_in_frontier_history() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "selection_history": [],
            "tracked_candidates": [
                {
                    "experiment_id": "exp_best",
                    "objective": "Best objective",
                    "hypothesis_links": ["h_best"],
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 2, "outcome": "accept"}],
                    "accept_count": 2,
                    "rework_count": 0,
                    "last_accept_iteration": 2,
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                    "status": "promising",
                    "evolution_phase": "stable",
                    "trajectory_signal": "stale_stable",
                },
                {
                    "experiment_id": "exp_alt",
                    "objective": "Alternative objective",
                    "hypothesis_links": ["h_alt"],
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "rework",
                    "history": [{"selection_iteration": 1, "outcome": "rework"}],
                    "accept_count": 1,
                    "rework_count": 1,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "phase_strength": "high",
                    "action_mode": "scale_confident_anchor",
                    "status": "promising",
                    "evolution_phase": "accelerating",
                    "trajectory_signal": "strong_acceleration",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 1,
                    "recommended_id": "exp_best",
                    "ranked_ids": ["exp_best", "exp_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                    },
                }
            ],
        },
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Best objective",
            "hypothesis_links": ["h_best"],
            "selection_rationale": {
                "source": "durable_state",
                "selection_mode": "tracked_reprioritization",
                "used_linked_hypothesis_state": True,
                "used_expansion_recommendations": True,
                "used_promotion_gate": True,
                "promotion_gate_passed": False,
                "promotion_gate_blocker": "challenger_recent_rework",
                "ranked_alternatives": [
                    {"experiment_id": "exp_best"},
                    {"experiment_id": "exp_alt", "frontier_trend": "rising"},
                ],
            },
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=2,
        verification={"status": "accept", "failed_check_types": []},
        candidate_pool=[
            {
                "experiment_id": "exp_best",
                "objective": "Best objective",
                "hypothesis_links": ["h_best"],
            },
            {
                "experiment_id": "exp_alt",
                "objective": "Alternative objective",
                "hypothesis_links": ["h_alt"],
            },
        ],
    )

    latest_frontier = backlog["frontier_history"][-1]
    assert latest_frontier["movement_summary"] == "leader_held+nearest_alternative_rising+promotion_blocked"
    assert latest_frontier["pressure_snapshot"]["promotion_gate_used"] is True
    assert latest_frontier["pressure_snapshot"]["promotion_gate_passed"] is False
    assert latest_frontier["pressure_snapshot"]["promotion_gate_blocker"] == "challenger_recent_rework"


def test_build_campaign_hypotheses_persists_promotion_gate_outcome_in_frontier_history() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "selection_history": [],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_best",
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 2, "outcome": "accept"}],
                    "accept_count": 2,
                    "rework_count": 0,
                    "last_accept_iteration": 2,
                    "current_accept_streak": 2,
                    "current_rework_streak": 0,
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "trajectory_signal": "stale_stable",
                },
                {
                    "hypothesis_id": "h_alt",
                    "times_selected": 1,
                    "last_selected_iteration": 1,
                    "last_outcome": "rework",
                    "history": [{"selection_iteration": 1, "outcome": "rework"}],
                    "accept_count": 1,
                    "rework_count": 1,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "phase_strength": "medium",
                    "action_mode": "promote_emerging_anchor",
                    "status": "supported",
                    "evolution_phase": "recovering",
                    "trajectory_signal": "newly_recovering",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 1,
                    "recommended_id": "h_best",
                    "ranked_ids": ["h_best", "h_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                    },
                }
            ],
        },
        hypothesis_links=["h_best"],
        verification={"status": "accept", "failed_check_types": []},
        iteration_number=2,
        selection_mode="selected_candidate_projection",
        used_promotion_gate=True,
        promotion_gate_passed=False,
        promotion_gate_blocker="challenger_recent_rework",
    )

    latest_frontier = hypotheses["frontier_history"][-1]
    assert latest_frontier["movement_summary"] == "leader_held+promotion_blocked"
    assert latest_frontier["pressure_snapshot"]["promotion_gate_used"] is True
    assert latest_frontier["pressure_snapshot"]["promotion_gate_passed"] is False
    assert latest_frontier["pressure_snapshot"]["promotion_gate_blocker"] == "challenger_recent_rework"


def test_build_campaign_backlog_marks_persistent_blocked_promotion_pressure() -> None:
    backlog = campaign_state.build_campaign_backlog(
        previous_backlog={
            "selection_history": [],
            "tracked_candidates": [
                {
                    "experiment_id": "exp_best",
                    "objective": "Best objective",
                    "hypothesis_links": ["h_best"],
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 3, "outcome": "accept"}],
                    "accept_count": 3,
                    "rework_count": 0,
                    "last_accept_iteration": 3,
                    "current_accept_streak": 3,
                    "current_rework_streak": 0,
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                    "status": "promising",
                    "evolution_phase": "stable",
                    "trajectory_signal": "established_stable",
                },
                {
                    "experiment_id": "exp_alt",
                    "objective": "Alternative objective",
                    "hypothesis_links": ["h_alt"],
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "rework",
                    "history": [{"selection_iteration": 2, "outcome": "rework"}],
                    "accept_count": 1,
                    "rework_count": 1,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "phase_strength": "high",
                    "action_mode": "scale_confident_anchor",
                    "status": "promising",
                    "evolution_phase": "accelerating",
                    "trajectory_signal": "strong_acceleration",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 2,
                    "recommended_id": "exp_best",
                    "ranked_ids": ["exp_best", "exp_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising+promotion_blocked",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "exp_alt",
                        "promotion_pressure_streak": 1,
                        "promotion_pressure_state": "new",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": False,
                        "promotion_gate_blocker": "challenger_recent_rework",
                    },
                }
            ],
        },
        selected_candidate={
            "experiment_id": "exp_best",
            "objective": "Best objective",
            "hypothesis_links": ["h_best"],
            "selection_rationale": {
                "source": "durable_state",
                "selection_mode": "tracked_reprioritization",
                "used_linked_hypothesis_state": True,
                "used_expansion_recommendations": True,
                "used_promotion_gate": True,
                "promotion_gate_passed": False,
                "promotion_gate_blocker": "challenger_recent_rework",
                "ranked_alternatives": [
                    {"experiment_id": "exp_best"},
                    {"experiment_id": "exp_alt", "frontier_trend": "rising"},
                ],
            },
        },
        backlog_source=None,
        candidate_count=2,
        iteration_number=3,
        verification={"status": "accept", "failed_check_types": []},
        candidate_pool=[
            {
                "experiment_id": "exp_best",
                "objective": "Best objective",
                "hypothesis_links": ["h_best"],
            },
            {
                "experiment_id": "exp_alt",
                "objective": "Alternative objective",
                "hypothesis_links": ["h_alt"],
            },
        ],
    )

    latest_frontier = backlog["frontier_history"][-1]
    assert latest_frontier["movement_summary"] == "leader_held+nearest_alternative_rising+promotion_blocked+promotion_pending"
    assert latest_frontier["pressure_snapshot"]["challenger_id"] == "exp_alt"
    assert latest_frontier["pressure_snapshot"]["promotion_pressure_streak"] == 2
    assert latest_frontier["pressure_snapshot"]["promotion_pressure_state"] == "persistent"


def test_build_campaign_hypotheses_marks_persistent_blocked_promotion_pressure() -> None:
    hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses={
            "selection_history": [],
            "tracked_hypotheses": [
                {
                    "hypothesis_id": "h_best",
                    "times_selected": 3,
                    "last_selected_iteration": 3,
                    "last_outcome": "accept",
                    "history": [{"selection_iteration": 3, "outcome": "accept"}],
                    "accept_count": 3,
                    "rework_count": 0,
                    "last_accept_iteration": 3,
                    "current_accept_streak": 3,
                    "current_rework_streak": 0,
                    "phase_strength": "low",
                    "action_mode": "validate_low_confidence_anchor",
                    "status": "supported",
                    "evolution_phase": "stable",
                    "trajectory_signal": "established_stable",
                },
                {
                    "hypothesis_id": "h_alt",
                    "times_selected": 2,
                    "last_selected_iteration": 2,
                    "last_outcome": "rework",
                    "history": [{"selection_iteration": 2, "outcome": "rework"}],
                    "accept_count": 1,
                    "rework_count": 1,
                    "last_accept_iteration": 1,
                    "current_accept_streak": 0,
                    "current_rework_streak": 1,
                    "phase_strength": "medium",
                    "action_mode": "promote_emerging_anchor",
                    "status": "supported",
                    "evolution_phase": "recovering",
                    "trajectory_signal": "newly_recovering",
                },
            ],
            "frontier_history": [
                {
                    "iteration": 2,
                    "recommended_id": "h_best",
                    "ranked_ids": ["h_best", "h_alt"],
                    "movement_summary": "leader_held+nearest_alternative_rising+promotion_blocked",
                    "pressure_snapshot": {
                        "leader_tenure": "sustained",
                        "challenger_pressure": "rising",
                        "challenger_id": "h_alt",
                        "promotion_pressure_streak": 1,
                        "promotion_pressure_state": "new",
                        "promotion_gate_used": True,
                        "promotion_gate_passed": False,
                        "promotion_gate_blocker": "challenger_recent_rework",
                    },
                }
            ],
        },
        hypothesis_links=["h_best"],
        verification={"status": "accept", "failed_check_types": []},
        iteration_number=3,
        selection_mode="selected_candidate_projection",
        used_promotion_gate=True,
        promotion_gate_passed=False,
        promotion_gate_blocker="challenger_recent_rework",
    )

    latest_frontier = hypotheses["frontier_history"][-1]
    assert latest_frontier["movement_summary"] == "leader_held+promotion_blocked+promotion_pending"
    assert latest_frontier["pressure_snapshot"]["challenger_id"] == "h_alt"
    assert latest_frontier["pressure_snapshot"]["promotion_pressure_streak"] == 2
    assert latest_frontier["pressure_snapshot"]["promotion_pressure_state"] == "persistent"
