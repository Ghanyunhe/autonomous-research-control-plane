from __future__ import annotations


def _derive_selection_stats(history: list[dict] | None) -> dict:
    entries = list(history or [])
    accept_count = sum(1 for item in entries if item.get("outcome") == "accept")
    rework_count = sum(1 for item in entries if item.get("outcome") == "rework")
    last_accept_iteration = None
    for item in entries:
        if item.get("outcome") == "accept":
            last_accept_iteration = item.get("selection_iteration")
    current_accept_streak = 0
    current_rework_streak = 0
    for item in reversed(entries):
        outcome = item.get("outcome")
        if outcome == "accept" and current_rework_streak == 0:
            current_accept_streak += 1
            continue
        if outcome == "rework" and current_accept_streak == 0:
            current_rework_streak += 1
            continue
        break
    return {
        "accept_count": accept_count,
        "rework_count": rework_count,
        "last_accept_iteration": last_accept_iteration,
        "current_accept_streak": current_accept_streak,
        "current_rework_streak": current_rework_streak,
    }


def _derive_dominant_failure_mode(history: list[dict] | None) -> str | None:
    counts: dict[str, int] = {}
    order: list[str] = []
    for item in list(history or []):
        if item.get("outcome") != "rework":
            continue
        for check_type in list(item.get("failed_check_types") or []):
            if check_type not in counts:
                counts[check_type] = 0
                order.append(check_type)
            counts[check_type] += 1
    if not counts:
        return None
    return max(counts, key=lambda check_type: (counts[check_type], -order.index(check_type)))


def _normalize_history_item(item: dict) -> dict:
    normalized = {
        "selection_iteration": item.get("selection_iteration"),
        "outcome": item.get("outcome"),
    }
    failed_check_types = list(item.get("failed_check_types") or [])
    if failed_check_types:
        normalized["failed_check_types"] = failed_check_types
    return normalized


def _derive_hypothesis_status(stats: dict) -> str:
    accept_count = int(stats.get("accept_count", 0) or 0)
    rework_count = int(stats.get("rework_count", 0) or 0)
    if accept_count == 0 and rework_count == 0:
        return "unknown"
    if accept_count > 0 and rework_count == 0:
        return "supported"
    if rework_count > accept_count:
        return "unstable"
    return "mixed"


def _derive_backlog_status(stats: dict) -> str:
    accept_count = int(stats.get("accept_count", 0) or 0)
    rework_count = int(stats.get("rework_count", 0) or 0)
    if accept_count == 0 and rework_count == 0:
        return "unproven"
    if accept_count > 0 and rework_count == 0:
        return "promising"
    if rework_count > accept_count:
        return "blocked"
    return "mixed"


def _derive_evolution_phase(stats: dict, *, status: str) -> str:
    current_accept_streak = int(stats.get("current_accept_streak", 0) or 0)
    current_rework_streak = int(stats.get("current_rework_streak", 0) or 0)
    accept_count = int(stats.get("accept_count", 0) or 0)
    rework_count = int(stats.get("rework_count", 0) or 0)

    if current_rework_streak >= 2 or status in {"blocked", "unstable"}:
        return "regressing"
    if status == "mixed":
        if current_accept_streak > 0:
            return "recovering"
        if current_rework_streak > 0:
            return "regressing"
    if current_accept_streak >= 2 and accept_count > rework_count:
        return "accelerating"
    if current_accept_streak > 0 or status in {"promising", "supported"}:
        return "stable"
    return "unproven"


def _derive_phase_strength(stats: dict, *, phase: str) -> str:
    accept_count = int(stats.get("accept_count", 0) or 0)
    rework_count = int(stats.get("rework_count", 0) or 0)
    current_accept_streak = int(stats.get("current_accept_streak", 0) or 0)
    current_rework_streak = int(stats.get("current_rework_streak", 0) or 0)

    if phase == "accelerating":
        if current_accept_streak >= 4 and accept_count >= 4:
            return "high"
        if current_accept_streak >= 2:
            return "medium"
        return "low"
    if phase == "stable":
        if accept_count >= 3 and rework_count == 0:
            return "medium"
        return "low"
    if phase == "recovering":
        if current_accept_streak >= 3 and rework_count > 0:
            return "high"
        if current_accept_streak >= 1:
            return "medium"
        return "low"
    if phase == "regressing":
        if current_rework_streak >= 4 or rework_count >= 4:
            return "high"
        if current_rework_streak >= 2:
            return "medium"
        return "low"
    return "low"


def _derive_trajectory_signal(stats: dict, *, phase: str, phase_strength: str) -> str:
    accept_count = int(stats.get("accept_count", 0) or 0)
    rework_count = int(stats.get("rework_count", 0) or 0)
    current_accept_streak = int(stats.get("current_accept_streak", 0) or 0)
    current_rework_streak = int(stats.get("current_rework_streak", 0) or 0)

    if phase == "recovering":
        if rework_count > 0 and current_accept_streak == 1:
            return "newly_recovering"
        if phase_strength == "high":
            return "strong_recovery"
        return "continuing_recovery"
    if phase == "accelerating":
        if phase_strength == "high":
            return "strong_acceleration"
        if current_accept_streak == 2:
            return "newly_accelerating"
        return "continuing_acceleration"
    if phase == "regressing":
        if phase_strength == "high":
            return "deep_regression"
        if current_rework_streak == 1:
            return "newly_regressing"
        return "continuing_regression"
    if phase == "stable":
        if accept_count <= 1:
            return "stale_stable"
        return "established_stable"
    return "unproven"


def _derive_action_mode(*, status: str, phase: str, phase_strength: str, dominant_failure_mode: str | None) -> str:
    if phase == "regressing":
        if dominant_failure_mode == "scientific_validity":
            return "reroute_for_stronger_evidence"
        if dominant_failure_mode == "artifact_presence":
            return "recover_missing_artifacts"
        if dominant_failure_mode == "worker_execution":
            return "stabilize_execution"
        return "recover_regressing_anchor"
    if phase == "recovering":
        return "stabilize_recovery"
    if phase == "accelerating":
        if phase_strength == "high":
            return "scale_confident_anchor"
        return "promote_emerging_anchor"
    if phase == "stable":
        if phase_strength == "low":
            return "validate_low_confidence_anchor"
        if status in {"promising", "supported"}:
            return "maintain_viable_anchor"
    return "observe_insufficient_signal"


def _strongest_phase_strength(items: list[dict]) -> str | None:
    rank = {"low": 1, "medium": 2, "high": 3}
    strengths = [item.get("phase_strength") for item in items if item.get("phase_strength") in rank]
    if not strengths:
        return None
    return max(strengths, key=lambda value: rank[value])


def _build_recommendation_drivers(item: dict | None) -> dict | None:
    if not item:
        return None

    phase = item.get("evolution_phase")
    phase_strength = item.get("phase_strength")
    trajectory_signal = item.get("trajectory_signal")
    if trajectory_signal is None and phase:
        trajectory_signal = _derive_trajectory_signal(
            item,
            phase=phase,
            phase_strength=phase_strength or "low",
        )

    drivers = {
        "phase": phase,
        "phase_strength": phase_strength,
        "trajectory_signal": trajectory_signal,
        "action_mode": item.get("action_mode"),
        "status": item.get("status"),
    }
    filtered = {key: value for key, value in drivers.items() if value is not None}
    recommendation_state_hint = _build_anchor_state_hint(
        filtered,
        anchor_label=(
            "recommended hypothesis anchor"
            if item.get("hypothesis_id") is not None
            else "recommended anchor"
        ),
        include_action_mode=True,
    )
    if recommendation_state_hint is not None:
        filtered["recommendation_state_hint"] = recommendation_state_hint
    anchor_trend_hint = _build_anchor_trend_hint(
        item,
        anchor_label=(
            "recommended hypothesis anchor"
            if item.get("hypothesis_id") is not None
            else "recommended anchor"
        ),
    )
    if anchor_trend_hint is not None:
        filtered["anchor_trend_hint"] = anchor_trend_hint
    return filtered


def _build_ranked_alternative(item: dict, *, id_key: str) -> dict:
    status = item.get("status") or "unproven"
    phase = item.get("evolution_phase") or _derive_evolution_phase(item, status=status)
    phase_strength = item.get("phase_strength") or _derive_phase_strength(item, phase=phase)
    trajectory_signal = item.get("trajectory_signal") or _derive_trajectory_signal(
        item,
        phase=phase,
        phase_strength=phase_strength,
    )
    dominant_failure_mode = item.get("dominant_failure_mode")
    action_mode = item.get("action_mode") or _derive_action_mode(
        status=status,
        phase=phase,
        phase_strength=phase_strength,
        dominant_failure_mode=dominant_failure_mode,
    )
    score_band = (
        "high"
        if phase in {"accelerating", "stable"} and phase_strength == "high"
        else "medium"
        if phase in {"accelerating", "recovering", "stable"} and phase_strength in {"medium", "high"}
        else "low"
    )
    return {
        id_key: item.get(id_key),
        "score_band": score_band,
        "reason": f"{phase} {phase_strength}-confidence anchor",
        "action_mode": action_mode,
        "score_signals": _build_score_signals(
            {
                "status": status,
                "evolution_phase": phase,
                "phase_strength": phase_strength,
                "trajectory_signal": trajectory_signal,
                "action_mode": action_mode,
            }
        ),
    }


def _annotate_suppressed_ranked_alternatives(alternatives: list[dict]) -> list[dict]:
    if not alternatives:
        return []

    annotated: list[dict] = []
    leader = alternatives[0]
    leader_score_band = leader.get("score_band")
    leader_action_mode = leader.get("action_mode")

    for index, item in enumerate(alternatives):
        enriched = dict(item)
        if index == 0:
            enriched["suppressed_by"] = None
        elif item.get("score_band") != leader_score_band:
            enriched["suppressed_by"] = "weaker_phase_strength"
        elif item.get("action_mode") != leader_action_mode:
            enriched["suppressed_by"] = "action_mode_misalignment"
        else:
            enriched["suppressed_by"] = "stale_trajectory"
        annotated.append(enriched)
    return annotated


def _annotate_frontier_age(
    alternatives: list[dict],
    *,
    previous_alternatives: list[dict] | None,
    id_key: str,
) -> list[dict]:
    previous_positions = {
        item.get(id_key): index
        for index, item in enumerate(list(previous_alternatives or []))
        if item.get(id_key) is not None
    }
    previous_ids = {
        item.get(id_key)
        for item in list(previous_alternatives or [])
        if item.get(id_key) is not None
    }
    annotated: list[dict] = []
    for item in list(alternatives or []):
        enriched = dict(item)
        enriched["frontier_age"] = "persistent" if enriched.get(id_key) in previous_ids else "new"
        current_index = len(annotated)
        previous_index = previous_positions.get(enriched.get(id_key))
        if previous_index is None:
            enriched["frontier_trend"] = "rising"
        elif previous_index == current_index:
            enriched["frontier_trend"] = "holding"
        elif previous_index > current_index:
            enriched["frontier_trend"] = "rising"
        else:
            enriched["frontier_trend"] = "slipping"
        annotated.append(enriched)
    return annotated


def _build_frontier_snapshot(
    *,
    iteration: int,
    ranked_items: list[dict],
    previous_history: list[dict] | None,
    id_key: str,
    driver_item: dict | None = None,
    promotion_gate: dict | None = None,
) -> dict | None:
    if not ranked_items:
        return None
    recommended_id = ranked_items[0].get(id_key)
    ranked_ids = [item.get(id_key) for item in ranked_items if item.get(id_key) is not None]
    previous_entry = list(previous_history or [])[-1] if previous_history else None
    previous_leader = (previous_entry or {}).get("recommended_id")
    movement_summary = "new_leader"
    if previous_leader is None:
        movement_summary = "new_leader"
    elif previous_leader == recommended_id:
        movement_summary = "leader_held"
    else:
        movement_summary = "leader_replaced"
    second_item = ranked_items[1] if len(ranked_items) > 1 else None
    if second_item and second_item.get("frontier_trend") == "rising":
        movement_summary = f"{movement_summary}+nearest_alternative_rising"
    if promotion_gate and promotion_gate.get("used_promotion_gate") and promotion_gate.get("promotion_gate_passed") is False:
        movement_summary = f"{movement_summary}+promotion_blocked"
    snapshot = {
        "iteration": iteration,
        "recommended_id": recommended_id,
        "ranked_ids": ranked_ids,
        "movement_summary": movement_summary,
    }
    driver_snapshot = _build_driver_snapshot(driver_item or ranked_items[0])
    if driver_snapshot:
        snapshot["driver_snapshot"] = driver_snapshot
    pressure_snapshot = _build_pressure_snapshot(
        recommended_id=recommended_id,
        previous_entry=previous_entry,
        second_item=second_item,
        promotion_gate=promotion_gate,
    )
    if pressure_snapshot:
        if pressure_snapshot.get("promotion_pressure_state") == "persistent":
            movement_summary = f"{movement_summary}+promotion_pending"
            snapshot["movement_summary"] = movement_summary
        snapshot["pressure_snapshot"] = pressure_snapshot
    return snapshot


def _build_driver_snapshot(item: dict | None) -> dict | None:
    if not item:
        return None
    status = item.get("status") or "unproven"
    phase = item.get("evolution_phase") or _derive_evolution_phase(item, status=status)
    phase_strength = item.get("phase_strength") or _derive_phase_strength(item, phase=phase)
    trajectory_signal = item.get("trajectory_signal") or _derive_trajectory_signal(
        item,
        phase=phase,
        phase_strength=phase_strength,
    )
    action_mode = item.get("action_mode") or _derive_action_mode(
        status=status,
        phase=phase,
        phase_strength=phase_strength,
        dominant_failure_mode=item.get("dominant_failure_mode"),
    )
    return _build_score_signals(
        {
            "status": status,
            "evolution_phase": phase,
            "phase_strength": phase_strength,
            "trajectory_signal": trajectory_signal,
            "action_mode": action_mode,
        }
    )


def _build_pressure_snapshot(
    *,
    recommended_id: str | None,
    previous_entry: dict | None,
    second_item: dict | None,
    promotion_gate: dict | None = None,
) -> dict | None:
    if recommended_id is None:
        return None
    previous_recommended_id = (previous_entry or {}).get("recommended_id")
    leader_tenure = "new" if previous_recommended_id != recommended_id else "sustained"
    challenger_pressure = "rising" if second_item and second_item.get("frontier_trend") == "rising" else "low"
    challenger_id = None
    if second_item is not None:
        challenger_id = second_item.get("experiment_id") or second_item.get("hypothesis_id")
    previous_pressure_snapshot = (previous_entry or {}).get("pressure_snapshot") or {}
    previous_challenger_id = previous_pressure_snapshot.get("challenger_id")
    previous_pressure_streak = int(previous_pressure_snapshot.get("promotion_pressure_streak", 0) or 0)
    gate_active = bool(promotion_gate and promotion_gate.get("used_promotion_gate"))
    if (
        challenger_id is None
        and challenger_pressure == "low"
        and gate_active
        and promotion_gate.get("promotion_gate_passed") is False
        and leader_tenure == "sustained"
        and previous_pressure_snapshot.get("challenger_pressure") == "rising"
        and previous_challenger_id is not None
    ):
        challenger_id = previous_challenger_id
        challenger_pressure = "rising"
    promotion_pressure_streak = 0
    promotion_pressure_state = None
    if challenger_pressure == "rising" and challenger_id is not None:
        if previous_challenger_id == challenger_id:
            promotion_pressure_streak = previous_pressure_streak + 1
        else:
            promotion_pressure_streak = 1
        promotion_pressure_state = "persistent" if promotion_pressure_streak >= 2 else "new"
    snapshot = {
        "leader_tenure": leader_tenure,
        "challenger_pressure": challenger_pressure,
    }
    if gate_active and challenger_pressure == "rising" and challenger_id is not None:
        snapshot["challenger_id"] = challenger_id
    if gate_active and challenger_pressure == "rising" and promotion_pressure_streak > 0:
        snapshot["promotion_pressure_streak"] = promotion_pressure_streak
    if gate_active and challenger_pressure == "rising" and promotion_pressure_state is not None:
        snapshot["promotion_pressure_state"] = promotion_pressure_state
    if promotion_gate and promotion_gate.get("used_promotion_gate"):
        snapshot["promotion_gate_used"] = True
        snapshot["promotion_gate_passed"] = bool(promotion_gate.get("promotion_gate_passed"))
        if promotion_gate.get("promotion_gate_blocker") is not None:
            snapshot["promotion_gate_blocker"] = promotion_gate.get("promotion_gate_blocker")
    return snapshot


def _enrich_frontier_history(
    history: list[dict],
    *,
    tracked_items: dict[str, dict],
) -> list[dict]:
    enriched_history: list[dict] = []
    for entry in history:
        enriched_entry = dict(entry)
        recommended_id = enriched_entry.get("recommended_id")
        driver_snapshot = enriched_entry.get("driver_snapshot")
        if driver_snapshot is None and recommended_id is not None:
            candidate = tracked_items.get(recommended_id)
            if candidate is not None:
                derived_snapshot = _build_driver_snapshot(candidate)
                if derived_snapshot:
                    enriched_entry["driver_snapshot"] = derived_snapshot
        if "pressure_snapshot" not in enriched_entry and recommended_id is not None:
            previous_entry = enriched_history[-1] if enriched_history else None
            pressure_snapshot = _build_pressure_snapshot(
                recommended_id=recommended_id,
                previous_entry=previous_entry,
                second_item=None,
            )
            if pressure_snapshot:
                enriched_entry["pressure_snapshot"] = pressure_snapshot
        enriched_history.append(enriched_entry)
    return enriched_history


def _build_selection_context(selection_record: dict | None) -> dict | None:
    if not selection_record:
        return None

    rationale = dict(selection_record.get("selection_rationale") or {})
    if not rationale:
        return None

    status = rationale.get("status")
    phase = rationale.get("phase")
    phase_strength = rationale.get("phase_strength")
    trajectory_signal = rationale.get("trajectory_signal")
    if "score_signals" in rationale:
        score_signals = dict(rationale.get("score_signals") or {})
        status = score_signals.get("status", status)
        phase = score_signals.get("phase", phase)
        phase_strength = score_signals.get("phase_strength", phase_strength)
        trajectory_signal = score_signals.get("trajectory_signal", trajectory_signal)

    selection_state_hint = _build_anchor_state_hint(
        {
            "status": status,
            "phase": phase,
            "phase_strength": phase_strength,
            "trajectory_signal": trajectory_signal,
        },
        anchor_label=(
            "selected hypothesis anchor"
            if selection_record.get("hypothesis_links")
            else "selected anchor"
        ),
    )
    if selection_state_hint is not None:
        rationale["selection_state_hint"] = selection_state_hint
    anchor_trend_hint = _build_anchor_trend_hint(
        rationale,
        anchor_label=(
            "selected hypothesis anchor"
            if selection_record.get("hypothesis_links")
            else "selected anchor"
        ),
    )
    if anchor_trend_hint is not None:
        rationale["anchor_trend_hint"] = anchor_trend_hint

    context = {
        "experiment_id": selection_record.get("experiment_id"),
        "selection_iteration": selection_record.get("selection_iteration"),
        **rationale,
    }
    return {key: value for key, value in context.items() if value is not None}


def _extract_pending_promotion_context(state: dict | None) -> dict | None:
    frontier_history = list((state or {}).get("frontier_history") or [])
    if not frontier_history:
        return None
    latest_frontier = frontier_history[-1]
    pressure_snapshot = latest_frontier.get("pressure_snapshot") or {}
    if pressure_snapshot.get("promotion_pressure_state") != "persistent":
        return None
    if pressure_snapshot.get("promotion_gate_used") is True and pressure_snapshot.get("promotion_gate_passed") is not False:
        return None
    challenger_id = pressure_snapshot.get("challenger_id")
    if challenger_id is None:
        return None
    return {
        "challenger_id": challenger_id,
        "gate_blocker": pressure_snapshot.get("promotion_gate_blocker"),
        "pressure_streak": int(pressure_snapshot.get("promotion_pressure_streak", 0) or 0),
    }


def _extract_promotion_ready_context(state: dict | None) -> dict | None:
    frontier_history = list((state or {}).get("frontier_history") or [])
    if not frontier_history:
        return None
    latest_frontier = frontier_history[-1]
    pressure_snapshot = latest_frontier.get("pressure_snapshot") or {}
    if pressure_snapshot.get("challenger_pressure") != "rising":
        return None
    if pressure_snapshot.get("promotion_gate_used") is not True:
        return None
    if pressure_snapshot.get("promotion_gate_passed") is not True:
        return None
    challenger_id = pressure_snapshot.get("challenger_id")
    if challenger_id is None:
        ranked_ids = list(latest_frontier.get("ranked_ids") or [])
        challenger_id = ranked_ids[1] if len(ranked_ids) > 1 else None
    if challenger_id is None:
        return None
    return {
        "challenger_id": challenger_id,
        "pressure_streak": int(pressure_snapshot.get("promotion_pressure_streak", 0) or 0),
        "leader_tenure": pressure_snapshot.get("leader_tenure"),
    }


def _recovery_streak_from_summary(summary: dict | None) -> int:
    if not summary:
        return 0
    trajectory_signal = summary.get("recommended_trajectory_signal")
    if trajectory_signal == "newly_recovering":
        return 1
    if trajectory_signal == "strong_recovery":
        return 3
    recovery_items = list(summary.get("recovery_candidates") or summary.get("recovery_hypotheses") or [])
    if recovery_items:
        return 2
    return 0


def _build_score_signals(item: dict | None) -> dict | None:
    if not item:
        return None
    signals = {
        "status": item.get("status"),
        "phase": item.get("evolution_phase"),
        "phase_strength": item.get("phase_strength"),
        "trajectory_signal": item.get("trajectory_signal"),
        "action_mode": item.get("action_mode"),
    }
    filtered = {key: value for key, value in signals.items() if value is not None}
    return filtered or None


def _build_anchor_state_hint(
    score_signals: dict | None,
    *,
    anchor_label: str,
    include_action_mode: bool = False,
) -> str | None:
    if not score_signals:
        return None
    hint_parts = [
        part
        for part in [
            score_signals.get("status"),
            score_signals.get("phase"),
            score_signals.get("phase_strength"),
            score_signals.get("trajectory_signal"),
            score_signals.get("action_mode") if include_action_mode else None,
        ]
        if part is not None
    ]
    if not hint_parts:
        return None
    return f"{' / '.join(hint_parts)} {anchor_label}"


def _build_anchor_trend_hint(item: dict | None, *, anchor_label: str) -> str | None:
    if not item:
        return None
    trend = item.get("frontier_trend")
    if trend is None:
        return None
    return f"{trend} {anchor_label}"


def _build_alternative_context(item: dict, *, anchor_label: str) -> dict:
    context = dict(item)
    state_hint = _build_anchor_state_hint(
        context.get("score_signals")
        or {
            "status": context.get("status"),
            "phase": context.get("evolution_phase"),
            "phase_strength": context.get("phase_strength"),
            "trajectory_signal": context.get("trajectory_signal"),
        },
        anchor_label=anchor_label,
    )
    if state_hint is not None:
        context["alternative_state_hint"] = state_hint
    return context


def assess_resume_readiness(last_record: dict | None) -> dict:
    if last_record is None:
        return {
            "resume_ready": False,
            "reasons": ["latest_iteration_missing"],
        }

    reasons: list[str] = []
    if "decision" not in last_record:
        reasons.append("missing_decision")
    if "verification" not in last_record:
        reasons.append("missing_verification")

    return {
        "resume_ready": not reasons,
        "reasons": reasons,
    }


def derive_campaign_lifecycle(*, latest_outcome: str | None, last_decision: str | None, iterations_run: int) -> str:
    if iterations_run <= 0:
        return "not_started"
    if last_decision == "STOP":
        return "stopped"
    if last_decision == "ESCALATE":
        return "escalated"
    if latest_outcome == "pending_review":
        return "awaiting_review"
    return "in_progress"


def build_governance_summary(*, decision: str, state: dict | None, verification: dict | None, policy: dict | None) -> dict:
    budget_status = (state or {}).get("budget_status") or {}
    failure_status = (state or {}).get("failure_status") or {}
    budgets = (policy or {}).get("budgets") or {}
    escalation = (policy or {}).get("escalation") or {}
    verification_payload = verification or {}

    experiments_run = int(budget_status.get("experiments_run", 0))
    failure_streak = int(failure_status.get("failure_streak", 0))
    max_experiments = budgets.get("max_experiments")
    failure_threshold = escalation.get("consecutive_failures_threshold")
    verification_status = verification_payload.get("status")
    rework_priority = verification_payload.get("rework_priority", "none")

    if decision == "STOP":
        reason = "The campaign reached its configured experiment budget and must stop."
    elif decision == "ESCALATE":
        reason = "The campaign hit the consecutive failure threshold and should be escalated."
    elif decision == "REFINE":
        reason = "Verification requested rework before the campaign can continue."
    else:
        reason = "Verification accepted the latest round, so the campaign can continue."

    summary = {
        "decision": decision,
        "reason": reason,
        "basis": {
            "verification_status": verification_status,
            "rework_priority": rework_priority,
            "failure_streak": failure_streak,
            "experiments_run": experiments_run,
        },
    }
    if max_experiments is not None:
        summary["basis"]["max_experiments"] = int(max_experiments)
    if failure_threshold is not None:
        summary["basis"]["failure_threshold"] = int(failure_threshold)
    return summary


def _derive_blocking_issue(verification: dict | None) -> str | None:
    failed_check_types = list((verification or {}).get("failed_check_types") or [])
    if not failed_check_types:
        return None
    if "artifact_presence" in failed_check_types:
        return "artifact_gap"
    if "scientific_validity" in failed_check_types:
        return "scientific_validity_gap"
    if "worker_execution" in failed_check_types:
        return "execution_instability"
    return "verification_gap"


def build_campaign_backlog(
    *,
    previous_backlog: dict | None,
    selected_candidate: dict | None,
    backlog_source: str | None,
    candidate_count: int | None,
    iteration_number: int = 0,
    verification: dict | None = None,
    candidate_pool: list[dict] | None = None,
) -> dict:
    previous_backlog = previous_backlog or {}
    if selected_candidate is None:
        return previous_backlog or {
            "source_type": None,
            "source_path": None,
            "candidate_count": 0,
            "active_candidate": None,
            "last_selection": None,
            "selection_history": [],
            "tracked_candidates": [],
            "selection_ready": False,
        }

    selection_record = {
        "experiment_id": selected_candidate.get("experiment_id"),
        "objective": selected_candidate.get("objective"),
        "hypothesis_links": list(selected_candidate.get("hypothesis_links") or []),
        "selection_iteration": iteration_number,
    }
    selection_rationale = selected_candidate.get("selection_rationale")
    if selection_rationale is not None:
        selection_record["selection_rationale"] = dict(selection_rationale)
    selection_history = list(previous_backlog.get("selection_history") or [])
    frontier_history = list(previous_backlog.get("frontier_history") or [])
    previous_ranked_alternatives = list(
        (((selection_history[-1] if selection_history else {}).get("selection_rationale") or {}).get("ranked_alternatives") or [])
    )
    appended_selection = False
    if not selection_history or selection_history[-1] != selection_record:
        selection_history.append(selection_record)
        appended_selection = True

    tracked = {
        item["experiment_id"]: dict(item)
        for item in list(previous_backlog.get("tracked_candidates") or [])
        if item.get("experiment_id")
    }
    for item in tracked.values():
        item["history"] = [_normalize_history_item(entry) for entry in list(item.get("history") or [])]
        item.update(_derive_selection_stats(item["history"]))
        item["status"] = _derive_backlog_status(item)
        item["evolution_phase"] = _derive_evolution_phase(item, status=item["status"])
        item["phase_strength"] = _derive_phase_strength(item, phase=item["evolution_phase"])
        dominant_failure_mode = _derive_dominant_failure_mode(item["history"])
        if dominant_failure_mode is None:
            item.pop("dominant_failure_mode", None)
        else:
            item["dominant_failure_mode"] = dominant_failure_mode
        item["action_mode"] = _derive_action_mode(
            status=item["status"],
            phase=item["evolution_phase"],
            phase_strength=item["phase_strength"],
            dominant_failure_mode=dominant_failure_mode,
        )
    for candidate in list(candidate_pool or []):
        candidate_id = candidate.get("experiment_id")
        if not candidate_id:
            continue
        current = tracked.get(
            candidate_id,
            {
                "experiment_id": candidate_id,
                "objective": candidate.get("objective"),
                "hypothesis_links": list(candidate.get("hypothesis_links") or []),
                "expected_information_gain": candidate.get("expected_information_gain"),
                "risk_reduction": candidate.get("risk_reduction"),
                "cost_score": candidate.get("cost_score"),
                "times_selected": 0,
                "last_selected_iteration": None,
                "last_outcome": None,
                "history": [],
                "accept_count": 0,
                "rework_count": 0,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 0,
                "phase_strength": "low",
                "dominant_failure_mode": None,
                "action_mode": "observe_insufficient_signal",
            },
        )
        current["objective"] = candidate.get("objective")
        current["hypothesis_links"] = list(candidate.get("hypothesis_links") or [])
        current["expected_information_gain"] = candidate.get("expected_information_gain")
        current["risk_reduction"] = candidate.get("risk_reduction")
        current["cost_score"] = candidate.get("cost_score")
        tracked[candidate_id] = current
    experiment_id = selected_candidate.get("experiment_id")
    current = tracked.get(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "objective": selected_candidate.get("objective"),
            "hypothesis_links": list(selected_candidate.get("hypothesis_links") or []),
            "expected_information_gain": selected_candidate.get("expected_information_gain"),
            "risk_reduction": selected_candidate.get("risk_reduction"),
            "cost_score": selected_candidate.get("cost_score"),
            "times_selected": 0,
            "last_selected_iteration": None,
            "last_outcome": None,
            "history": [],
            "accept_count": 0,
            "rework_count": 0,
            "last_accept_iteration": None,
            "current_accept_streak": 0,
            "current_rework_streak": 0,
            "phase_strength": "low",
            "dominant_failure_mode": None,
            "action_mode": "observe_insufficient_signal",
        },
    )
    current["objective"] = selected_candidate.get("objective")
    current["hypothesis_links"] = list(selected_candidate.get("hypothesis_links") or [])
    current["expected_information_gain"] = selected_candidate.get("expected_information_gain")
    current["risk_reduction"] = selected_candidate.get("risk_reduction")
    current["cost_score"] = selected_candidate.get("cost_score")
    current["times_selected"] = int(current.get("times_selected", 0)) + 1
    current["last_selected_iteration"] = iteration_number
    current["last_outcome"] = (verification or {}).get("status")
    current_history = [_normalize_history_item(entry) for entry in list(current.get("history") or [])]
    current_history.append(
        _normalize_history_item(
            {
                "selection_iteration": iteration_number,
                "outcome": (verification or {}).get("status"),
                "failed_check_types": list((verification or {}).get("failed_check_types") or []),
            }
        )
    )
    current["history"] = current_history
    current.update(_derive_selection_stats(current_history))
    current["status"] = _derive_backlog_status(current)
    current["evolution_phase"] = _derive_evolution_phase(current, status=current["status"])
    current["phase_strength"] = _derive_phase_strength(current, phase=current["evolution_phase"])
    dominant_failure_mode = _derive_dominant_failure_mode(current_history)
    if dominant_failure_mode is None:
        current.pop("dominant_failure_mode", None)
    else:
        current["dominant_failure_mode"] = dominant_failure_mode
    current["action_mode"] = _derive_action_mode(
        status=current["status"],
        phase=current["evolution_phase"],
        phase_strength=current["phase_strength"],
        dominant_failure_mode=dominant_failure_mode,
    )
    tracked[experiment_id] = current
    frontier_history = _enrich_frontier_history(frontier_history, tracked_items=tracked)
    if "selection_rationale" in selection_record:
        score_signals = _build_score_signals(current)
        if score_signals:
            selection_record["selection_rationale"]["score_signals"] = score_signals
        ranked_alternatives = list(selection_record["selection_rationale"].get("ranked_alternatives") or [])
        if ranked_alternatives:
            selection_record["selection_rationale"]["ranked_alternatives"] = _annotate_frontier_age(
                ranked_alternatives,
                previous_alternatives=previous_ranked_alternatives,
                id_key="experiment_id",
            )
        if appended_selection:
            selection_history[-1] = selection_record
        frontier_snapshot = _build_frontier_snapshot(
            iteration=iteration_number,
            ranked_items=list(selection_record["selection_rationale"].get("ranked_alternatives") or []),
            previous_history=frontier_history,
            id_key="experiment_id",
            driver_item=current,
            promotion_gate={
                "used_promotion_gate": selection_record["selection_rationale"].get("used_promotion_gate"),
                "promotion_gate_passed": selection_record["selection_rationale"].get("promotion_gate_passed"),
                "promotion_gate_blocker": selection_record["selection_rationale"].get("promotion_gate_blocker"),
            },
        )
        if frontier_snapshot is not None:
            frontier_history.append(frontier_snapshot)

    return {
        "source_type": "file" if backlog_source is not None else previous_backlog.get("source_type"),
        "source_path": backlog_source if backlog_source is not None else previous_backlog.get("source_path"),
        "candidate_count": int(candidate_count or 0),
        "active_candidate": {
            "experiment_id": selected_candidate.get("experiment_id"),
            "objective": selected_candidate.get("objective"),
            "hypothesis_links": list(selected_candidate.get("hypothesis_links") or []),
        },
        "last_selection": selection_record,
        "selection_history": selection_history,
        "frontier_history": frontier_history,
        "tracked_candidates": sorted(tracked.values(), key=lambda item: item["experiment_id"]),
        "selection_ready": True,
    }


def build_campaign_hypotheses(
    *,
    previous_hypotheses: dict | None,
    hypothesis_links: list[str] | None,
    verification: dict | None,
    iteration_number: int,
    projected_from_experiment_id: str | None = None,
    selection_mode: str = "selected_candidate_projection",
    used_frontier_pressure: bool = False,
    used_promotion_gate: bool = False,
    promotion_gate_passed: bool | None = None,
    promotion_gate_blocker: str | None = None,
) -> dict:
    previous_hypotheses = previous_hypotheses or {}
    active_hypotheses = list(hypothesis_links or [])
    selection_history = list(previous_hypotheses.get("selection_history") or [])
    frontier_history = list(previous_hypotheses.get("frontier_history") or [])
    previous_ranked_active_hypotheses = list(
        (((selection_history[-1] if selection_history else {}).get("selection_rationale") or {}).get("ranked_active_hypotheses") or [])
    )
    if not active_hypotheses:
        existing_tracked = [
            {
                **dict(item),
                "history": [_normalize_history_item(entry) for entry in list((item or {}).get("history") or [])],
            }
            for item in list(previous_hypotheses.get("tracked_hypotheses") or [])
            if item.get("hypothesis_id")
        ]
        for item in existing_tracked:
            item.update(_derive_selection_stats(item["history"]))
            item["status"] = _derive_hypothesis_status(item)
            item["evolution_phase"] = _derive_evolution_phase(item, status=item["status"])
            item["phase_strength"] = _derive_phase_strength(item, phase=item["evolution_phase"])
            dominant_failure_mode = _derive_dominant_failure_mode(item["history"])
            if dominant_failure_mode is None:
                item.pop("dominant_failure_mode", None)
            else:
                item["dominant_failure_mode"] = dominant_failure_mode
            item["action_mode"] = _derive_action_mode(
                status=item["status"],
                phase=item["evolution_phase"],
                phase_strength=item["phase_strength"],
                dominant_failure_mode=dominant_failure_mode,
            )
        if previous_hypotheses:
            return {
                "active_hypotheses": [],
                "last_selection": previous_hypotheses.get("last_selection"),
                "selection_history": selection_history,
                "frontier_history": frontier_history,
                "tracked_hypotheses": sorted(existing_tracked, key=lambda item: item["hypothesis_id"]),
                "selection_ready": False,
            }
        return {
            "active_hypotheses": [],
            "last_selection": None,
            "selection_history": [],
            "frontier_history": [],
            "tracked_hypotheses": [],
            "selection_ready": False,
        }

    selection_record = {
        "hypothesis_links": active_hypotheses,
        "selection_iteration": iteration_number,
        "selection_rationale": {
            "source": "durable_state" if selection_mode == "tracked_reprioritization" else "backlog_candidate_links",
            "selection_mode": selection_mode,
            "used_backlog_context": selection_mode != "tracked_reprioritization",
            "used_expansion_recommendations": False,
        },
    }
    if used_frontier_pressure:
        selection_record["selection_rationale"]["used_frontier_pressure"] = True
    if used_promotion_gate:
        selection_record["selection_rationale"]["used_promotion_gate"] = True
        selection_record["selection_rationale"]["promotion_gate_passed"] = bool(promotion_gate_passed)
        if promotion_gate_blocker is not None:
            selection_record["selection_rationale"]["promotion_gate_blocker"] = promotion_gate_blocker
    if projected_from_experiment_id is not None:
        selection_record["selection_rationale"]["projected_from_experiment_id"] = projected_from_experiment_id
    appended_selection = False
    if not selection_history or selection_history[-1] != selection_record:
        selection_history.append(selection_record)
        appended_selection = True

    tracked = {
        item["hypothesis_id"]: dict(item)
        for item in list(previous_hypotheses.get("tracked_hypotheses") or [])
        if item.get("hypothesis_id")
    }
    for item in tracked.values():
        item["history"] = [_normalize_history_item(entry) for entry in list(item.get("history") or [])]
        item.update(_derive_selection_stats(item["history"]))
        item["status"] = _derive_hypothesis_status(item)
        item["evolution_phase"] = _derive_evolution_phase(item, status=item["status"])
        item["phase_strength"] = _derive_phase_strength(item, phase=item["evolution_phase"])
        dominant_failure_mode = _derive_dominant_failure_mode(item["history"])
        if dominant_failure_mode is None:
            item.pop("dominant_failure_mode", None)
        else:
            item["dominant_failure_mode"] = dominant_failure_mode
        item["action_mode"] = _derive_action_mode(
            status=item["status"],
            phase=item["evolution_phase"],
            phase_strength=item["phase_strength"],
            dominant_failure_mode=dominant_failure_mode,
        )
    verification_status = (verification or {}).get("status")

    for hypothesis_id in active_hypotheses:
        current = tracked.get(
            hypothesis_id,
            {
                "hypothesis_id": hypothesis_id,
                "times_selected": 0,
                "last_selected_iteration": None,
                "last_outcome": None,
                "history": [],
                "accept_count": 0,
                "rework_count": 0,
                "last_accept_iteration": None,
                "current_accept_streak": 0,
                "current_rework_streak": 0,
                "phase_strength": "low",
                "dominant_failure_mode": None,
                "action_mode": "observe_insufficient_signal",
            },
        )
        current["times_selected"] = int(current.get("times_selected", 0)) + 1
        current["last_selected_iteration"] = iteration_number
        current["last_outcome"] = verification_status
        current_history = [_normalize_history_item(entry) for entry in list(current.get("history") or [])]
        current_history.append(
            _normalize_history_item(
                {
                    "selection_iteration": iteration_number,
                    "outcome": verification_status,
                    "failed_check_types": list((verification or {}).get("failed_check_types") or []),
                }
            )
        )
        current["history"] = current_history
        current.update(_derive_selection_stats(current_history))
        current["status"] = _derive_hypothesis_status(current)
        current["evolution_phase"] = _derive_evolution_phase(current, status=current["status"])
        current["phase_strength"] = _derive_phase_strength(current, phase=current["evolution_phase"])
        dominant_failure_mode = _derive_dominant_failure_mode(current_history)
        if dominant_failure_mode is None:
            current.pop("dominant_failure_mode", None)
        else:
            current["dominant_failure_mode"] = dominant_failure_mode
        current["action_mode"] = _derive_action_mode(
            status=current["status"],
            phase=current["evolution_phase"],
            phase_strength=current["phase_strength"],
            dominant_failure_mode=dominant_failure_mode,
        )
        tracked[hypothesis_id] = current

    ranked_active_hypotheses = _annotate_suppressed_ranked_alternatives(
        [
            {
                "hypothesis_id": item.get("hypothesis_id"),
                "status": item.get("status"),
                "evolution_phase": item.get("evolution_phase"),
                "phase_strength": item.get("phase_strength"),
                "trajectory_signal": item.get("trajectory_signal")
                or _derive_trajectory_signal(
                    item,
                    phase=item.get("evolution_phase", "unproven"),
                    phase_strength=item.get("phase_strength", "low"),
                ),
                "action_mode": item.get("action_mode"),
            }
            for item in sorted(
                (
                    item
                    for item in tracked.values()
                    if item.get("hypothesis_id") in active_hypotheses
                ),
                key=lambda item: (
                    0
                    if item.get("evolution_phase") == "accelerating"
                    else 1
                    if item.get("evolution_phase") == "recovering"
                    else 2
                    if item.get("evolution_phase") == "stable"
                    else 3,
                    0
                    if item.get("phase_strength") == "high"
                    else 1
                    if item.get("phase_strength") == "medium"
                    else 2,
                    item.get("hypothesis_id"),
                ),
            )
        ]
    )
    frontier_history = _enrich_frontier_history(frontier_history, tracked_items=tracked)
    if ranked_active_hypotheses:
        ranked_active_hypotheses = _annotate_frontier_age(
            ranked_active_hypotheses,
            previous_alternatives=previous_ranked_active_hypotheses,
            id_key="hypothesis_id",
        )
        score_signals = _build_score_signals(
            {
                "status": ranked_active_hypotheses[0].get("status"),
                "evolution_phase": ranked_active_hypotheses[0].get("evolution_phase"),
                "phase_strength": ranked_active_hypotheses[0].get("phase_strength"),
                "trajectory_signal": ranked_active_hypotheses[0].get("trajectory_signal"),
                "action_mode": ranked_active_hypotheses[0].get("action_mode"),
            }
        )
        if score_signals:
            selection_record["selection_rationale"]["score_signals"] = score_signals
        selection_record["selection_rationale"]["ranked_active_hypotheses"] = ranked_active_hypotheses
        if appended_selection:
            selection_history[-1] = selection_record
        frontier_snapshot = _build_frontier_snapshot(
            iteration=iteration_number,
            ranked_items=ranked_active_hypotheses,
            previous_history=frontier_history,
            id_key="hypothesis_id",
            driver_item=tracked.get(ranked_active_hypotheses[0].get("hypothesis_id")),
            promotion_gate={
                "used_promotion_gate": selection_record["selection_rationale"].get("used_promotion_gate"),
                "promotion_gate_passed": selection_record["selection_rationale"].get("promotion_gate_passed"),
                "promotion_gate_blocker": selection_record["selection_rationale"].get("promotion_gate_blocker"),
            },
        )
        if frontier_snapshot is not None:
            frontier_history.append(frontier_snapshot)

    return {
        "active_hypotheses": active_hypotheses,
        "last_selection": selection_record,
        "selection_history": selection_history,
        "frontier_history": frontier_history,
        "tracked_hypotheses": sorted(tracked.values(), key=lambda item: item["hypothesis_id"]),
        "selection_ready": True,
    }


def build_backlog_summary(backlog: dict | None) -> dict:
    backlog = backlog or {}
    tracked_candidates = list(backlog.get("tracked_candidates") or [])
    active_candidate = backlog.get("active_candidate") or {}
    ranked_candidates = list((backlog.get("backlog_evolution_summary") or {}).get("ranked_candidates") or [])
    if not ranked_candidates:
        ranked_candidates = list(build_backlog_evolution_summary(backlog).get("ranked_candidates") or [])

    promising = sorted(
        candidate["experiment_id"]
        for candidate in tracked_candidates
        if candidate.get("experiment_id") and candidate.get("status") == "promising"
    )
    blocked = sorted(
        candidate["experiment_id"]
        for candidate in tracked_candidates
        if candidate.get("experiment_id") and candidate.get("status") == "blocked"
    )
    unproven = sorted(
        candidate["experiment_id"]
        for candidate in tracked_candidates
        if candidate.get("experiment_id") and candidate.get("status") == "unproven"
    )

    recommended = next(
        (
            candidate
            for candidate in tracked_candidates
            if candidate.get("experiment_id") == active_candidate.get("experiment_id")
            and candidate.get("status") == "promising"
        ),
        None,
    )
    if recommended is None:
        recommended = next(
            (candidate for candidate in tracked_candidates if candidate.get("status") == "promising"),
            None,
        )
    if recommended is None:
        recommended = next(
            (candidate for candidate in tracked_candidates if candidate.get("experiment_id") == active_candidate.get("experiment_id")),
            None,
        )

    summary = {
        "selection_ready": bool(backlog.get("selection_ready")),
        "active_experiment_id": active_candidate.get("experiment_id"),
        "active_objective": active_candidate.get("objective"),
        "promising_candidates": promising,
        "blocked_candidates": blocked,
        "unproven_candidates": unproven,
        "recommended_anchor_experiment_id": None if recommended is None else recommended.get("experiment_id"),
        "recommended_anchor_status": None if recommended is None else recommended.get("status"),
    }
    if recommended is not None and list(recommended.get("hypothesis_links") or []):
        summary["recommended_anchor_hypothesis_links"] = list(recommended.get("hypothesis_links") or [])
    selection_context = _build_selection_context(backlog.get("last_selection"))
    if selection_context is not None and selection_context.get("experiment_id") == summary["recommended_anchor_experiment_id"]:
        summary["recommended_anchor_selection_context"] = selection_context
    if len(ranked_candidates) > 1:
        summary["alternative_anchor_context"] = ranked_candidates[1]
    return summary


def build_backlog_evolution_summary(backlog: dict | None) -> dict:
    backlog = backlog or {}
    tracked_candidates = list(backlog.get("tracked_candidates") or [])
    active_candidate_id = ((backlog.get("active_candidate") or {}).get("experiment_id"))
    dominant_failure_mode = None
    pending_promotion = _extract_pending_promotion_context(backlog)
    promotion_ready = _extract_promotion_ready_context(backlog)
    phase_strength_signal = _strongest_phase_strength(tracked_candidates)
    trajectory_signal_rank = {
        "newly_recovering": 6,
        "strong_recovery": 5,
        "continuing_recovery": 4,
        "strong_acceleration": 4,
        "newly_accelerating": 3,
        "continuing_acceleration": 2,
        "established_stable": 1,
        "stale_stable": 0,
        "newly_regressing": -1,
        "continuing_regression": -2,
        "deep_regression": -3,
        "unproven": -4,
    }

    def _ids_for(predicate) -> list[str]:  # noqa: ANN001
        return sorted(
            item["experiment_id"]
            for item in tracked_candidates
            if item.get("experiment_id") and predicate(item)
        )

    advancing = _ids_for(
        lambda item: item.get("status") == "promising" and int(item.get("current_accept_streak", 0) or 0) > 0
    )
    regressing = _ids_for(
        lambda item: (
            item.get("evolution_phase") == "regressing"
            and item.get("experiment_id") == active_candidate_id
        )
        or (
            item.get("status") == "blocked"
            and int(item.get("current_rework_streak", 0) or 0) > 0
        )
    )
    recovery = _ids_for(
        lambda item: item.get("status") == "mixed" and int(item.get("current_accept_streak", 0) or 0) > 0
    )
    accelerating = _ids_for(lambda item: item.get("evolution_phase") == "accelerating")
    stable = _ids_for(lambda item: item.get("evolution_phase") == "stable")
    healthier_candidates = sorted(
        item["experiment_id"]
        for item in tracked_candidates
        if item.get("experiment_id") and item.get("status") in {"promising", "mixed", "unproven"}
    )

    def _trajectory_signal_for(item: dict) -> str:
        return item.get("trajectory_signal") or _derive_trajectory_signal(
            item,
            phase=item.get("evolution_phase", "unproven"),
            phase_strength=item.get("phase_strength", "low"),
        )

    has_priority_recovery = any(
        _trajectory_signal_for(item) in {"newly_recovering", "strong_recovery"} for item in tracked_candidates
    )

    if pending_promotion is not None:
        recommended_experiment_id = pending_promotion["challenger_id"]
        recommended_action = "investigate_pending_candidate_promotion"
        status_headline = (
            "A rising backlog challenger has been blocked from promotion across consecutive rounds and should be investigated before promotion."
        )
    elif promotion_ready is not None:
        recommended_experiment_id = promotion_ready["challenger_id"]
        recommended_action = "promote_ready_candidate"
        status_headline = (
            "A rising backlog challenger has cleared the promotion gate and should now be promoted over the decaying leader."
        )
    elif has_priority_recovery and recovery:
        recommended_experiment_id = sorted(
            recovery,
            key=lambda candidate_id: -trajectory_signal_rank.get(
                next(
                    (
                        _trajectory_signal_for(item)
                        for item in tracked_candidates
                        if item.get("experiment_id") == candidate_id
                    ),
                    "unproven",
                ),
                -4,
            ),
        )[0]
        recommended_action = "stabilize_recovering_candidate"
        status_headline = "A mixed backlog candidate is recovering, but it still needs stabilization."
    elif advancing:
        recommended_experiment_id = advancing[0]
        recommended_action = "promote_promising_candidate"
        if regressing:
            status_headline = "A promising backlog candidate is advancing, but some candidates still need recovery."
        else:
            status_headline = "A promising backlog candidate is advancing and ready to promote."
    elif recovery:
        recommended_experiment_id = sorted(
            recovery,
            key=lambda candidate_id: -trajectory_signal_rank.get(
                next(
                    (
                        _trajectory_signal_for(item)
                        for item in tracked_candidates
                        if item.get("experiment_id") == candidate_id
                    ),
                    "unproven",
                ),
                -4,
            ),
        )[0]
        recommended_action = "stabilize_recovering_candidate"
        status_headline = "A mixed backlog candidate is recovering, but it still needs stabilization."
    elif regressing:
        recommended_experiment_id = healthier_candidates[0] if healthier_candidates else regressing[0]
        recommended_action = "recover_regressing_candidate"
        dominant_failure_mode = next(
            (
                item.get("dominant_failure_mode")
                for item in tracked_candidates
                if item.get("experiment_id") in regressing and item.get("dominant_failure_mode")
            ),
            None,
        )
        if healthier_candidates:
            if dominant_failure_mode:
                status_headline = (
                    "The campaign's active backlog candidates are regressing due to "
                    f"{dominant_failure_mode} failures and should shift toward a healthier candidate."
                )
            else:
                status_headline = "The campaign's active backlog candidates are regressing and should shift toward a healthier candidate."
        else:
            if dominant_failure_mode:
                status_headline = (
                    "The campaign's active backlog candidates are regressing due to "
                    f"{dominant_failure_mode} failures and need recovery."
                )
            else:
                status_headline = "The campaign's active backlog candidates are regressing and need recovery."
    else:
        recommended_experiment_id = None
        recommended_action = "insufficient_backlog_signal"
        status_headline = "The campaign has not accumulated enough backlog evidence to recommend an evolution path."

    summary = {
        "selection_ready": bool(backlog.get("selection_ready")),
        "advancing_candidates": advancing,
        "regressing_candidates": regressing,
        "recovery_candidates": recovery,
        "accelerating_candidates": accelerating,
        "stable_candidates": stable,
        "recommended_experiment_id": recommended_experiment_id,
        "recommended_action": recommended_action,
        "status_headline": status_headline,
    }
    if phase_strength_signal is not None:
        summary["phase_strength_signal"] = phase_strength_signal
    if dominant_failure_mode is not None:
        summary["dominant_failure_mode"] = dominant_failure_mode
    if pending_promotion is not None:
        summary["pending_promotion_candidate_id"] = pending_promotion["challenger_id"]
        summary["pending_promotion_pressure_streak"] = pending_promotion["pressure_streak"]
        if pending_promotion["gate_blocker"] is not None:
            summary["pending_promotion_gate_blocker"] = pending_promotion["gate_blocker"]
    if promotion_ready is not None:
        summary["promotion_ready_candidate_id"] = promotion_ready["challenger_id"]
        if promotion_ready["pressure_streak"] > 0:
            summary["promotion_ready_pressure_streak"] = promotion_ready["pressure_streak"]
    recommended_candidate = next(
        (item for item in tracked_candidates if item.get("experiment_id") == recommended_experiment_id),
        None,
    )
    if recommended_candidate is not None and recommended_candidate.get("action_mode"):
        summary["recommended_action_mode"] = recommended_candidate["action_mode"]
    if recommended_candidate is not None:
        summary["recommended_trajectory_signal"] = _trajectory_signal_for(recommended_candidate)
        summary["recommendation_drivers"] = _build_recommendation_drivers(recommended_candidate)
    ranked_candidates = _annotate_suppressed_ranked_alternatives([
        _build_ranked_alternative(item, id_key="experiment_id")
        for item in sorted(
            (item for item in tracked_candidates if item.get("experiment_id")),
            key=lambda item: (
                0
                if item.get("evolution_phase") == "accelerating"
                else 1
                if item.get("evolution_phase") == "recovering"
                else 2
                if item.get("evolution_phase") == "stable"
                else 3,
                0
                if item.get("phase_strength") == "high"
                else 1
                if item.get("phase_strength") == "medium"
                else 2,
                item.get("experiment_id"),
            ),
        )
    ])
    previous_ranked_candidates = list(((backlog.get("backlog_evolution_summary") or {}).get("ranked_candidates") or []))
    summary["ranked_candidates"] = _annotate_frontier_age(
        ranked_candidates,
        previous_alternatives=previous_ranked_candidates,
        id_key="experiment_id",
    )
    return summary


def build_hypothesis_summary(hypotheses: dict | None) -> dict:
    hypotheses = hypotheses or {}
    previous_ranked_active_hypotheses = list(
        (((hypotheses.get("last_selection") or {}).get("selection_rationale") or {}).get("ranked_active_hypotheses") or [])
    )
    tracked_hypotheses = list(hypotheses.get("tracked_hypotheses") or [])
    active_hypotheses = list(hypotheses.get("active_hypotheses") or [])

    def _ids_for(status: str) -> list[str]:
        return sorted(
            item["hypothesis_id"]
            for item in tracked_hypotheses
            if item.get("hypothesis_id") and item.get("status") == status
        )

    supported = _ids_for("supported")
    unstable = _ids_for("unstable")
    mixed = _ids_for("mixed")
    unknown = _ids_for("unknown")

    recommended = None
    if active_hypotheses:
        recommended = next(
            (item for item in tracked_hypotheses if item.get("hypothesis_id") == active_hypotheses[0]),
            None,
        )
    if recommended is None:
        recommended = next(
            (item for item in tracked_hypotheses if item.get("status") == "supported"),
            None,
        )

    summary = {
        "selection_ready": bool(hypotheses.get("selection_ready")),
        "active_hypotheses": active_hypotheses,
        "supported_hypotheses": supported,
        "unstable_hypotheses": unstable,
        "mixed_hypotheses": mixed,
        "unknown_hypotheses": unknown,
        "recommended_hypothesis_id": None if recommended is None else recommended.get("hypothesis_id"),
        "recommended_hypothesis_status": None if recommended is None else recommended.get("status"),
    }
    ranked_active_items: list[dict] = []
    for item in tracked_hypotheses:
        if item.get("hypothesis_id") not in active_hypotheses:
            continue
        status = item.get("status") or "unknown"
        phase = item.get("evolution_phase") or _derive_evolution_phase(item, status=status)
        phase_strength = item.get("phase_strength") or _derive_phase_strength(item, phase=phase)
        ranked_active_items.append(
            {
                "hypothesis_id": item.get("hypothesis_id"),
                "status": status,
                "evolution_phase": phase,
                "phase_strength": phase_strength,
                "trajectory_signal": item.get("trajectory_signal")
                or _derive_trajectory_signal(
                    item,
                    phase=phase,
                    phase_strength=phase_strength,
                ),
                "action_mode": item.get("action_mode")
                or _derive_action_mode(
                    status=status,
                    phase=phase,
                    phase_strength=phase_strength,
                    dominant_failure_mode=item.get("dominant_failure_mode"),
                ),
            }
        )
    ranked_active_hypotheses = _annotate_suppressed_ranked_alternatives(
        sorted(
            ranked_active_items,
            key=lambda item: (
                0
                if item.get("evolution_phase") == "accelerating"
                else 1
                if item.get("evolution_phase") == "recovering"
                else 2
                if item.get("evolution_phase") == "stable"
                else 3,
                0
                if item.get("phase_strength") == "high"
                else 1
                if item.get("phase_strength") == "medium"
                else 2,
                item.get("hypothesis_id"),
            ),
        )
    )
    if ranked_active_hypotheses:
        ranked_active_hypotheses = _annotate_frontier_age(
            ranked_active_hypotheses,
            previous_alternatives=previous_ranked_active_hypotheses,
            id_key="hypothesis_id",
        )
        summary["ranked_active_hypotheses"] = ranked_active_hypotheses
        if len(ranked_active_hypotheses) > 1:
            summary["active_alternative_context"] = _build_alternative_context(
                ranked_active_hypotheses[1],
                anchor_label="reserve active hypothesis anchor",
            )
    selection_record = hypotheses.get("last_selection")
    selection_context = _build_selection_context(selection_record)
    recommended_hypothesis_id = summary["recommended_hypothesis_id"]
    if (
        selection_context is not None
        and recommended_hypothesis_id is not None
        and recommended_hypothesis_id in list((selection_record or {}).get("hypothesis_links") or [])
    ):
        selection_context.pop("hypothesis_links", None)
        selection_context.pop("hypothesis_id", None)
        summary["recommended_hypothesis_selection_context"] = selection_context
    return summary


def build_hypothesis_evolution_summary(hypotheses: dict | None) -> dict:
    hypotheses = hypotheses or {}
    tracked_hypotheses = list(hypotheses.get("tracked_hypotheses") or [])
    active_hypothesis_ids = set(hypotheses.get("active_hypotheses") or [])
    dominant_failure_mode = None
    pending_promotion = _extract_pending_promotion_context(hypotheses)
    promotion_ready = _extract_promotion_ready_context(hypotheses)
    phase_strength_signal = _strongest_phase_strength(tracked_hypotheses)
    trajectory_signal_rank = {
        "newly_recovering": 6,
        "strong_recovery": 5,
        "continuing_recovery": 4,
        "strong_acceleration": 4,
        "newly_accelerating": 3,
        "continuing_acceleration": 2,
        "established_stable": 1,
        "stale_stable": 0,
        "newly_regressing": -1,
        "continuing_regression": -2,
        "deep_regression": -3,
        "unproven": -4,
    }

    def _ids_for(predicate) -> list[str]:  # noqa: ANN001
        return sorted(
            item["hypothesis_id"]
            for item in tracked_hypotheses
            if item.get("hypothesis_id") and predicate(item)
        )

    advancing = _ids_for(
        lambda item: item.get("status") == "supported" and int(item.get("current_accept_streak", 0) or 0) > 0
    )
    regressing = _ids_for(
        lambda item: (
            item.get("evolution_phase") == "regressing"
            and item.get("hypothesis_id") in active_hypothesis_ids
        )
        or (
            item.get("status") == "unstable"
            and int(item.get("current_rework_streak", 0) or 0) > 0
        )
    )
    recovery = _ids_for(
        lambda item: item.get("status") == "mixed" and int(item.get("current_accept_streak", 0) or 0) > 0
    )
    accelerating = _ids_for(lambda item: item.get("evolution_phase") == "accelerating")
    stable = _ids_for(lambda item: item.get("evolution_phase") == "stable")
    healthier_hypotheses = sorted(
        item["hypothesis_id"]
        for item in tracked_hypotheses
        if item.get("hypothesis_id") and item.get("status") in {"supported", "mixed", "unknown"}
    )

    def _trajectory_signal_for(item: dict) -> str:
        return item.get("trajectory_signal") or _derive_trajectory_signal(
            item,
            phase=item.get("evolution_phase", "unproven"),
            phase_strength=item.get("phase_strength", "low"),
        )

    has_priority_recovery = any(
        _trajectory_signal_for(item) in {"newly_recovering", "strong_recovery"} for item in tracked_hypotheses
    )

    if pending_promotion is not None:
        recommended_hypothesis_id = pending_promotion["challenger_id"]
        recommended_action = "investigate_pending_hypothesis_promotion"
        status_headline = (
            "A rising hypothesis challenger has been blocked from promotion across consecutive rounds and should be investigated before promotion."
        )
    elif promotion_ready is not None:
        recommended_hypothesis_id = promotion_ready["challenger_id"]
        recommended_action = "promote_ready_hypothesis"
        status_headline = (
            "A rising hypothesis challenger has cleared the promotion gate and should now be promoted over the decaying leader."
        )
    elif has_priority_recovery and recovery:
        recommended_hypothesis_id = sorted(
            recovery,
            key=lambda hypothesis_id: -trajectory_signal_rank.get(
                next(
                    (
                        _trajectory_signal_for(item)
                        for item in tracked_hypotheses
                        if item.get("hypothesis_id") == hypothesis_id
                    ),
                    "unproven",
                ),
                -4,
            ),
        )[0]
        recommended_action = "stabilize_recovering_hypothesis"
        status_headline = "A mixed hypothesis is recovering, but it still needs stabilization."
    elif advancing:
        recommended_hypothesis_id = advancing[0]
        recommended_action = "promote_supported_hypothesis"
        if regressing:
            status_headline = "A supported hypothesis is advancing, but some hypotheses still need stabilization."
        else:
            status_headline = "A supported hypothesis is advancing and ready to promote."
    elif recovery:
        recommended_hypothesis_id = sorted(
            recovery,
            key=lambda hypothesis_id: -trajectory_signal_rank.get(
                next(
                    (
                        _trajectory_signal_for(item)
                        for item in tracked_hypotheses
                        if item.get("hypothesis_id") == hypothesis_id
                    ),
                    "unproven",
                ),
                -4,
            ),
        )[0]
        recommended_action = "stabilize_recovering_hypothesis"
        status_headline = "A mixed hypothesis is recovering, but it still needs stabilization."
    elif regressing:
        recommended_hypothesis_id = healthier_hypotheses[0] if healthier_hypotheses else regressing[0]
        recommended_action = "stabilize_regressing_hypothesis"
        dominant_failure_mode = next(
            (
                item.get("dominant_failure_mode")
                for item in tracked_hypotheses
                if item.get("hypothesis_id") in regressing and item.get("dominant_failure_mode")
            ),
            None,
        )
        if healthier_hypotheses:
            if dominant_failure_mode:
                status_headline = (
                    "The campaign's active hypothesis signals are regressing due to "
                    f"{dominant_failure_mode} failures and should shift toward a healthier hypothesis anchor."
                )
            else:
                status_headline = "The campaign's active hypothesis signals are regressing and should shift toward a healthier hypothesis anchor."
        else:
            if dominant_failure_mode:
                status_headline = (
                    "The campaign's active hypothesis signals are regressing due to "
                    f"{dominant_failure_mode} failures and need stabilization."
                )
            else:
                status_headline = "The campaign's active hypothesis signals are regressing and need stabilization."
    else:
        recommended_hypothesis_id = None
        recommended_action = "insufficient_hypothesis_signal"
        status_headline = "The campaign has not accumulated enough hypothesis evidence to recommend an evolution path."

    summary = {
        "selection_ready": bool(hypotheses.get("selection_ready")),
        "advancing_hypotheses": advancing,
        "regressing_hypotheses": regressing,
        "recovery_hypotheses": recovery,
        "accelerating_hypotheses": accelerating,
        "stable_hypotheses": stable,
        "recommended_hypothesis_id": recommended_hypothesis_id,
        "recommended_action": recommended_action,
        "status_headline": status_headline,
    }
    if phase_strength_signal is not None:
        summary["phase_strength_signal"] = phase_strength_signal
    if dominant_failure_mode is not None:
        summary["dominant_failure_mode"] = dominant_failure_mode
    if pending_promotion is not None:
        summary["pending_promotion_hypothesis_id"] = pending_promotion["challenger_id"]
        summary["pending_promotion_pressure_streak"] = pending_promotion["pressure_streak"]
        if pending_promotion["gate_blocker"] is not None:
            summary["pending_promotion_gate_blocker"] = pending_promotion["gate_blocker"]
    if promotion_ready is not None:
        summary["promotion_ready_hypothesis_id"] = promotion_ready["challenger_id"]
        if promotion_ready["pressure_streak"] > 0:
            summary["promotion_ready_pressure_streak"] = promotion_ready["pressure_streak"]
    recommended_hypothesis = next(
        (item for item in tracked_hypotheses if item.get("hypothesis_id") == recommended_hypothesis_id),
        None,
    )
    if recommended_hypothesis is not None and recommended_hypothesis.get("action_mode"):
        summary["recommended_action_mode"] = recommended_hypothesis["action_mode"]
    if recommended_hypothesis is not None:
        summary["recommended_trajectory_signal"] = _trajectory_signal_for(recommended_hypothesis)
        summary["recommendation_drivers"] = _build_recommendation_drivers(recommended_hypothesis)
    ranked_hypotheses = _annotate_suppressed_ranked_alternatives([
        _build_ranked_alternative(item, id_key="hypothesis_id")
        for item in sorted(
            (item for item in tracked_hypotheses if item.get("hypothesis_id")),
            key=lambda item: (
                0
                if item.get("evolution_phase") == "accelerating"
                else 1
                if item.get("evolution_phase") == "recovering"
                else 2
                if item.get("evolution_phase") == "stable"
                else 3,
                0
                if item.get("phase_strength") == "high"
                else 1
                if item.get("phase_strength") == "medium"
                else 2,
                item.get("hypothesis_id"),
            ),
        )
    ])
    previous_ranked_hypotheses = list(((hypotheses.get("hypothesis_evolution_summary") or {}).get("ranked_hypotheses") or []))
    summary["ranked_hypotheses"] = _annotate_frontier_age(
        ranked_hypotheses,
        previous_alternatives=previous_ranked_hypotheses,
        id_key="hypothesis_id",
    )
    return summary


def build_expansion_summary(
    *,
    backlog_summary: dict | None,
    backlog_evolution_summary: dict | None = None,
    hypothesis_summary: dict | None,
    hypothesis_evolution_summary: dict | None = None,
    previous_summary: dict | None = None,
) -> dict:
    backlog_summary = backlog_summary or {}
    backlog_evolution_summary = backlog_evolution_summary or {}
    hypothesis_summary = hypothesis_summary or {}
    hypothesis_evolution_summary = hypothesis_evolution_summary or {}
    previous_summary = previous_summary or {}

    backlog_summary_recommended_experiment_id = backlog_summary.get("recommended_anchor_experiment_id")
    backlog_evolution_recommended_experiment_id = backlog_evolution_summary.get("recommended_experiment_id")
    recommended_experiment_id = (
        backlog_evolution_recommended_experiment_id or backlog_summary_recommended_experiment_id
    )
    recommended_hypothesis_id = hypothesis_evolution_summary.get("recommended_hypothesis_id") or hypothesis_summary.get(
        "recommended_hypothesis_id"
    )
    backlog_failure_mode = backlog_evolution_summary.get("dominant_failure_mode")
    hypothesis_failure_mode = hypothesis_evolution_summary.get("dominant_failure_mode")
    backlog_phase_strength_signal = backlog_evolution_summary.get("phase_strength_signal")
    hypothesis_phase_strength_signal = hypothesis_evolution_summary.get("phase_strength_signal")
    backlog_action_mode = backlog_evolution_summary.get("recommended_action_mode")
    hypothesis_action_mode = hypothesis_evolution_summary.get("recommended_action_mode")
    backlog_pending_promotion_id = backlog_evolution_summary.get("pending_promotion_candidate_id")
    hypothesis_pending_promotion_id = hypothesis_evolution_summary.get("pending_promotion_hypothesis_id")
    backlog_promotion_ready_id = backlog_evolution_summary.get("promotion_ready_candidate_id")
    hypothesis_promotion_ready_id = hypothesis_evolution_summary.get("promotion_ready_hypothesis_id")
    pending_promotion_gate_blockers = sorted(
        {
            blocker
            for blocker in [
                backlog_evolution_summary.get("pending_promotion_gate_blocker"),
                hypothesis_evolution_summary.get("pending_promotion_gate_blocker"),
            ]
            if blocker is not None
        }
    )
    backlog_phase_signal = (
        "accelerating"
        if list(backlog_evolution_summary.get("accelerating_candidates") or [])
        else "recovering"
        if list(backlog_evolution_summary.get("recovery_candidates") or [])
        else "regressing"
        if list(backlog_evolution_summary.get("regressing_candidates") or [])
        else "stable"
        if list(backlog_evolution_summary.get("stable_candidates") or [])
        else None
    )
    hypothesis_phase_signal = (
        "accelerating"
        if list(hypothesis_evolution_summary.get("accelerating_hypotheses") or [])
        else "recovering"
        if list(hypothesis_evolution_summary.get("recovery_hypotheses") or [])
        else "regressing"
        if list(hypothesis_evolution_summary.get("regressing_hypotheses") or [])
        else "stable"
        if list(hypothesis_evolution_summary.get("stable_hypotheses") or [])
        else None
    )

    risk_flags: list[str] = []
    if list(backlog_summary.get("blocked_candidates") or []):
        risk_flags.append("blocked_backlog_candidates")
        if backlog_failure_mode:
            risk_flags.append(f"blocked_backlog_candidates:{backlog_failure_mode}")
    if list(hypothesis_summary.get("unstable_hypotheses") or []):
        risk_flags.append("unstable_hypotheses")
        if hypothesis_failure_mode:
            risk_flags.append(f"unstable_hypotheses:{hypothesis_failure_mode}")

    expansion_ready = bool(
        backlog_summary.get("selection_ready")
        and hypothesis_summary.get("selection_ready")
        and recommended_experiment_id is not None
        and recommended_hypothesis_id is not None
    )

    recovery_action_modes = {
        "recover_missing_artifacts",
        "reroute_for_stronger_evidence",
        "stabilize_execution",
        "recover_regressing_anchor",
        "stabilize_recovery",
    }
    growth_action_modes = {
        "scale_confident_anchor",
        "promote_emerging_anchor",
        "maintain_viable_anchor",
        "validate_low_confidence_anchor",
        "observe_insufficient_signal",
    }

    action_mode_alignment = None
    if backlog_action_mode and hypothesis_action_mode:
        if backlog_action_mode == hypothesis_action_mode:
            action_mode_alignment = "aligned"
        elif backlog_action_mode in recovery_action_modes and hypothesis_action_mode in recovery_action_modes:
            action_mode_alignment = "aligned"
        elif backlog_action_mode in growth_action_modes and hypothesis_action_mode in growth_action_modes:
            action_mode_alignment = "aligned"
        else:
            action_mode_alignment = "divergent"
    action_mode_divergence_memory = None
    if action_mode_alignment == "divergent" and backlog_action_mode and hypothesis_action_mode:
        previous_action_mode_divergence_memory = dict(previous_summary.get("action_mode_divergence_memory") or {})
        previous_backlog_action_mode = previous_action_mode_divergence_memory.get("backlog_action_mode")
        previous_hypothesis_action_mode = previous_action_mode_divergence_memory.get("hypothesis_action_mode")
        if (
            previous_summary.get("action_mode_alignment") == "divergent"
            and previous_backlog_action_mode == backlog_action_mode
            and previous_hypothesis_action_mode == hypothesis_action_mode
        ):
            divergence_streak = int(previous_action_mode_divergence_memory.get("divergence_streak", 0) or 0) + 1
        else:
            divergence_streak = 1
        action_mode_divergence_memory = {
            "backlog_action_mode": backlog_action_mode,
            "hypothesis_action_mode": hypothesis_action_mode,
            "divergence_streak": divergence_streak,
            "divergence_state": "persistent" if divergence_streak >= 2 else "new",
        }

    anchor_coherence = None
    recommended_anchor_hypothesis_links = list(backlog_summary.get("recommended_anchor_hypothesis_links") or [])
    if (
        recommended_hypothesis_id
        and recommended_anchor_hypothesis_links
        and backlog_summary_recommended_experiment_id is not None
        and recommended_hypothesis_id in recommended_anchor_hypothesis_links
        and backlog_summary_recommended_experiment_id != backlog_evolution_recommended_experiment_id
    ):
        recommended_experiment_id = backlog_summary_recommended_experiment_id
    if recommended_hypothesis_id and recommended_anchor_hypothesis_links:
        anchor_coherence = (
            "aligned"
            if recommended_hypothesis_id in recommended_anchor_hypothesis_links
            else "divergent"
        )
    anchor_divergence_memory = None
    if anchor_coherence == "divergent":
        expected_hypothesis_ids = list(recommended_anchor_hypothesis_links)
        selected_hypothesis_id = recommended_hypothesis_id
        previous_divergence_memory = dict(previous_summary.get("anchor_divergence_memory") or {})
        previous_expected_hypothesis_ids = list(previous_divergence_memory.get("expected_hypothesis_ids") or [])
        previous_selected_hypothesis_id = previous_divergence_memory.get("selected_hypothesis_id")
        if (
            previous_summary.get("anchor_coherence") == "divergent"
            and previous_expected_hypothesis_ids == expected_hypothesis_ids
            and previous_selected_hypothesis_id == selected_hypothesis_id
        ):
            divergence_streak = int(previous_divergence_memory.get("divergence_streak", 0) or 0) + 1
        else:
            divergence_streak = 1
        anchor_divergence_memory = {
            "expected_hypothesis_ids": expected_hypothesis_ids,
            "selected_hypothesis_id": selected_hypothesis_id,
            "divergence_streak": divergence_streak,
            "divergence_state": "persistent" if divergence_streak >= 2 else "new",
        }
    persistent_coordination_divergence = None
    if (
        (anchor_divergence_memory or {}).get("divergence_state") == "persistent"
        and (action_mode_divergence_memory or {}).get("divergence_state") == "persistent"
        and anchor_coherence == "divergent"
        and action_mode_alignment == "divergent"
    ):
        persistent_coordination_divergence = {
            "expected_hypothesis_ids": list(anchor_divergence_memory.get("expected_hypothesis_ids") or []),
            "selected_hypothesis_id": anchor_divergence_memory.get("selected_hypothesis_id"),
            "backlog_action_mode": action_mode_divergence_memory.get("backlog_action_mode"),
            "hypothesis_action_mode": action_mode_divergence_memory.get("hypothesis_action_mode"),
            "divergence_streak": min(
                int(anchor_divergence_memory.get("divergence_streak", 0) or 0),
                int(action_mode_divergence_memory.get("divergence_streak", 0) or 0),
            ),
            "divergence_state": "persistent",
        }
    persistent_joint_reserve_memory = None
    backlog_alternative_context = None
    hypothesis_ranked_alternative_context = None
    backlog_ranked_alternatives = list(backlog_evolution_summary.get("ranked_candidates") or [])
    hypothesis_ranked_alternatives = list(hypothesis_evolution_summary.get("ranked_hypotheses") or [])
    if len(backlog_ranked_alternatives) > 1:
        backlog_alternative_context = _build_alternative_context(
            backlog_ranked_alternatives[1],
            anchor_label="reserve anchor",
        )
    if len(hypothesis_ranked_alternatives) > 1:
        hypothesis_ranked_alternative_context = _build_alternative_context(
            hypothesis_ranked_alternatives[1],
            anchor_label="reserve hypothesis anchor",
        )
    backlog_reserve_hypothesis_links = list(
        (backlog_ranked_alternatives[1].get("hypothesis_links") if len(backlog_ranked_alternatives) > 1 else []) or []
    )
    backlog_reserve_experiment_id = (
        backlog_alternative_context.get("experiment_id") if backlog_alternative_context is not None else None
    )
    hypothesis_reserve_id = (
        hypothesis_ranked_alternative_context.get("hypothesis_id")
        if hypothesis_ranked_alternative_context is not None
        else None
    )
    if (
        backlog_reserve_experiment_id is not None
        and hypothesis_reserve_id is not None
        and hypothesis_reserve_id in backlog_reserve_hypothesis_links
        and backlog_alternative_context.get("frontier_age") == "persistent"
        and backlog_alternative_context.get("frontier_trend") == "rising"
        and hypothesis_ranked_alternative_context.get("frontier_age") == "persistent"
        and hypothesis_ranked_alternative_context.get("frontier_trend") == "rising"
    ):
        persistent_joint_reserve_memory = {
            "experiment_id": backlog_reserve_experiment_id,
            "hypothesis_id": hypothesis_reserve_id,
            "backlog_frontier_age": backlog_alternative_context.get("frontier_age"),
            "backlog_frontier_trend": backlog_alternative_context.get("frontier_trend"),
            "backlog_suppressed_by": backlog_alternative_context.get("suppressed_by"),
            "hypothesis_frontier_age": hypothesis_ranked_alternative_context.get("frontier_age"),
            "hypothesis_frontier_trend": hypothesis_ranked_alternative_context.get("frontier_trend"),
            "hypothesis_suppressed_by": hypothesis_ranked_alternative_context.get("suppressed_by"),
            "reserve_state": "persistent",
        }
    joint_pending_promotion_pair = None
    if backlog_pending_promotion_id is not None and hypothesis_pending_promotion_id is not None:
        pending_promotion_pressure_streak = min(
            int(backlog_evolution_summary.get("pending_promotion_pressure_streak", 0) or 0),
            int(hypothesis_evolution_summary.get("pending_promotion_pressure_streak", 0) or 0),
        )
        joint_pending_promotion_pair = {
            "experiment_id": backlog_pending_promotion_id,
            "hypothesis_id": hypothesis_pending_promotion_id,
            "gate_blockers": pending_promotion_gate_blockers,
        }
        if pending_promotion_pressure_streak > 0:
            joint_pending_promotion_pair["pressure_streak"] = pending_promotion_pressure_streak
            joint_pending_promotion_pair["pending_state"] = (
                "persistent" if pending_promotion_pressure_streak >= 2 else "new"
            )
    joint_recovery_pair = None
    if (
        recommended_experiment_id is not None
        and recommended_hypothesis_id is not None
        and backlog_evolution_summary.get("recommended_action") == "recover_regressing_candidate"
        and hypothesis_evolution_summary.get("recommended_action") == "stabilize_regressing_hypothesis"
        and backlog_failure_mode == "scientific_validity"
        and hypothesis_failure_mode == "scientific_validity"
        and recommended_hypothesis_id in recommended_anchor_hypothesis_links
    ):
        recovery_streak = min(
            _recovery_streak_from_summary(backlog_evolution_summary),
            _recovery_streak_from_summary(hypothesis_evolution_summary),
        )
        recovery_state = (
            "new"
            if backlog_evolution_summary.get("recommended_trajectory_signal") == "newly_recovering"
            or hypothesis_evolution_summary.get("recommended_trajectory_signal") == "newly_recovering"
            else "persistent"
        )
        joint_recovery_pair = {
            "experiment_id": recommended_experiment_id,
            "hypothesis_id": recommended_hypothesis_id,
            "failure_mode": "scientific_validity",
            "recovery_state": recovery_state,
        }
        if recovery_streak > 0:
            joint_recovery_pair["recovery_streak"] = recovery_streak
    joint_promotion_ready_pair = None
    if (
        backlog_promotion_ready_id is not None
        and hypothesis_promotion_ready_id is not None
        and hypothesis_promotion_ready_id in recommended_anchor_hypothesis_links
    ):
        promotion_ready_pressure_streak = min(
            int(backlog_evolution_summary.get("promotion_ready_pressure_streak", 0) or 0),
            int(hypothesis_evolution_summary.get("promotion_ready_pressure_streak", 0) or 0),
        )
        joint_promotion_ready_pair = {
            "experiment_id": backlog_promotion_ready_id,
            "hypothesis_id": hypothesis_promotion_ready_id,
        }
        if promotion_ready_pressure_streak > 0:
            joint_promotion_ready_pair["pressure_streak"] = promotion_ready_pressure_streak
            joint_promotion_ready_pair["readiness_state"] = (
                "persistent" if promotion_ready_pressure_streak >= 2 else "new"
            )

    if not expansion_ready:
        next_expansion_action = "insufficient_anchors"
        status_headline = "The campaign has not established reusable backlog or hypothesis anchors yet."
    elif backlog_promotion_ready_id is not None or hypothesis_promotion_ready_id is not None:
        if (joint_promotion_ready_pair or {}).get("readiness_state") == "persistent":
            next_expansion_action = "advance_persistent_promotion_ready_pair"
            status_headline = (
                "The campaign has a persistently gate-cleared challenger pair and should advance that promotion path before broader expansion."
            )
        else:
            next_expansion_action = "promote_ready_challengers"
            status_headline = (
                "The campaign has a rising challenger that has cleared the promotion gate and should now be promoted over the decaying incumbent."
            )
    elif joint_pending_promotion_pair is not None:
        if joint_pending_promotion_pair.get("pending_state") == "persistent":
            next_expansion_action = "resolve_persistent_pending_promotion_pair"
            status_headline = (
                "The campaign has a persistently blocked challenger pair and should resolve that stalled promotion path before broader expansion."
            )
        else:
            next_expansion_action = "investigate_pending_promotion_pair"
            status_headline = (
                "The campaign has a blocked challenger pair that should be investigated together before broader expansion."
            )
    elif backlog_pending_promotion_id is not None or hypothesis_pending_promotion_id is not None:
        next_expansion_action = "investigate_pending_promotions"
        status_headline = (
            "The campaign has rising challenger anchors that remain blocked from promotion and should investigate those blockers before broader expansion."
        )
    elif joint_recovery_pair is not None:
        if joint_recovery_pair.get("recovery_state") == "persistent":
            next_expansion_action = "stabilize_persistent_joint_recovery_pair"
            status_headline = (
                "The campaign has a persistently aligned recovery pair and should stabilize that recovery path before broader expansion."
            )
        else:
            next_expansion_action = "preserve_joint_recovery_pair"
            status_headline = (
                "The campaign has an aligned recovery pair that should be preserved together before broader expansion."
            )
    elif persistent_coordination_divergence is not None:
        next_expansion_action = "resolve_persistent_coordination_divergence"
        status_headline = (
            "The campaign has a persistently unresolved coordination divergence across anchor coherence and action modes and should resolve it before broader expansion."
        )
    elif persistent_joint_reserve_memory is not None:
        next_expansion_action = "resolve_persistent_joint_reserve_memory"
        status_headline = (
            "The campaign has a persistent joint reserve memory and should resolve that rising reserve pair before broader expansion."
        )
    elif anchor_coherence == "divergent":
        if (anchor_divergence_memory or {}).get("divergence_state") == "persistent":
            next_expansion_action = "resolve_persistent_anchor_divergence"
            status_headline = (
                "The recommended backlog anchor and hypothesis anchor have diverged persistently and should be resolved before broader expansion."
            )
        else:
            next_expansion_action = "reconcile_anchor_signals"
            status_headline = (
                "The recommended backlog anchor and hypothesis anchor should be reconciled before broader expansion."
            )
    elif action_mode_alignment == "divergent":
        if (action_mode_divergence_memory or {}).get("divergence_state") == "persistent":
            next_expansion_action = "resolve_persistent_action_mode_divergence"
            status_headline = (
                "The campaign has reusable anchors, but backlog and hypothesis action modes have diverged persistently and should be resolved before broader expansion."
            )
        else:
            next_expansion_action = "reconcile_anchor_signals"
            status_headline = (
                "The campaign has reusable anchors, but backlog and hypothesis action modes should be reconciled before broader expansion."
            )
    elif "unstable_hypotheses" in risk_flags:
        if hypothesis_failure_mode == "scientific_validity":
            next_expansion_action = "stabilize_hypotheses_scientific_validity"
            status_headline = (
                "The campaign has reusable anchors, but unstable hypotheses still need stronger scientific validity."
            )
        elif hypothesis_failure_mode == "artifact_presence":
            next_expansion_action = "stabilize_hypotheses_artifact_gap"
            status_headline = (
                "The campaign has reusable anchors, but unstable hypotheses still need stronger artifact support."
            )
        elif hypothesis_failure_mode == "worker_execution":
            next_expansion_action = "stabilize_hypotheses_execution"
            status_headline = (
                "The campaign has reusable anchors, but unstable hypotheses still need more reliable execution."
            )
        else:
            next_expansion_action = "stabilize_hypotheses"
            status_headline = "The campaign has reusable anchors, but unstable hypotheses still need stabilization."
    elif "blocked_backlog_candidates" in risk_flags:
        if backlog_failure_mode == "scientific_validity":
            next_expansion_action = "unblock_backlog_candidates_scientific_validity"
            status_headline = (
                "The campaign has reusable anchors, but blocked backlog candidates still need stronger scientific validity."
            )
        elif backlog_failure_mode == "artifact_presence":
            next_expansion_action = "unblock_backlog_candidates_artifact_gap"
            status_headline = (
                "The campaign has reusable anchors, but blocked backlog candidates still need stronger artifact support."
            )
        elif backlog_failure_mode == "worker_execution":
            next_expansion_action = "unblock_backlog_candidates_execution"
            status_headline = (
                "The campaign has reusable anchors, but blocked backlog candidates still need more reliable execution."
            )
        else:
            next_expansion_action = "unblock_backlog_candidates"
            status_headline = "The campaign has reusable anchors, but blocked backlog candidates still need recovery."
    elif backlog_phase_strength_signal == "high" or hypothesis_phase_strength_signal == "high":
        next_expansion_action = "promote_high_confidence_anchor"
        status_headline = "The campaign has a high-confidence anchor that is ready to promote."
    elif backlog_phase_strength_signal == "low" and hypothesis_phase_strength_signal == "low":
        next_expansion_action = "validate_low_confidence_anchor"
        status_headline = "The campaign has only low-confidence anchors and should validate them before broader expansion."
    else:
        next_expansion_action = "promote_recommended_anchor"
        status_headline = "The campaign has a promising backlog anchor and a supported hypothesis anchor."

    summary = {
        "expansion_ready": expansion_ready,
        "recommended_experiment_id": recommended_experiment_id,
        "recommended_hypothesis_id": recommended_hypothesis_id,
        "risk_flags": risk_flags,
        "next_expansion_action": next_expansion_action,
        "status_headline": status_headline,
        "recommended_backlog_action": backlog_evolution_summary.get("recommended_action", "insufficient_backlog_signal"),
        "recommended_hypothesis_action": hypothesis_evolution_summary.get(
            "recommended_action", "insufficient_hypothesis_signal"
        ),
    }
    if backlog_evolution_summary.get("recommended_action_mode") is not None:
        summary["recommended_backlog_action_mode"] = backlog_evolution_summary["recommended_action_mode"]
    if hypothesis_evolution_summary.get("recommended_action_mode") is not None:
        summary["recommended_hypothesis_action_mode"] = hypothesis_evolution_summary["recommended_action_mode"]
    if backlog_pending_promotion_id is not None:
        summary["pending_promotion_candidate_id"] = backlog_pending_promotion_id
    if hypothesis_pending_promotion_id is not None:
        summary["pending_promotion_hypothesis_id"] = hypothesis_pending_promotion_id
    if pending_promotion_gate_blockers:
        summary["pending_promotion_gate_blockers"] = pending_promotion_gate_blockers
    if joint_pending_promotion_pair is not None:
        summary["joint_pending_promotion_pair"] = joint_pending_promotion_pair
    if backlog_promotion_ready_id is not None:
        summary["promotion_ready_candidate_id"] = backlog_promotion_ready_id
    if hypothesis_promotion_ready_id is not None:
        summary["promotion_ready_hypothesis_id"] = hypothesis_promotion_ready_id
    if joint_promotion_ready_pair is not None:
        summary["joint_promotion_ready_pair"] = joint_promotion_ready_pair
    if joint_recovery_pair is not None:
        summary["joint_recovery_pair"] = joint_recovery_pair
    if backlog_evolution_summary.get("recommendation_drivers") is not None:
        summary["backlog_recommendation_drivers"] = backlog_evolution_summary["recommendation_drivers"]
    if hypothesis_evolution_summary.get("recommendation_drivers") is not None:
        summary["hypothesis_recommendation_drivers"] = hypothesis_evolution_summary["recommendation_drivers"]
    selection_context = backlog_summary.get("recommended_anchor_selection_context")
    if selection_context is not None:
        summary["backlog_selection_context"] = selection_context
    hypothesis_selection_context = hypothesis_summary.get("recommended_hypothesis_selection_context")
    if hypothesis_selection_context is not None:
        summary["hypothesis_selection_context"] = hypothesis_selection_context
    hypothesis_ranked_active_alternatives = list(hypothesis_summary.get("ranked_active_hypotheses") or [])
    if hypothesis_ranked_active_alternatives:
        summary["hypothesis_ranked_active_alternatives"] = hypothesis_ranked_active_alternatives[:3]
    hypothesis_active_alternative_context = hypothesis_summary.get("active_alternative_context")
    if hypothesis_active_alternative_context is not None:
        summary["hypothesis_active_alternative_context"] = hypothesis_active_alternative_context
    if backlog_ranked_alternatives:
        summary["backlog_ranked_alternatives"] = backlog_ranked_alternatives[:3]
        if backlog_alternative_context is not None:
            summary["backlog_alternative_context"] = backlog_alternative_context
    if hypothesis_ranked_alternatives:
        summary["hypothesis_ranked_alternatives"] = hypothesis_ranked_alternatives[:3]
        if hypothesis_ranked_alternative_context is not None:
            summary["hypothesis_alternative_context"] = hypothesis_ranked_alternative_context
    if action_mode_alignment is not None:
        summary["action_mode_alignment"] = action_mode_alignment
    if action_mode_divergence_memory is not None:
        summary["action_mode_divergence_memory"] = action_mode_divergence_memory
    if anchor_coherence is not None:
        summary["anchor_coherence"] = anchor_coherence
    if anchor_coherence == "divergent":
        summary["anchor_coherence_expected_hypothesis_ids"] = recommended_anchor_hypothesis_links
        summary["anchor_coherence_selected_hypothesis_id"] = recommended_hypothesis_id
    if anchor_divergence_memory is not None:
        summary["anchor_divergence_memory"] = anchor_divergence_memory
    if persistent_coordination_divergence is not None:
        summary["persistent_coordination_divergence"] = persistent_coordination_divergence
    if persistent_joint_reserve_memory is not None:
        summary["persistent_joint_reserve_memory"] = persistent_joint_reserve_memory
    if backlog_phase_signal is not None:
        summary["backlog_phase_signal"] = backlog_phase_signal
    if hypothesis_phase_signal is not None:
        summary["hypothesis_phase_signal"] = hypothesis_phase_signal
    if backlog_phase_strength_signal is not None:
        summary["backlog_phase_strength_signal"] = backlog_phase_strength_signal
    if hypothesis_phase_strength_signal is not None:
        summary["hypothesis_phase_strength_signal"] = hypothesis_phase_strength_signal
    if backlog_failure_mode is not None:
        summary["backlog_dominant_failure_mode"] = backlog_failure_mode
    if hypothesis_failure_mode is not None:
        summary["hypothesis_dominant_failure_mode"] = hypothesis_failure_mode
    return summary


def build_status_snapshot(*, campaign_dir: str | None, state: dict | None, latest_iteration: dict | None = None) -> dict:
    state = state or {}
    payload: dict = {
        "service": "autonomous_research_campaign",
        "status": "ready",
    }
    if campaign_dir is None:
        return payload

    payload.update(
        {
            "campaign_dir": campaign_dir,
            "campaign_id": state.get("campaign_id"),
            "iterations_run": int(state.get("iterations_run", 0)),
            "campaign_lifecycle": state.get("campaign_lifecycle"),
            "campaign_summary": state.get("campaign_summary"),
            "expansion_summary": state.get("expansion_summary"),
            "backlog_summary": state.get("backlog_summary"),
            "backlog_evolution_summary": state.get("backlog_evolution_summary"),
            "hypothesis_summary": state.get("hypothesis_summary"),
            "hypothesis_evolution_summary": state.get("hypothesis_evolution_summary"),
            "memory_summary": state.get("memory_summary"),
            "continuation_anchor": state.get("continuation_anchor"),
            "resume_assessment": state.get("resume_assessment"),
        }
    )
    if latest_iteration is not None:
        payload["latest_round"] = {
            "iteration": latest_iteration.get("iteration"),
            "objective": latest_iteration.get("objective"),
            "decision": latest_iteration.get("decision"),
            "task_results": latest_iteration.get("task_results"),
            "worker_result": latest_iteration.get("worker_result"),
            "artifacts": latest_iteration.get("artifacts"),
            "verification": latest_iteration.get("verification"),
            "task_intent": latest_iteration.get("task_intent"),
            "brain_plan": latest_iteration.get("brain_plan"),
            "governance": latest_iteration.get("governance"),
            "round_summary": latest_iteration.get("round_summary"),
            "operator_summary": latest_iteration.get("operator_summary"),
        }
    return payload


def build_campaign_memory(
    *,
    decision: str,
    objective: str | None,
    worker_result: dict | None,
    artifacts: dict | None,
    verification: dict | None,
    previous_memory: dict | None,
) -> dict:
    verification_status = (verification or {}).get("status")
    if verification_status != "accept":
        return previous_memory or {
            "latest_accepted_objective": objective,
            "latest_accepted_summary": None,
            "latest_accepted_artifacts": [],
            "latest_accepted_iteration_outcome": None,
        }

    artifact_paths = list((artifacts or {}).get("deliverable_paths") or [])
    if not artifact_paths:
        artifact_paths = list((worker_result or {}).get("deliverable_paths") or [])

    return {
        "latest_accepted_objective": objective,
        "latest_accepted_summary": (worker_result or {}).get("summary"),
        "latest_accepted_artifacts": artifact_paths,
        "latest_accepted_iteration_outcome": verification_status,
    }


def build_campaign_memory_summary(memory: dict | None) -> dict:
    memory = memory or {}
    artifacts = list(memory.get("latest_accepted_artifacts") or [])
    preferred_artifact = None
    if "result_note.md" in artifacts:
        preferred_artifact = "result_note.md"
    elif artifacts:
        preferred_artifact = artifacts[0]

    accepted_memory_ready = bool(
        memory.get("latest_accepted_iteration_outcome") == "accept" and preferred_artifact is not None
    )

    return {
        "preferred_artifact": preferred_artifact,
        "evidence_summary": memory.get("latest_accepted_summary"),
        "accepted_memory_ready": accepted_memory_ready,
    }


def build_continuation_anchor(*, memory: dict | None, memory_summary: dict | None) -> dict:
    memory = memory or {}
    memory_summary = memory_summary or {}
    return {
        "anchor_artifact": memory_summary.get("preferred_artifact"),
        "anchor_objective": memory.get("latest_accepted_objective"),
        "anchor_summary": memory_summary.get("evidence_summary"),
        "anchor_ready": bool(memory_summary.get("accepted_memory_ready")),
    }


def build_campaign_summary(
    *,
    research_question: str | None,
    iteration_number: int,
    operator_summary: dict | None,
    verification: dict | None,
    resume_metadata: dict | None,
    resume_assessment: dict,
) -> dict:
    round_label = "round" if iteration_number == 1 else "rounds"
    failed_check_types = list((verification or {}).get("failed_check_types") or [])
    summary = {
        "research_question": research_question,
        "status_headline": (
            f"The campaign has completed {iteration_number} {round_label} for the current research question."
        ),
        "latest_outcome": (operator_summary or {}).get("outcome", "pending_review"),
        "next_step": (operator_summary or {}).get(
            "next_step",
            "Review the round outcome and decide the next campaign action.",
        ),
        "latest_failed_check_types": failed_check_types,
        "blocking_issue": _derive_blocking_issue(verification),
        "resume_ready": resume_assessment["resume_ready"],
        "resume_reasons": resume_assessment["reasons"],
    }
    if resume_metadata and resume_metadata.get("requested"):
        summary["resumed_from_iteration"] = resume_metadata.get("source_iteration")
    return summary



def build_round_summary(*, decision: str, task_intent: dict | None, verification: dict | None, brain_plan) -> dict:
    verification_status = None
    if verification is not None:
        verification_status = verification.get("status")

    next_action_reason = None
    if brain_plan is not None:
        if isinstance(brain_plan, dict):
            next_action_reason = brain_plan.get("reason")
        else:
            next_action_reason = getattr(brain_plan, "reason", None)

    return {
        "decision": decision,
        "task_type": (task_intent or {}).get("task_type"),
        "acceptance_emphasis": (task_intent or {}).get("acceptance_emphasis"),
        "verification_status": verification_status,
        "next_action_reason": next_action_reason,
    }


def build_operator_summary(*, task_intent: dict | None, verification: dict | None) -> dict:
    task_type = (task_intent or {}).get("task_type")
    acceptance_emphasis = (task_intent or {}).get("acceptance_emphasis")
    verification_status = (verification or {}).get("status")
    failed_check_types = set((verification or {}).get("failed_check_types") or [])

    if task_type == "analysis":
        headline = "Review the previous successful output through an analysis step."
    elif task_type == "repair":
        headline = "Repair the previous attempt before continuing the campaign."
    else:
        headline = "Run a code-and-run step for the current research question."

    if verification_status == "accept":
        outcome = "accepted"
        why = "The round satisfied its verification checks."
        next_step = "Continue execution from the current objective or successful outputs."
    elif "scientific_validity" in failed_check_types:
        outcome = "needs_refinement"
        why = "The round needs stronger scientific explanation before it can be accepted."
        next_step = "Refine the previous attempt with stronger evidence, explanation, or method quality."
    elif "artifact_presence" in failed_check_types:
        outcome = "needs_refinement"
        why = "The round is missing one or more required deliverables."
        next_step = "Refine the previous attempt and recover the missing artifacts."
    elif "worker_execution" in failed_check_types:
        outcome = "needs_refinement"
        why = "The round did not complete successfully enough to trust the result."
        next_step = "Refine the previous attempt and stabilize worker execution."
    elif verification_status == "rework":
        outcome = "needs_refinement"
        why = "The round did not satisfy its verification checks."
        next_step = "Refine the previous attempt using the recorded failures and warnings."
    elif verification_status is None and acceptance_emphasis == "scientific_validity":
        outcome = "pending_review"
        why = "The round has not produced a verification result yet."
        next_step = "Review the analysis output and decide whether to continue, refine, hold, or escalate."
    else:
        outcome = "pending_review"
        why = "The round has not produced a verification result yet."
        next_step = "Review the round outcome and decide the next campaign action."

    return {
        "headline": headline,
        "outcome": outcome,
        "why": why,
        "next_step": next_step,
    }
