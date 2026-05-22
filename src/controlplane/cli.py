from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import typer
from typer import BadParameter
import yaml

from controlplane.brain.decomposer import decompose_experiment
from controlplane.brain.objective_evolver import plan_next_iteration
from controlplane.brain.objective_evolver import plan_next_iteration_with_candidate_transition
from controlplane.brain.planner import score_candidate, select_next_experiment
from controlplane.brain.task_intent import derive_task_intent
from controlplane.dispatcher.router import resolve_launcher_for_task
from controlplane.governor.decisions import make_governance_decision
from controlplane.orchestrator.campaign_loop import run_campaign_loop
from controlplane.orchestrator.iteration_loop import run_iteration
from controlplane.state import campaign_state
from controlplane.verifier.completion_judge import verify_completion
from controlplane.governor.presets import build_policy_for_mode
from controlplane.schemas.experiment_brief import ExperimentBrief


app = typer.Typer(help="Multi-agent autonomous research control plane")


@app.command()
def status(campaign_dir: str | None = typer.Argument(None)) -> None:
    payload: dict
    if campaign_dir is None:
        payload = campaign_state.build_status_snapshot(campaign_dir=None, state=None, latest_iteration=None)
    else:
        target = Path(campaign_dir)
        state = _load_state(target)
        if "campaign_id" not in state:
            state["campaign_id"] = target.name
        payload = campaign_state.build_status_snapshot(
            campaign_dir=str(target),
            state=state,
            latest_iteration=_load_latest_iteration(target),
        )
    typer.echo(json.dumps(payload))


@app.command()
def init(path: str, question: str = typer.Option(..., "--question")) -> None:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    (target / "campaign_spec.md").write_text(f"# Research Question\n\n{question}\n", encoding="utf-8")
    initial_resume_assessment = campaign_state.assess_resume_readiness(None)
    initial_campaign_memory = campaign_state.build_campaign_memory(
        decision="INIT",
        objective=None,
        worker_result=None,
        artifacts=None,
        verification=None,
        previous_memory=None,
    )
    initial_memory_summary = campaign_state.build_campaign_memory_summary(initial_campaign_memory)
    initial_campaign_backlog = campaign_state.build_campaign_backlog(
        previous_backlog=None,
        selected_candidate=None,
        backlog_source=None,
        candidate_count=None,
        iteration_number=0,
        verification=None,
    )
    initial_campaign_hypotheses = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=None,
        hypothesis_links=None,
        verification=None,
        iteration_number=0,
    )
    initial_backlog_evolution_summary = campaign_state.build_backlog_evolution_summary(initial_campaign_backlog)
    initial_hypothesis_evolution_summary = campaign_state.build_hypothesis_evolution_summary(initial_campaign_hypotheses)
    (target / "campaign_state.json").write_text(
        json.dumps(
            {
                "campaign_id": target.name,
                "status": "active",
                "iterations_run": 0,
                "campaign_summary": campaign_state.build_campaign_summary(
                    research_question=question,
                    iteration_number=0,
                    operator_summary=None,
                    verification=None,
                    resume_metadata=None,
                    resume_assessment=initial_resume_assessment,
                ),
                "campaign_memory": initial_campaign_memory,
                "memory_summary": initial_memory_summary,
                "continuation_anchor": campaign_state.build_continuation_anchor(
                    memory=initial_campaign_memory,
                    memory_summary=initial_memory_summary,
                ),
                "campaign_backlog": initial_campaign_backlog,
                "backlog_summary": campaign_state.build_backlog_summary(initial_campaign_backlog),
                "backlog_evolution_summary": initial_backlog_evolution_summary,
                "campaign_hypotheses": initial_campaign_hypotheses,
                "hypothesis_summary": campaign_state.build_hypothesis_summary(initial_campaign_hypotheses),
                "hypothesis_evolution_summary": initial_hypothesis_evolution_summary,
                "expansion_summary": campaign_state.build_expansion_summary(
                    backlog_summary=campaign_state.build_backlog_summary(initial_campaign_backlog),
                    backlog_evolution_summary=initial_backlog_evolution_summary,
                    hypothesis_summary=campaign_state.build_hypothesis_summary(initial_campaign_hypotheses),
                    hypothesis_evolution_summary=initial_hypothesis_evolution_summary,
                ),
                "resume_assessment": initial_resume_assessment,
                "campaign_lifecycle": "not_started",
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (target / "governor_policy.yaml").write_text(
        yaml.safe_dump({"mode": "moderate_autonomy"}, sort_keys=False),
        encoding="utf-8",
    )
    (target / "worker_registry.yaml").write_text(
        yaml.safe_dump({"workers": []}, sort_keys=False),
        encoding="utf-8",
    )
    typer.echo(f"Initialized campaign at {target}")


def _read_question(campaign_dir: Path) -> str:
    spec_path = campaign_dir / "campaign_spec.md"
    if not spec_path.exists():
        return "Unknown research question"
    text = spec_path.read_text(encoding="utf-8").strip().splitlines()
    non_empty = [line.strip() for line in text if line.strip() and not line.startswith("#")]
    return non_empty[0] if non_empty else "Unknown research question"


def _load_state(campaign_dir: Path) -> dict:
    state_path = campaign_dir / "campaign_state.json"
    if not state_path.exists():
        return {"campaign_id": campaign_dir.name, "status": "active", "iterations_run": 0}
    return json.loads(state_path.read_text(encoding="utf-8"))


def _load_worker_registry(campaign_dir: Path) -> list[dict] | None:
    registry_path = campaign_dir / "worker_registry.yaml"
    if not registry_path.exists():
        return None
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    workers = payload.get("workers")
    return workers if isinstance(workers, list) else None


def _build_governor_state(campaign_state_record: dict) -> dict:
    iterations_run = int(campaign_state_record.get("iterations_run", 0))
    if "failure_streak" in campaign_state_record:
        failure_streak = int(campaign_state_record.get("failure_streak", 0))
    else:
        last_decision = campaign_state_record.get("last_decision")
        failure_streak = 1 if last_decision == "REFINE" else 0
    return {
        "budget_status": {"experiments_run": iterations_run},
        "failure_status": {"failure_streak": failure_streak},
    }


def _load_latest_iteration(campaign_dir: Path) -> dict | None:
    latest_path = campaign_dir / "latest_iteration.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))


def _validate_resume_record(last_record: dict) -> None:
    assessment = campaign_state.assess_resume_readiness(last_record)
    if assessment["resume_ready"]:
        return

    field_map = {
        "missing_decision": "decision",
        "missing_verification": "verification",
    }
    missing = ", ".join(field_map[reason] for reason in assessment["reasons"])
    raise BadParameter(
        "--resume requires latest_iteration.json to include planning signals: "
        f"missing {missing}."
    )


def _load_resume_record(campaign_dir: Path, *, resume: bool) -> dict | None:
    if not resume:
        return None
    last_record = _load_latest_iteration(campaign_dir)
    if last_record is None:
        raise BadParameter("--resume requires an existing latest_iteration.json in the campaign directory.")
    _validate_resume_record(last_record)
    return last_record


def _select_objective(base_objective: str, backlog_file: str | None) -> str:
    if not backlog_file:
        return base_objective

    backlog = json.loads(Path(backlog_file).read_text(encoding="utf-8"))
    selected = select_next_experiment(backlog)
    return selected.get("objective", base_objective)


def _build_hypothesis_index(hypothesis_state: dict | None) -> dict[str, dict]:
    tracked = list((hypothesis_state or {}).get("tracked_hypotheses") or [])
    return {
        item["hypothesis_id"]: dict(item)
        for item in tracked
        if item.get("hypothesis_id")
    }


def _score_linked_hypotheses(candidate: dict, hypothesis_index: dict[str, dict]) -> float:
    linked_hypotheses = [
        hypothesis_index[hypothesis_id]
        for hypothesis_id in list(candidate.get("hypothesis_links") or [])
        if hypothesis_id in hypothesis_index
    ]
    if not linked_hypotheses:
        return 0.0

    def failure_mode_bonus(item: dict) -> float:
        dominant_failure_mode = item.get("dominant_failure_mode")
        if dominant_failure_mode == "artifact_presence":
            return 0.03
        if dominant_failure_mode == "worker_execution":
            return -0.02
        if dominant_failure_mode == "scientific_validity":
            return -0.04
        return 0.0

    def phase_bonus(item: dict) -> float:
        evolution_phase = item.get("evolution_phase")
        phase_strength = item.get("phase_strength")
        strength_bonus = (
            0.03
            if phase_strength == "high"
            else 0.015
            if phase_strength == "medium"
            else 0.0
        )
        if evolution_phase == "accelerating":
            return 0.05 + strength_bonus
        if evolution_phase == "recovering":
            return 0.02 + strength_bonus
        if evolution_phase == "regressing":
            return -0.06 - strength_bonus
        return 0.0

    def trajectory_bonus(item: dict) -> float:
        trajectory_signal = item.get("trajectory_signal")
        if trajectory_signal == "newly_recovering":
            return 0.05
        if trajectory_signal == "strong_recovery":
            return 0.04
        if trajectory_signal == "continuing_recovery":
            return 0.02
        if trajectory_signal == "strong_acceleration":
            return 0.03
        if trajectory_signal == "newly_accelerating":
            return 0.02
        if trajectory_signal == "stale_stable":
            return -0.02
        if trajectory_signal == "deep_regression":
            return -0.04
        if trajectory_signal == "continuing_regression":
            return -0.03
        return 0.0

    def action_mode_bonus(item: dict) -> float:
        action_mode = item.get("action_mode")
        if action_mode == "scale_confident_anchor":
            return 0.06
        if action_mode == "promote_emerging_anchor":
            return 0.04
        if action_mode == "maintain_viable_anchor":
            return 0.02
        if action_mode == "validate_low_confidence_anchor":
            return -0.01
        if action_mode == "stabilize_recovery":
            return 0.01
        if action_mode == "recover_missing_artifacts":
            return 0.02
        if action_mode == "reroute_for_stronger_evidence":
            return -0.05
        if action_mode == "stabilize_execution":
            return -0.03
        if action_mode == "recover_regressing_anchor":
            return -0.04
        return 0.0

    return sum(
        (
            0.08
            if item.get("status") == "supported"
            else -0.08
            if item.get("status") == "unstable"
            else 0.0
        )
        + 0.03 * int(item.get("accept_count", 0) or 0)
        - 0.04 * int(item.get("rework_count", 0) or 0)
        + 0.04 * int(item.get("current_accept_streak", 0) or 0)
        - 0.05 * int(item.get("current_rework_streak", 0) or 0)
        + (0.005 * int(item.get("last_accept_iteration"))) if item.get("last_accept_iteration") is not None else 0.0
        + failure_mode_bonus(item)
        + phase_bonus(item)
        + trajectory_bonus(item)
        + action_mode_bonus(item)
        for item in linked_hypotheses
    ) / len(linked_hypotheses)


def _score_hypothesis_frontier_pressure(candidate: dict, hypothesis_state: dict | None) -> float:
    frontier_history = list((hypothesis_state or {}).get("frontier_history") or [])
    if not frontier_history:
        return 0.0

    latest_frontier = frontier_history[-1]
    ranked_ids = list(latest_frontier.get("ranked_ids") or [])
    if len(ranked_ids) < 2:
        return 0.0

    linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
    leader_id = latest_frontier.get("recommended_id")
    challenger_id = ranked_ids[1]
    pressure = (latest_frontier.get("pressure_snapshot") or {}).get("challenger_pressure")
    leader_tenure = (latest_frontier.get("pressure_snapshot") or {}).get("leader_tenure")

    if pressure != "rising":
        return 0.0
    if challenger_id in linked_hypothesis_ids:
        return 0.05
    if leader_id in linked_hypothesis_ids and leader_tenure == "sustained":
        return -0.02
    return 0.0


def _evaluate_promotion_gate(
    leader: dict | None,
    challenger: dict | None,
    *,
    pressure: str | None,
    leader_tenure: str | None,
) -> dict:
    used_gate = bool(pressure == "rising" and leader_tenure == "sustained" and leader and challenger)
    if not used_gate:
        return {
            "used_promotion_gate": False,
            "promotion_gate_passed": None,
            "promotion_gate_blocker": None,
        }

    challenger_last_outcome = challenger.get("last_outcome")
    challenger_rework_streak = int(challenger.get("current_rework_streak", 0) or 0)
    if challenger_last_outcome == "rework" or challenger_rework_streak > 0:
        return {
            "used_promotion_gate": True,
            "promotion_gate_passed": False,
            "promotion_gate_blocker": "challenger_recent_rework",
        }

    challenger_accept_count = int(challenger.get("accept_count", 0) or 0)
    leader_accept_count = int((leader or {}).get("accept_count", 0) or 0)
    challenger_accept_streak = int(challenger.get("current_accept_streak", 0) or 0)
    leader_accept_streak = int((leader or {}).get("current_accept_streak", 0) or 0)
    leader_phase = (leader or {}).get("evolution_phase")
    challenger_phase = challenger.get("evolution_phase")
    challenger_phase_strength = challenger.get("phase_strength")
    challenger_trajectory_signal = challenger.get("trajectory_signal")
    challenger_has_momentum_override = (
        leader_phase == "regressing"
        and challenger_phase in {"accelerating", "recovering"}
        and (
            challenger_phase_strength == "high"
            or challenger_trajectory_signal in {"strong_acceleration", "strong_recovery", "newly_recovering"}
        )
    )
    if challenger_accept_count < leader_accept_count and challenger_accept_streak < leader_accept_streak:
        if challenger_has_momentum_override:
            return {
                "used_promotion_gate": True,
                "promotion_gate_passed": True,
                "promotion_gate_blocker": None,
            }
        return {
            "used_promotion_gate": True,
            "promotion_gate_passed": False,
            "promotion_gate_blocker": "challenger_weaker_acceptance",
        }

    return {
        "used_promotion_gate": True,
        "promotion_gate_passed": True,
        "promotion_gate_blocker": None,
    }


def _select_hypothesis_links(
    hypothesis_state: dict | None,
    fallback_links: list[str] | None,
    backlog_state: dict | None = None,
    backlog_evolution_summary: dict | None = None,
    expansion_summary: dict | None = None,
) -> tuple[list[str], str, bool, dict]:
    fallback = list(fallback_links or [])
    tracked_hypotheses = list((hypothesis_state or {}).get("tracked_hypotheses") or [])
    frontier_history = list((hypothesis_state or {}).get("frontier_history") or [])
    if not tracked_hypotheses:
        return fallback, "selected_candidate_projection", False, {
            "used_promotion_gate": False,
            "promotion_gate_passed": None,
            "promotion_gate_blocker": None,
        }

    latest_frontier = frontier_history[-1] if frontier_history else {}
    pressure = (latest_frontier.get("pressure_snapshot") or {}).get("challenger_pressure")
    leader_tenure = (latest_frontier.get("pressure_snapshot") or {}).get("leader_tenure")
    ranked_ids = list(latest_frontier.get("ranked_ids") or [])
    challenger_id = ranked_ids[1] if len(ranked_ids) > 1 else None
    leader_id = latest_frontier.get("recommended_id")
    leader = next((item for item in tracked_hypotheses if item.get("hypothesis_id") == leader_id), None)
    challenger = next((item for item in tracked_hypotheses if item.get("hypothesis_id") == challenger_id), None)
    promotion_gate = _evaluate_promotion_gate(
        leader,
        challenger,
        pressure=pressure,
        leader_tenure=leader_tenure,
    )

    def score(item: dict) -> float:
        base = 0.0
        status = item.get("status")
        if status == "supported":
            base += 0.08
        elif status == "unstable":
            base -= 0.08
        phase = item.get("evolution_phase")
        if phase == "accelerating":
            base += 0.07
        elif phase == "recovering":
            base += 0.03
        elif phase == "regressing":
            base -= 0.08
        strength = item.get("phase_strength")
        if strength == "high":
            base += 0.03
        elif strength == "medium":
            base += 0.015
        trajectory = item.get("trajectory_signal")
        if trajectory == "strong_acceleration":
            base += 0.03
        elif trajectory == "newly_accelerating":
            base += 0.02
        elif trajectory == "strong_recovery":
            base += 0.03
        elif trajectory == "newly_recovering":
            base += 0.02
        elif trajectory == "stale_stable":
            base -= 0.02
        elif trajectory == "continuing_regression":
            base -= 0.03
        elif trajectory == "deep_regression":
            base -= 0.04
        action_mode = item.get("action_mode")
        if action_mode == "promote_emerging_anchor":
            base += 0.04
        elif action_mode == "scale_confident_anchor":
            base += 0.06
        elif action_mode == "validate_low_confidence_anchor":
            base -= 0.01
        if pressure == "rising" and challenger_id:
            if item.get("hypothesis_id") == challenger_id:
                base += 0.05
            elif item.get("hypothesis_id") == leader_id and leader_tenure == "sustained":
                base -= 0.02
        base += _score_backlog_projected_hypothesis_coherence(item, fallback, expansion_summary)
        base += _score_joint_pending_hypothesis_pair(
            item,
            fallback,
            backlog_state,
            backlog_evolution_summary,
            expansion_summary,
        )
        base += _score_joint_recovery_hypothesis_pair(
            item,
            backlog_state,
            expansion_summary,
        )
        base += _score_joint_promotion_ready_hypothesis_pair(
            item,
            backlog_state,
            expansion_summary,
        )
        return base

    selected = max(
        tracked_hypotheses,
        key=lambda item: (
            score(item),
            -(int(item.get("last_selected_iteration", 0) or 0)),
            item.get("hypothesis_id") or "",
        ),
    )
    selected_id = selected.get("hypothesis_id")
    if not selected_id:
        return fallback, "selected_candidate_projection", False, promotion_gate
    used_frontier_pressure = bool(
        pressure == "rising"
        and challenger_id
        and selected_id == challenger_id
        and leader_tenure == "sustained"
    )
    if not used_frontier_pressure:
        if _allows_persistent_rising_reserve_hypothesis_reroute(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", False, promotion_gate
        if _allows_persistent_action_mode_divergence_hypothesis_reroute(
            selected_id,
            fallback,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", False, promotion_gate
        if _allows_persistent_anchor_divergence_hypothesis_reroute(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", False, promotion_gate
        if _allows_persistent_promotion_ready_hypothesis_reroute(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        if _allows_persistent_recovery_hypothesis_reroute(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        if _allows_persistent_pending_hypothesis_reroute(
            selected_id,
            backlog_state,
            backlog_evolution_summary,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        return fallback, "selected_candidate_projection", False, promotion_gate
    if promotion_gate["used_promotion_gate"] and not promotion_gate["promotion_gate_passed"]:
        if _allows_joint_pending_hypothesis_override(
            selected_id,
            backlog_state,
            backlog_evolution_summary,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        if _allows_joint_recovery_hypothesis_override(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        if _allows_joint_promotion_ready_hypothesis_override(
            selected_id,
            backlog_state,
            expansion_summary,
        ):
            return [selected_id], "tracked_reprioritization", True, promotion_gate
        return fallback, "selected_candidate_projection", False, promotion_gate
    return [selected_id], "tracked_reprioritization", True, promotion_gate


def _score_expansion_recommendations(
    candidate: dict,
    backlog_evolution_summary: dict | None,
    hypothesis_evolution_summary: dict | None,
) -> float:
    score = 0.0
    candidate_id = candidate.get("experiment_id")
    linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])

    recommended_experiment_id = (backlog_evolution_summary or {}).get("recommended_experiment_id")
    recommended_backlog_action = (backlog_evolution_summary or {}).get("recommended_action")
    if recommended_experiment_id and candidate_id == recommended_experiment_id:
        if recommended_backlog_action == "promote_promising_candidate":
            score += 0.16
        elif recommended_backlog_action == "stabilize_recovering_candidate":
            score += 0.15
        elif recommended_backlog_action == "recover_regressing_candidate":
            score -= 0.12
        else:
            score += 0.12
        recommended_trajectory_signal = (backlog_evolution_summary or {}).get("recommended_trajectory_signal")
        if recommended_trajectory_signal == "newly_recovering":
            score += 0.04
        elif recommended_trajectory_signal == "strong_recovery":
            score += 0.03
        elif recommended_trajectory_signal == "stale_stable":
            score -= 0.02

    recommended_hypothesis_id = (hypothesis_evolution_summary or {}).get("recommended_hypothesis_id")
    recommended_hypothesis_action = (hypothesis_evolution_summary or {}).get("recommended_action")
    if recommended_hypothesis_id and recommended_hypothesis_id in linked_hypothesis_ids:
        if recommended_hypothesis_action == "promote_supported_hypothesis":
            score += 0.14
        elif recommended_hypothesis_action == "stabilize_recovering_hypothesis":
            score += 0.13
        elif recommended_hypothesis_action == "stabilize_regressing_hypothesis":
            score -= 0.1
        else:
            score += 0.1
        recommended_hypothesis_trajectory_signal = (hypothesis_evolution_summary or {}).get("recommended_trajectory_signal")
        if recommended_hypothesis_trajectory_signal == "newly_recovering":
            score += 0.03
        elif recommended_hypothesis_trajectory_signal == "stale_stable":
            score -= 0.01

    return score


def _score_anchor_coherence(
    candidate: dict,
    hypothesis_evolution_summary: dict | None,
    expansion_summary: dict | None = None,
) -> float:
    action_mode_divergence_memory = (expansion_summary or {}).get("action_mode_divergence_memory") or {}
    if (
        (expansion_summary or {}).get("next_expansion_action") == "resolve_persistent_action_mode_divergence"
        and action_mode_divergence_memory.get("divergence_state") == "persistent"
    ):
        linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
        if not linked_hypothesis_ids:
            return 0.0
        recommended_backlog_action_mode = (expansion_summary or {}).get("recommended_backlog_action_mode")
        recommended_hypothesis_action_mode = (expansion_summary or {}).get("recommended_hypothesis_action_mode")
        if not recommended_backlog_action_mode or not recommended_hypothesis_action_mode:
            return 0.0
        recommended_hypothesis_id = (hypothesis_evolution_summary or {}).get("recommended_hypothesis_id")
        if recommended_hypothesis_id and recommended_hypothesis_id in linked_hypothesis_ids:
            return -0.22
        active_candidate_hypothesis_ids = set(
            (((expansion_summary or {}).get("backlog_selection_context") or {}).get("hypothesis_links") or [])
        )
        if linked_hypothesis_ids & active_candidate_hypothesis_ids:
            return 0.44

    divergence_memory = (expansion_summary or {}).get("anchor_divergence_memory") or {}
    if (
        (expansion_summary or {}).get("next_expansion_action")
        in {
            "reconcile_anchor_signals",
            "resolve_persistent_anchor_divergence",
            "resolve_persistent_coordination_divergence",
        }
        and (expansion_summary or {}).get("anchor_coherence") == "divergent"
        and divergence_memory.get("divergence_state") == "persistent"
    ):
        expected_hypothesis_ids = set(
            divergence_memory.get("expected_hypothesis_ids")
            or (expansion_summary or {}).get("anchor_coherence_expected_hypothesis_ids")
            or []
        )
        linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
        if not linked_hypothesis_ids:
            return 0.0
        if linked_hypothesis_ids & expected_hypothesis_ids:
            return 0.62
        return -0.34

    recommended_hypothesis_id = (hypothesis_evolution_summary or {}).get("recommended_hypothesis_id")
    recommended_hypothesis_action = (hypothesis_evolution_summary or {}).get("recommended_action")
    if not recommended_hypothesis_id:
        return 0.0
    if recommended_hypothesis_action not in {
        "promote_supported_hypothesis",
        "promote_ready_hypothesis",
    }:
        return 0.0

    linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
    if not linked_hypothesis_ids:
        return 0.0
    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    readiness_state = promotion_ready_pair.get("readiness_state")
    readiness_pressure_streak = int(promotion_ready_pair.get("pressure_streak", 0) or 0)
    if recommended_hypothesis_id in linked_hypothesis_ids:
        score = 0.58 if readiness_state == "persistent" else 0.5
        if readiness_pressure_streak > 2:
            score += 0.02 * min(readiness_pressure_streak - 2, 2)
        return score
    return -0.3


def _score_backlog_projected_hypothesis_coherence(
    hypothesis: dict,
    fallback_links: list[str] | None,
    expansion_summary: dict | None = None,
) -> float:
    projected_hypothesis_ids = set(fallback_links or [])
    if not projected_hypothesis_ids:
        return 0.0

    hypothesis_id = hypothesis.get("hypothesis_id")
    if hypothesis_id not in projected_hypothesis_ids:
        return 0.0

    status = hypothesis.get("status")
    phase = hypothesis.get("evolution_phase")
    action_mode = hypothesis.get("action_mode")
    if status != "supported":
        return 0.0
    if phase not in {"stable", "accelerating"}:
        return 0.0
    if action_mode not in {"validate_low_confidence_anchor", "scale_confident_anchor"}:
        return 0.0
    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    readiness_state = promotion_ready_pair.get("readiness_state")
    readiness_pressure_streak = int(promotion_ready_pair.get("pressure_streak", 0) or 0)
    score = 0.28 if readiness_state == "persistent" else 0.22
    if readiness_pressure_streak > 2:
        score += 0.02 * min(readiness_pressure_streak - 2, 2)
    return score


def _score_joint_promotion_ready_hypothesis_pair(
    hypothesis: dict,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> float:
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "promote_ready_challengers",
        "advance_persistent_promotion_ready_pair",
    }:
        return 0.0
    if (expansion_summary or {}).get("recommended_backlog_action") != "promote_ready_candidate":
        return 0.0
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "promote_ready_hypothesis":
        return 0.0

    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    candidate_id = promotion_ready_pair.get("experiment_id") or (expansion_summary or {}).get(
        "promotion_ready_candidate_id"
    )
    hypothesis_id = promotion_ready_pair.get("hypothesis_id") or (expansion_summary or {}).get(
        "promotion_ready_hypothesis_id"
    )
    if not candidate_id or not hypothesis_id:
        return 0.0

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    if active_candidate_id != candidate_id:
        return 0.0

    if hypothesis.get("hypothesis_id") != hypothesis_id:
        return -0.04

    readiness_state = promotion_ready_pair.get("readiness_state")
    readiness_pressure_streak = int(promotion_ready_pair.get("pressure_streak", 0) or 0)
    score = 0.32 if readiness_state == "persistent" else 0.24
    if readiness_pressure_streak > 2:
        score += 0.02 * min(readiness_pressure_streak - 2, 2)
    return score


def _allows_joint_promotion_ready_candidate_override(
    selected_candidate_id: str | None,
    hypothesis_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_candidate_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "promote_ready_challengers",
        "advance_persistent_promotion_ready_pair",
    }:
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "promote_ready_candidate":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "promote_ready_hypothesis":
        return False

    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    candidate_id = promotion_ready_pair.get("experiment_id") or (expansion_summary or {}).get(
        "promotion_ready_candidate_id"
    )
    hypothesis_id = promotion_ready_pair.get("hypothesis_id") or (expansion_summary or {}).get(
        "promotion_ready_hypothesis_id"
    )
    if not candidate_id or not hypothesis_id:
        return False

    active_hypotheses = set((hypothesis_state or {}).get("active_hypotheses") or [])
    return selected_candidate_id == candidate_id and hypothesis_id in active_hypotheses


def _allows_joint_pending_candidate_override(
    selected_candidate_id: str | None,
    hypothesis_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_candidate_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "investigate_pending_promotion_pair",
        "resolve_persistent_pending_promotion_pair",
    }:
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "investigate_pending_candidate_promotion":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "investigate_pending_hypothesis_promotion":
        return False

    pending_pair = (expansion_summary or {}).get("joint_pending_promotion_pair") or {}
    candidate_id = pending_pair.get("experiment_id") or (expansion_summary or {}).get(
        "pending_promotion_candidate_id"
    )
    hypothesis_id = pending_pair.get("hypothesis_id") or (expansion_summary or {}).get(
        "pending_promotion_hypothesis_id"
    )
    if not candidate_id or not hypothesis_id:
        return False

    active_hypotheses = set((hypothesis_state or {}).get("active_hypotheses") or [])
    return selected_candidate_id == candidate_id and hypothesis_id in active_hypotheses


def _allows_joint_recovery_candidate_override(
    selected_candidate_id: str | None,
    hypothesis_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_candidate_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "preserve_joint_recovery_pair",
        "stabilize_persistent_joint_recovery_pair",
    }:
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "recover_regressing_candidate":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "stabilize_regressing_hypothesis":
        return False
    if "scientific_validity_gap" not in set((expansion_summary or {}).get("risk_flags") or []):
        return False

    recovery_pair = (expansion_summary or {}).get("joint_recovery_pair") or {}
    candidate_id = recovery_pair.get("experiment_id")
    hypothesis_id = recovery_pair.get("hypothesis_id")
    if not candidate_id or not hypothesis_id:
        return False

    active_hypotheses = set((hypothesis_state or {}).get("active_hypotheses") or [])
    return selected_candidate_id == candidate_id and hypothesis_id in active_hypotheses


def _score_joint_pending_promotion_pair(
    candidate: dict,
    backlog_evolution_summary: dict | None,
    hypothesis_evolution_summary: dict | None,
    expansion_summary: dict | None = None,
) -> float:
    if (backlog_evolution_summary or {}).get("recommended_action") != "investigate_pending_candidate_promotion":
        return 0.0
    if (hypothesis_evolution_summary or {}).get("recommended_action") != "investigate_pending_hypothesis_promotion":
        return 0.0

    pending_candidate_id = (backlog_evolution_summary or {}).get("pending_promotion_candidate_id")
    pending_hypothesis_id = (hypothesis_evolution_summary or {}).get("pending_promotion_hypothesis_id")
    if not pending_candidate_id or not pending_hypothesis_id:
        return 0.0

    pending_pair = (expansion_summary or {}).get("joint_pending_promotion_pair") or {}
    pending_state = pending_pair.get("pending_state")
    pending_pressure_streak = int(pending_pair.get("pressure_streak", 0) or 0)
    candidate_id = candidate.get("experiment_id")
    linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
    if candidate_id == pending_candidate_id and pending_hypothesis_id in linked_hypothesis_ids:
        score = 0.34 if pending_state == "persistent" else 0.26
        if pending_pressure_streak > 2:
            score += 0.02 * min(pending_pressure_streak - 2, 2)
        return score
    if pending_hypothesis_id in linked_hypothesis_ids:
        return 0.08
    return -0.06


def _score_joint_recovery_pair(
    candidate: dict,
    backlog_evolution_summary: dict | None,
    hypothesis_evolution_summary: dict | None,
    expansion_summary: dict | None = None,
) -> float:
    if (backlog_evolution_summary or {}).get("recommended_action") != "recover_regressing_candidate":
        return 0.0
    if (hypothesis_evolution_summary or {}).get("recommended_action") != "stabilize_regressing_hypothesis":
        return 0.0
    if (backlog_evolution_summary or {}).get("dominant_failure_mode") != "scientific_validity":
        return 0.0
    if (hypothesis_evolution_summary or {}).get("dominant_failure_mode") != "scientific_validity":
        return 0.0

    recommended_candidate_id = (backlog_evolution_summary or {}).get("recommended_experiment_id")
    recommended_hypothesis_id = (hypothesis_evolution_summary or {}).get("recommended_hypothesis_id")
    if not recommended_candidate_id or not recommended_hypothesis_id:
        return 0.0

    candidate_id = candidate.get("experiment_id")
    linked_hypothesis_ids = set(candidate.get("hypothesis_links") or [])
    candidate_status = candidate.get("status")
    candidate_phase = candidate.get("evolution_phase")
    recovery_pair = (expansion_summary or {}).get("joint_recovery_pair") or {}
    recovery_state = recovery_pair.get("recovery_state")
    recovery_streak = int(recovery_pair.get("recovery_streak", 0) or 0)
    if candidate_id == recommended_candidate_id and recommended_hypothesis_id in linked_hypothesis_ids:
        if candidate_status == "mixed" or candidate_phase == "recovering":
            score = 0.98 if recovery_state == "persistent" else 0.9
            if recovery_streak > 2:
                score += 0.02 * min(recovery_streak - 2, 2)
            return score
        return 0.24
    if recommended_hypothesis_id in linked_hypothesis_ids:
        return 0.07
    return -0.05


def _score_joint_pending_hypothesis_pair(
    hypothesis: dict,
    fallback_links: list[str] | None,
    backlog_state: dict | None,
    backlog_evolution_summary: dict | None,
    expansion_summary: dict | None,
) -> float:
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "investigate_pending_promotion_pair",
        "resolve_persistent_pending_promotion_pair",
    }:
        return 0.0

    pending_pair = (expansion_summary or {}).get("joint_pending_promotion_pair") or {}
    pending_candidate_id = pending_pair.get("experiment_id") or (backlog_evolution_summary or {}).get(
        "pending_promotion_candidate_id"
    )
    pending_hypothesis_id = pending_pair.get("hypothesis_id")
    if not pending_candidate_id or not pending_hypothesis_id:
        return 0.0

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    if active_candidate_id != pending_candidate_id:
        return 0.0

    projected_hypothesis_ids = set(fallback_links or [])
    pending_state = pending_pair.get("pending_state")
    pending_pressure_streak = int(pending_pair.get("pressure_streak", 0) or 0)

    hypothesis_id = hypothesis.get("hypothesis_id")
    if hypothesis_id == pending_hypothesis_id:
        score = 0.28 if pending_state == "persistent" else 0.22
        if pending_pressure_streak > 2:
            score += 0.10 + 0.02 * min(pending_pressure_streak - 3, 1)
        return score
    if hypothesis_id in projected_hypothesis_ids:
        return -0.04
    return -0.06


def _score_joint_recovery_hypothesis_pair(
    hypothesis: dict,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> float:
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "preserve_joint_recovery_pair",
        "stabilize_persistent_joint_recovery_pair",
    }:
        return 0.0
    if (expansion_summary or {}).get("recommended_backlog_action") != "recover_regressing_candidate":
        return 0.0
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "stabilize_regressing_hypothesis":
        return 0.0
    if "scientific_validity_gap" not in set((expansion_summary or {}).get("risk_flags") or []):
        return 0.0

    recovery_pair = (expansion_summary or {}).get("joint_recovery_pair") or {}
    recovery_candidate_id = recovery_pair.get("experiment_id")
    recovery_hypothesis_id = recovery_pair.get("hypothesis_id")
    if not recovery_candidate_id or not recovery_hypothesis_id:
        return 0.0

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    if active_candidate_id != recovery_candidate_id:
        return 0.0

    hypothesis_id = hypothesis.get("hypothesis_id")
    recovery_state = recovery_pair.get("recovery_state")
    recovery_streak = int(recovery_pair.get("recovery_streak", 0) or 0)
    if hypothesis_id == recovery_hypothesis_id:
        status = hypothesis.get("status")
        phase = hypothesis.get("evolution_phase")
        if status == "mixed" or phase == "recovering":
            score = 0.54 if recovery_state == "persistent" else 0.48
            if recovery_streak > 2:
                score += 0.02 * min(recovery_streak - 2, 2)
            return score
        return 0.18
    return -0.04


def _allows_joint_promotion_ready_hypothesis_override(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "promote_ready_challengers",
        "advance_persistent_promotion_ready_pair",
    }:
        return False

    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    candidate_id = promotion_ready_pair.get("experiment_id") or (expansion_summary or {}).get(
        "promotion_ready_candidate_id"
    )
    hypothesis_id = promotion_ready_pair.get("hypothesis_id") or (expansion_summary or {}).get(
        "promotion_ready_hypothesis_id"
    )
    if not candidate_id or not hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == candidate_id and selected_hypothesis_id == hypothesis_id


def _allows_persistent_promotion_ready_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") != "advance_persistent_promotion_ready_pair":
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "promote_ready_candidate":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "promote_ready_hypothesis":
        return False

    promotion_ready_pair = (expansion_summary or {}).get("joint_promotion_ready_pair") or {}
    if promotion_ready_pair.get("readiness_state") != "persistent":
        return False

    candidate_id = promotion_ready_pair.get("experiment_id") or (expansion_summary or {}).get(
        "promotion_ready_candidate_id"
    )
    hypothesis_id = promotion_ready_pair.get("hypothesis_id") or (expansion_summary or {}).get(
        "promotion_ready_hypothesis_id"
    )
    if not candidate_id or not hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == candidate_id and selected_hypothesis_id == hypothesis_id


def _allows_persistent_anchor_divergence_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "reconcile_anchor_signals",
        "resolve_persistent_anchor_divergence",
        "resolve_persistent_coordination_divergence",
    }:
        return False
    if (expansion_summary or {}).get("anchor_coherence") != "divergent":
        return False

    divergence_memory = (expansion_summary or {}).get("anchor_divergence_memory") or {}
    if divergence_memory.get("divergence_state") != "persistent":
        return False

    expected_hypothesis_ids = list(
        divergence_memory.get("expected_hypothesis_ids")
        or (expansion_summary or {}).get("anchor_coherence_expected_hypothesis_ids")
        or []
    )
    if selected_hypothesis_id not in expected_hypothesis_ids:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    recommended_candidate_id = (expansion_summary or {}).get("recommended_experiment_id")
    return bool(active_candidate_id and active_candidate_id == recommended_candidate_id)


def _allows_persistent_action_mode_divergence_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    fallback_links: list[str] | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "resolve_persistent_action_mode_divergence",
        "resolve_persistent_coordination_divergence",
    }:
        return False

    divergence_memory = (expansion_summary or {}).get("action_mode_divergence_memory") or {}
    if divergence_memory.get("divergence_state") != "persistent":
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    recommended_candidate_id = (expansion_summary or {}).get("recommended_experiment_id")
    if not active_candidate_id or active_candidate_id != recommended_candidate_id:
        return False

    projected_hypothesis_ids = set(fallback_links or [])
    if projected_hypothesis_ids and selected_hypothesis_id in projected_hypothesis_ids:
        return True

    recommended_hypothesis_action_mode = (expansion_summary or {}).get("recommended_hypothesis_action_mode")
    return bool(recommended_hypothesis_action_mode and selected_hypothesis_id)


def _allows_persistent_rising_reserve_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False

    alternative_context = (expansion_summary or {}).get("hypothesis_active_alternative_context") or {}
    if alternative_context.get("hypothesis_id") != selected_hypothesis_id:
        return False
    if alternative_context.get("frontier_age") != "persistent":
        return False
    if alternative_context.get("frontier_trend") != "rising":
        return False
    if alternative_context.get("suppressed_by") not in {"stale_trajectory", "weaker_phase_strength"}:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    recommended_candidate_id = (expansion_summary or {}).get("recommended_experiment_id")
    if not active_candidate_id or active_candidate_id != recommended_candidate_id:
        return False

    recommended_hypothesis_id = (expansion_summary or {}).get("recommended_hypothesis_id")
    return bool(recommended_hypothesis_id and recommended_hypothesis_id != selected_hypothesis_id)


def _select_persistent_rising_reserve_backlog_candidate(
    candidate_pool: list[dict],
    hypothesis_state: dict | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> dict | None:
    alternative_context = (expansion_summary or {}).get("backlog_alternative_context") or {}
    reserve_candidate_id = alternative_context.get("experiment_id")
    if not reserve_candidate_id:
        return None
    if alternative_context.get("frontier_age") != "persistent":
        return None
    if alternative_context.get("frontier_trend") != "rising":
        return None
    if alternative_context.get("suppressed_by") not in {"stale_trajectory", "weaker_phase_strength"}:
        return None

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    recommended_candidate_id = (expansion_summary or {}).get("recommended_experiment_id")
    if not active_candidate_id or active_candidate_id != recommended_candidate_id:
        return None
    if reserve_candidate_id == recommended_candidate_id:
        return None

    active_hypothesis_ids = set((hypothesis_state or {}).get("active_hypotheses") or [])
    reserve_candidate = next(
        (candidate for candidate in candidate_pool if candidate.get("experiment_id") == reserve_candidate_id),
        None,
    )
    if reserve_candidate is None:
        return None

    reserve_links = set(reserve_candidate.get("hypothesis_links") or [])
    if active_hypothesis_ids and reserve_links and not (active_hypothesis_ids & reserve_links):
        return None
    return reserve_candidate


def _allows_joint_recovery_hypothesis_override(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "preserve_joint_recovery_pair",
        "stabilize_persistent_joint_recovery_pair",
    }:
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "recover_regressing_candidate":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "stabilize_regressing_hypothesis":
        return False
    if "scientific_validity_gap" not in set((expansion_summary or {}).get("risk_flags") or []):
        return False

    recovery_pair = (expansion_summary or {}).get("joint_recovery_pair") or {}
    candidate_id = recovery_pair.get("experiment_id")
    hypothesis_id = recovery_pair.get("hypothesis_id")
    if not candidate_id or not hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == candidate_id and selected_hypothesis_id == hypothesis_id


def _allows_persistent_recovery_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") != "stabilize_persistent_joint_recovery_pair":
        return False
    if (expansion_summary or {}).get("recommended_backlog_action") != "recover_regressing_candidate":
        return False
    if (expansion_summary or {}).get("recommended_hypothesis_action") != "stabilize_regressing_hypothesis":
        return False
    if "scientific_validity_gap" not in set((expansion_summary or {}).get("risk_flags") or []):
        return False

    recovery_pair = (expansion_summary or {}).get("joint_recovery_pair") or {}
    if recovery_pair.get("recovery_state") != "persistent":
        return False

    candidate_id = recovery_pair.get("experiment_id")
    hypothesis_id = recovery_pair.get("hypothesis_id")
    if not candidate_id or not hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == candidate_id and selected_hypothesis_id == hypothesis_id


def _allows_joint_pending_hypothesis_override(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    backlog_evolution_summary: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") not in {
        "investigate_pending_promotion_pair",
        "resolve_persistent_pending_promotion_pair",
    }:
        return False

    pending_pair = (expansion_summary or {}).get("joint_pending_promotion_pair") or {}
    pending_candidate_id = pending_pair.get("experiment_id") or (backlog_evolution_summary or {}).get(
        "pending_promotion_candidate_id"
    )
    pending_hypothesis_id = pending_pair.get("hypothesis_id")
    if not pending_candidate_id or not pending_hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == pending_candidate_id and selected_hypothesis_id == pending_hypothesis_id


def _allows_persistent_pending_hypothesis_reroute(
    selected_hypothesis_id: str | None,
    backlog_state: dict | None,
    backlog_evolution_summary: dict | None,
    expansion_summary: dict | None,
) -> bool:
    if not selected_hypothesis_id:
        return False
    if (expansion_summary or {}).get("next_expansion_action") != "resolve_persistent_pending_promotion_pair":
        return False

    pending_pair = (expansion_summary or {}).get("joint_pending_promotion_pair") or {}
    if pending_pair.get("pending_state") != "persistent":
        return False

    pending_candidate_id = pending_pair.get("experiment_id") or (backlog_evolution_summary or {}).get(
        "pending_promotion_candidate_id"
    )
    pending_hypothesis_id = pending_pair.get("hypothesis_id")
    if not pending_candidate_id or not pending_hypothesis_id:
        return False

    active_candidate_id = (((backlog_state or {}).get("active_candidate") or {}).get("experiment_id"))
    return active_candidate_id == pending_candidate_id and selected_hypothesis_id == pending_hypothesis_id


def _score_frontier_pressure(candidate: dict, backlog_state: dict | None) -> float:
    frontier_history = list((backlog_state or {}).get("frontier_history") or [])
    if not frontier_history:
        return 0.0

    latest_frontier = frontier_history[-1]
    ranked_ids = list(latest_frontier.get("ranked_ids") or [])
    if len(ranked_ids) < 2:
        return 0.0

    candidate_id = candidate.get("experiment_id")
    leader_id = latest_frontier.get("recommended_id")
    challenger_id = ranked_ids[1]
    pressure = (latest_frontier.get("pressure_snapshot") or {}).get("challenger_pressure")
    leader_tenure = (latest_frontier.get("pressure_snapshot") or {}).get("leader_tenure")

    if pressure != "rising":
        return 0.0
    if candidate_id == challenger_id:
        return 0.06
    if candidate_id == leader_id and leader_tenure == "sustained":
        return -0.03
    return 0.0


def _build_selection_rationale(
    candidate: dict | None,
    *,
    source: str,
    selection_mode: str,
    used_linked_hypothesis_state: bool,
    used_expansion_recommendations: bool,
    used_backlog_frontier_pressure: bool = False,
    used_hypothesis_frontier_pressure: bool = False,
    used_promotion_gate: bool = False,
    promotion_gate_passed: bool | None = None,
    promotion_gate_blocker: str | None = None,
    ranked_alternatives: list[dict] | None = None,
) -> dict | None:
    if not candidate:
        return None

    rationale = {
        "source": source,
        "selection_mode": selection_mode,
        "used_linked_hypothesis_state": used_linked_hypothesis_state,
        "used_expansion_recommendations": used_expansion_recommendations,
        "used_backlog_frontier_pressure": used_backlog_frontier_pressure,
        "used_hypothesis_frontier_pressure": used_hypothesis_frontier_pressure,
    }
    if used_promotion_gate:
        rationale["used_promotion_gate"] = True
        rationale["promotion_gate_passed"] = bool(promotion_gate_passed)
        if promotion_gate_blocker is not None:
            rationale["promotion_gate_blocker"] = promotion_gate_blocker
    score_signals: dict[str, str] = {}
    for key in ("evolution_phase", "phase_strength", "trajectory_signal", "action_mode", "status"):
        value = candidate.get(key)
        if value is None:
            continue
        normalized_key = {
            "evolution_phase": "phase",
            "phase_strength": "phase_strength",
            "trajectory_signal": "trajectory_signal",
            "action_mode": "action_mode",
            "status": "status",
        }[key]
        score_signals[normalized_key] = value
    if score_signals:
        rationale["score_signals"] = score_signals
    if ranked_alternatives:
        rationale["ranked_alternatives"] = [dict(item) for item in ranked_alternatives]
    return rationale


def _build_ranked_selection_frontier(
    selected_candidate: dict | None,
    *,
    candidate_pool: list[dict] | None,
    id_key: str = "experiment_id",
) -> list[dict]:
    if not selected_candidate:
        return []

    selected_id = selected_candidate.get(id_key)
    pool = [dict(item) for item in list(candidate_pool or []) if item.get(id_key)]
    if not pool:
        return []

    selected_item = next((item for item in pool if item.get(id_key) == selected_id), None)
    others = [item for item in pool if item.get(id_key) != selected_id]
    frontier: list[dict] = []

    if selected_item is not None:
        frontier.append(campaign_state._build_ranked_alternative(selected_item, id_key=id_key))

    for item in others[:2]:
        frontier.append(campaign_state._build_ranked_alternative(item, id_key=id_key))

    if not frontier:
        return frontier

    annotated: list[dict] = []
    leader = frontier[0]
    leader_score_band = leader.get("score_band")
    leader_action_mode = leader.get("action_mode")
    for index, item in enumerate(frontier):
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


def _build_candidate_transition_context(
    previous_candidate: dict | None,
    next_candidate: dict | None,
    state: dict | None,
) -> dict | None:
    def _recommendation_hint_from_driver(driver: dict | None, *, hypothesis: bool = False) -> str | None:
        if not driver:
            return None
        parts = [
            value
            for value in (
                driver.get("status"),
                driver.get("phase"),
                driver.get("phase_strength"),
                driver.get("trajectory_signal"),
                driver.get("action_mode"),
            )
            if value is not None
        ]
        if not parts:
            return None
        label = "recommended hypothesis anchor" if hypothesis else "recommended anchor"
        return f"{' / '.join(parts)} {label}"

    def _driver_from_score_signals(signals: dict | None) -> dict | None:
        if not signals:
            return None
        driver = {
            "phase": signals.get("phase"),
            "phase_strength": signals.get("phase_strength"),
            "trajectory_signal": signals.get("trajectory_signal"),
            "action_mode": signals.get("action_mode"),
            "status": signals.get("status"),
        }
        return driver if any(value is not None for value in driver.values()) else None

    def _selection_score_signals(selection_context: dict | None) -> dict | None:
        if not selection_context:
            return None
        direct = selection_context.get("score_signals")
        if direct:
            return direct
        ranked = list(selection_context.get("ranked_alternatives") or [])
        if ranked:
            leader_signals = (ranked[0] or {}).get("score_signals")
            if leader_signals:
                return leader_signals
        ranked_active = list(selection_context.get("ranked_active_hypotheses") or [])
        if ranked_active:
            leader_signals = (ranked_active[0] or {}).get("score_signals")
            if leader_signals:
                return leader_signals
        return None

    previous_id = (previous_candidate or {}).get("experiment_id")
    next_id = (next_candidate or {}).get("experiment_id")
    if not next_id:
        return None

    backlog_evolution_summary = (state or {}).get("backlog_evolution_summary") or {}
    hypothesis_evolution_summary = (state or {}).get("hypothesis_evolution_summary") or {}
    backlog_state = (state or {}).get("campaign_backlog") or {}
    hypothesis_state = (state or {}).get("campaign_hypotheses") or {}
    recovery_backlog_actions = {"recover_regressing_candidate", "stabilize_recovering_candidate"}
    recovery_hypothesis_actions = {"stabilize_regressing_hypothesis", "stabilize_recovering_hypothesis"}

    backlog_action = backlog_evolution_summary.get("recommended_action")
    backlog_action_mode = backlog_evolution_summary.get("recommended_action_mode")
    hypothesis_action = hypothesis_evolution_summary.get("recommended_action")
    hypothesis_action_mode = hypothesis_evolution_summary.get("recommended_action_mode")
    dominant_failure_mode = backlog_evolution_summary.get("dominant_failure_mode") or hypothesis_evolution_summary.get(
        "dominant_failure_mode"
    )
    expansion_confidence_action = ((state or {}).get("expansion_summary") or {}).get("next_expansion_action")
    backlog_selection_context = (
        ((state or {}).get("expansion_summary") or {}).get("backlog_selection_context")
        or (next_candidate or {}).get("selection_rationale")
        or {}
    )
    hypothesis_selection_context = (
        ((state or {}).get("expansion_summary") or {}).get("hypothesis_selection_context")
        or ((hypothesis_state.get("last_selection") or {}).get("selection_rationale") or {})
    )
    backlog_ranked_alternatives = list(((state or {}).get("expansion_summary") or {}).get("backlog_ranked_alternatives") or [])
    hypothesis_ranked_alternatives = list(((state or {}).get("expansion_summary") or {}).get("hypothesis_ranked_alternatives") or [])
    hypothesis_alternative_scope = "global_frontier"
    if not hypothesis_ranked_alternatives:
        hypothesis_ranked_alternatives = list(
            ((state or {}).get("expansion_summary") or {}).get("hypothesis_ranked_active_alternatives") or []
        )
        if hypothesis_ranked_alternatives:
            hypothesis_alternative_scope = "active_frontier"
    hypothesis_projection_experiment_id = hypothesis_selection_context.get("projected_from_experiment_id")
    hypothesis_selection_source = hypothesis_selection_context.get("source")
    hypothesis_selection_mode = hypothesis_selection_context.get("selection_mode")
    if (
        hypothesis_projection_experiment_id is None
        and hypothesis_selection_mode != "tracked_reprioritization"
        and list((next_candidate or {}).get("hypothesis_links") or [])
    ):
        hypothesis_projection_experiment_id = next_id
    if (
        hypothesis_selection_source is None
        and hypothesis_selection_mode != "tracked_reprioritization"
        and list((next_candidate or {}).get("hypothesis_links") or [])
    ):
        hypothesis_selection_source = "backlog_candidate_links"
    if hypothesis_selection_mode is None and list((next_candidate or {}).get("hypothesis_links") or []):
        hypothesis_selection_mode = "selected_candidate_projection"
    backlog_phase_strength_signal = backlog_evolution_summary.get("phase_strength_signal")
    hypothesis_phase_strength_signal = hypothesis_evolution_summary.get("phase_strength_signal")
    has_durable_expansion_state = bool(backlog_state.get("selection_ready") or hypothesis_state.get("selection_ready"))
    backlog_phase_signal = (
        backlog_evolution_summary.get("backlog_phase_signal")
        or backlog_evolution_summary.get("phase_signal")
        or ("accelerating" if backlog_evolution_summary.get("accelerating_candidates") else None)
        or ("recovering" if backlog_evolution_summary.get("recovery_candidates") else None)
        or ("regressing" if backlog_evolution_summary.get("regressing_candidates") else None)
        or ("stable" if backlog_evolution_summary.get("stable_candidates") else None)
    )
    hypothesis_phase_signal = (
        hypothesis_evolution_summary.get("hypothesis_phase_signal")
        or hypothesis_evolution_summary.get("phase_signal")
        or ("accelerating" if hypothesis_evolution_summary.get("accelerating_hypotheses") else None)
        or ("recovering" if hypothesis_evolution_summary.get("recovery_hypotheses") else None)
        or ("regressing" if hypothesis_evolution_summary.get("regressing_hypotheses") else None)
        or ("stable" if hypothesis_evolution_summary.get("stable_hypotheses") else None)
    )
    has_recovery_guidance = (
        backlog_action in recovery_backlog_actions or hypothesis_action in recovery_hypothesis_actions
    )

    backlog_recommendation_drivers = backlog_evolution_summary.get("recommendation_drivers")
    if backlog_recommendation_drivers is None:
        backlog_recommendation_drivers = _driver_from_score_signals(
            _selection_score_signals(backlog_selection_context)
        )
    if backlog_recommendation_drivers is None and next_candidate:
        backlog_recommendation_drivers = _driver_from_score_signals(
            {
                "phase": next_candidate.get("evolution_phase"),
                "phase_strength": next_candidate.get("phase_strength"),
                "trajectory_signal": next_candidate.get("trajectory_signal"),
                "action_mode": next_candidate.get("action_mode"),
                "status": next_candidate.get("status"),
            }
        )
    if backlog_recommendation_drivers and backlog_recommendation_drivers.get("recommendation_state_hint") is None:
        hint = _recommendation_hint_from_driver(backlog_recommendation_drivers, hypothesis=False)
        if hint is not None:
            backlog_recommendation_drivers = {
                **backlog_recommendation_drivers,
                "recommendation_state_hint": hint,
            }
    hypothesis_recommendation_drivers = hypothesis_evolution_summary.get("recommendation_drivers")
    if hypothesis_recommendation_drivers is None:
        hypothesis_recommendation_drivers = _driver_from_score_signals(
            _selection_score_signals(hypothesis_selection_context)
        )
    if hypothesis_recommendation_drivers is None:
        first_hypothesis = next(
            (
                item
                for item in list(hypothesis_state.get("tracked_hypotheses") or [])
                if item.get("hypothesis_id") in list((next_candidate or {}).get("hypothesis_links") or [])
            ),
            None,
        )
        if first_hypothesis is not None:
            hypothesis_recommendation_drivers = _driver_from_score_signals(
                {
                    "phase": first_hypothesis.get("evolution_phase"),
                    "phase_strength": first_hypothesis.get("phase_strength"),
                    "trajectory_signal": first_hypothesis.get("trajectory_signal"),
                    "action_mode": first_hypothesis.get("action_mode"),
                    "status": first_hypothesis.get("status"),
                }
            )
    if hypothesis_recommendation_drivers and hypothesis_recommendation_drivers.get("recommendation_state_hint") is None:
        hint = _recommendation_hint_from_driver(hypothesis_recommendation_drivers, hypothesis=True)
        if hint is not None:
            hypothesis_recommendation_drivers = {
                **hypothesis_recommendation_drivers,
                "recommendation_state_hint": hint,
            }
    pending_promotion_candidate_id = (
        ((state or {}).get("expansion_summary") or {}).get("pending_promotion_candidate_id")
        or backlog_evolution_summary.get("pending_promotion_candidate_id")
    )
    pending_promotion_hypothesis_id = (
        ((state or {}).get("expansion_summary") or {}).get("pending_promotion_hypothesis_id")
        or hypothesis_evolution_summary.get("pending_promotion_hypothesis_id")
    )
    pending_promotion_gate_blockers = list(
        ((state or {}).get("expansion_summary") or {}).get("pending_promotion_gate_blockers") or []
    )
    if not pending_promotion_gate_blockers:
        pending_promotion_gate_blockers = [
            blocker
            for blocker in [
                backlog_evolution_summary.get("pending_promotion_gate_blocker"),
                hypothesis_evolution_summary.get("pending_promotion_gate_blocker"),
            ]
            if blocker is not None
        ]
    promotion_ready_candidate_id = (
        ((state or {}).get("expansion_summary") or {}).get("promotion_ready_candidate_id")
        or backlog_evolution_summary.get("promotion_ready_candidate_id")
    )
    promotion_ready_hypothesis_id = (
        ((state or {}).get("expansion_summary") or {}).get("promotion_ready_hypothesis_id")
        or hypothesis_evolution_summary.get("promotion_ready_hypothesis_id")
    )
    joint_promotion_ready_pair = (
        ((state or {}).get("expansion_summary") or {}).get("joint_promotion_ready_pair") or None
    )
    joint_pending_promotion_pair = (
        ((state or {}).get("expansion_summary") or {}).get("joint_pending_promotion_pair") or None
    )
    joint_recovery_pair = (((state or {}).get("expansion_summary") or {}).get("joint_recovery_pair") or None)

    if previous_id and previous_id == next_id and not has_recovery_guidance:
        return None

    mode = (
        "recovery"
        if has_recovery_guidance
        else "continuation"
    )

    if not has_durable_expansion_state and not has_recovery_guidance:
        backlog_action = None
        backlog_action_mode = None
        hypothesis_action = None
        hypothesis_action_mode = None
        dominant_failure_mode = None
        backlog_phase_signal = None
        hypothesis_phase_signal = None
        backlog_phase_strength_signal = None
        hypothesis_phase_strength_signal = None
        expansion_confidence_action = None

    return {
        "mode": mode,
        "backlog_action": backlog_action,
        "backlog_action_mode": backlog_action_mode,
        "backlog_trajectory_signal": backlog_evolution_summary.get("recommended_trajectory_signal"),
        "backlog_recommendation_drivers": backlog_recommendation_drivers,
        "hypothesis_action": hypothesis_action,
        "hypothesis_action_mode": hypothesis_action_mode,
        "hypothesis_trajectory_signal": hypothesis_evolution_summary.get("recommended_trajectory_signal"),
        "hypothesis_recommendation_drivers": hypothesis_recommendation_drivers,
        "dominant_failure_mode": dominant_failure_mode,
        "backlog_phase_signal": backlog_phase_signal,
        "hypothesis_phase_signal": hypothesis_phase_signal,
        "backlog_phase_strength_signal": backlog_phase_strength_signal,
        "hypothesis_phase_strength_signal": hypothesis_phase_strength_signal,
        "expansion_confidence_action": expansion_confidence_action,
        "backlog_selection_source": backlog_selection_context.get("source"),
        "backlog_selection_mode": backlog_selection_context.get("selection_mode"),
        "backlog_selection_score_signals": _selection_score_signals(backlog_selection_context),
        "used_backlog_frontier_pressure": bool(backlog_selection_context.get("used_backlog_frontier_pressure")),
        "backlog_alternative_anchor": backlog_ranked_alternatives[1] if len(backlog_ranked_alternatives) > 1 else None,
        "hypothesis_alternative_anchor": (
            hypothesis_ranked_alternatives[1] if len(hypothesis_ranked_alternatives) > 1 else None
        ),
        "hypothesis_alternative_scope": hypothesis_alternative_scope,
        "hypothesis_projection_experiment_id": hypothesis_projection_experiment_id,
        "hypothesis_selection_source": hypothesis_selection_source,
        "hypothesis_selection_mode": hypothesis_selection_mode,
        "hypothesis_selection_score_signals": _selection_score_signals(hypothesis_selection_context),
        "pending_promotion_candidate_id": pending_promotion_candidate_id,
        "pending_promotion_hypothesis_id": pending_promotion_hypothesis_id,
        "pending_promotion_gate_blockers": pending_promotion_gate_blockers,
        "joint_pending_promotion_pair": joint_pending_promotion_pair,
        "promotion_ready_candidate_id": promotion_ready_candidate_id,
        "promotion_ready_hypothesis_id": promotion_ready_hypothesis_id,
        "joint_promotion_ready_pair": joint_promotion_ready_pair,
        "joint_recovery_pair": joint_recovery_pair,
        "anchor_coherence": ((state or {}).get("expansion_summary") or {}).get("anchor_coherence"),
        "anchor_coherence_expected_hypothesis_ids": list(
            ((state or {}).get("expansion_summary") or {}).get("anchor_coherence_expected_hypothesis_ids") or []
        ),
        "anchor_coherence_selected_hypothesis_id": (
            ((state or {}).get("expansion_summary") or {}).get("anchor_coherence_selected_hypothesis_id")
        ),
        "anchor_divergence_memory": (
            ((state or {}).get("expansion_summary") or {}).get("anchor_divergence_memory")
        ),
        "action_mode_divergence_memory": (
            ((state or {}).get("expansion_summary") or {}).get("action_mode_divergence_memory")
        ),
        "persistent_coordination_divergence": (
            ((state or {}).get("expansion_summary") or {}).get("persistent_coordination_divergence")
        ),
        "persistent_joint_reserve_memory": (
            ((state or {}).get("expansion_summary") or {}).get("persistent_joint_reserve_memory")
        ),
        "used_hypothesis_frontier_pressure": bool(hypothesis_selection_context.get("used_hypothesis_frontier_pressure"))
        or bool(backlog_selection_context.get("used_hypothesis_frontier_pressure")),
    }


def _select_tracked_candidate(
    backlog_state: dict | None,
    hypothesis_state: dict | None = None,
    backlog_evolution_summary: dict | None = None,
    hypothesis_evolution_summary: dict | None = None,
    expansion_summary: dict | None = None,
) -> dict | None:
    tracked_candidates = list((backlog_state or {}).get("tracked_candidates") or [])
    if not tracked_candidates:
        return None

    acceptable = [candidate for candidate in tracked_candidates if candidate.get("last_outcome") == "accept"]
    pool = acceptable or tracked_candidates
    hypothesis_index = _build_hypothesis_index(hypothesis_state)
    frontier_history = list((backlog_state or {}).get("frontier_history") or [])
    latest_frontier = frontier_history[-1] if frontier_history else {}
    ranked_ids = list(latest_frontier.get("ranked_ids") or [])
    leader_id = latest_frontier.get("recommended_id")
    challenger_id = ranked_ids[1] if len(ranked_ids) > 1 else None
    pressure = (latest_frontier.get("pressure_snapshot") or {}).get("challenger_pressure")
    leader_tenure = (latest_frontier.get("pressure_snapshot") or {}).get("leader_tenure")
    leader_candidate = next((item for item in tracked_candidates if item.get("experiment_id") == leader_id), None)
    challenger_candidate = next((item for item in tracked_candidates if item.get("experiment_id") == challenger_id), None)
    promotion_gate = _evaluate_promotion_gate(
        leader_candidate,
        challenger_candidate,
        pressure=pressure,
        leader_tenure=leader_tenure,
    )

    def tracked_candidate_score(candidate: dict) -> float:
        base = 0.0
        planner_ready = all(
            key in candidate and candidate.get(key) is not None
            for key in ("expected_information_gain", "risk_reduction", "cost_score")
        )
        if planner_ready:
            base = score_candidate(candidate)

        accept_count = int(candidate.get("accept_count", 0) or 0)
        rework_count = int(candidate.get("rework_count", 0) or 0)
        current_accept_streak = int(candidate.get("current_accept_streak", 0) or 0)
        current_rework_streak = int(candidate.get("current_rework_streak", 0) or 0)
        times_selected = int(candidate.get("times_selected", 0) or 0)
        last_accept_iteration = candidate.get("last_accept_iteration")
        last_selected_iteration = int(candidate.get("last_selected_iteration", 0) or 0)
        recency_bonus = 0.0 if last_accept_iteration is None else 0.01 * int(last_accept_iteration)
        hypothesis_bonus = _score_linked_hypotheses(candidate, hypothesis_index)
        hypothesis_pressure_bonus = _score_hypothesis_frontier_pressure(candidate, hypothesis_state)
        expansion_bonus = _score_expansion_recommendations(
            candidate,
            backlog_evolution_summary,
            hypothesis_evolution_summary,
        )
        joint_pending_pair_bonus = _score_joint_pending_promotion_pair(
            candidate,
            backlog_evolution_summary,
            hypothesis_evolution_summary,
            expansion_summary,
        )
        joint_recovery_pair_bonus = _score_joint_recovery_pair(
            candidate,
            backlog_evolution_summary,
            hypothesis_evolution_summary,
            expansion_summary,
        )
        anchor_coherence_bonus = _score_anchor_coherence(
            candidate,
            hypothesis_evolution_summary,
            expansion_summary,
        )
        frontier_pressure_bonus = _score_frontier_pressure(candidate, backlog_state)
        backlog_status_bonus = (
            0.08
            if candidate.get("status") == "promising"
            else -0.08
            if candidate.get("status") == "blocked"
            else 0.0
        )
        evolution_phase_bonus = (
            (
                0.07
                + (
                    0.03
                    if candidate.get("phase_strength") == "high"
                    else 0.015
                    if candidate.get("phase_strength") == "medium"
                    else 0.0
                )
            )
            if candidate.get("evolution_phase") == "accelerating"
            else (
                0.03
                + (
                    0.03
                    if candidate.get("phase_strength") == "high"
                    else 0.015
                    if candidate.get("phase_strength") == "medium"
                    else 0.0
                )
            )
            if candidate.get("evolution_phase") == "recovering"
            else (
                -0.08
                - (
                    0.03
                    if candidate.get("phase_strength") == "high"
                    else 0.015
                    if candidate.get("phase_strength") == "medium"
                    else 0.0
                )
            )
            if candidate.get("evolution_phase") == "regressing"
            else 0.0
        )
        action_mode_bonus = (
            0.08
            if candidate.get("action_mode") == "scale_confident_anchor"
            else 0.05
            if candidate.get("action_mode") == "promote_emerging_anchor"
            else 0.03
            if candidate.get("action_mode") == "maintain_viable_anchor"
            else -0.01
            if candidate.get("action_mode") == "validate_low_confidence_anchor"
            else 0.01
            if candidate.get("action_mode") == "stabilize_recovery"
            else 0.02
            if candidate.get("action_mode") == "recover_missing_artifacts"
            else -0.05
            if candidate.get("action_mode") == "reroute_for_stronger_evidence"
            else -0.03
            if candidate.get("action_mode") == "stabilize_execution"
            else -0.04
            if candidate.get("action_mode") == "recover_regressing_anchor"
            else 0.0
        )

        return (
            base
            + backlog_status_bonus
            + evolution_phase_bonus
            + action_mode_bonus
            + 0.05 * accept_count
            - 0.07 * rework_count
            + 0.06 * current_accept_streak
            - 0.09 * current_rework_streak
            - 0.02 * times_selected
            + recency_bonus
            + hypothesis_bonus
            + hypothesis_pressure_bonus
            + expansion_bonus
            + joint_pending_pair_bonus
            + joint_recovery_pair_bonus
            + anchor_coherence_bonus
            + frontier_pressure_bonus
        )

    scored_pool = [
        (
            candidate,
            tracked_candidate_score(candidate),
            _score_frontier_pressure(candidate, backlog_state),
            _score_hypothesis_frontier_pressure(candidate, hypothesis_state),
        )
        for candidate in pool
    ]

    planner_ready = [
        candidate
        for candidate, _score, _backlog_pressure, _hypothesis_pressure in scored_pool
        if all(key in candidate and candidate.get(key) is not None for key in ("expected_information_gain", "risk_reduction", "cost_score"))
    ]
    if planner_ready:
        selected = max(
            (
                (candidate, score, backlog_pressure, hypothesis_pressure)
                for candidate, score, backlog_pressure, hypothesis_pressure in scored_pool
                if candidate in planner_ready
            ),
            key=lambda item: (
                item[1],
                -(int(item[0].get("last_selected_iteration", 0) or 0)),
                item[0].get("experiment_id") or "",
            ),
        )
        reserve_candidate = _select_persistent_rising_reserve_backlog_candidate(
            pool,
            hypothesis_state,
            backlog_state,
            expansion_summary,
        )
        if reserve_candidate is not None and selected[0].get("experiment_id") != reserve_candidate.get("experiment_id"):
            reserve_backlog_pressure = _score_frontier_pressure(reserve_candidate, backlog_state)
            reserve_hypothesis_pressure = _score_hypothesis_frontier_pressure(reserve_candidate, hypothesis_state)
            return {
                **reserve_candidate,
                "_used_backlog_frontier_pressure": reserve_backlog_pressure > 0,
                "_used_hypothesis_frontier_pressure": reserve_hypothesis_pressure > 0,
                "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
            }
        if (
            promotion_gate["used_promotion_gate"]
            and not promotion_gate["promotion_gate_passed"]
            and selected[0].get("experiment_id") == challenger_id
            and leader_candidate is not None
        ):
            if _allows_joint_pending_candidate_override(
                selected[0].get("experiment_id"),
                hypothesis_state,
                expansion_summary,
            ):
                return {
                    **selected[0],
                    "_used_backlog_frontier_pressure": selected[2] > 0,
                    "_used_hypothesis_frontier_pressure": selected[3] > 0,
                    "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                    "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                    "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
                }
            if _allows_joint_recovery_candidate_override(
                selected[0].get("experiment_id"),
                hypothesis_state,
                expansion_summary,
            ):
                return {
                    **selected[0],
                    "_used_backlog_frontier_pressure": selected[2] > 0,
                    "_used_hypothesis_frontier_pressure": selected[3] > 0,
                    "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                    "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                    "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
                }
            if _allows_joint_promotion_ready_candidate_override(
                selected[0].get("experiment_id"),
                hypothesis_state,
                expansion_summary,
            ):
                return {
                    **selected[0],
                    "_used_backlog_frontier_pressure": selected[2] > 0,
                    "_used_hypothesis_frontier_pressure": selected[3] > 0,
                    "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                    "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                    "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
                }
            return {
                **leader_candidate,
                "_used_backlog_frontier_pressure": False,
                "_used_hypothesis_frontier_pressure": False,
                "_used_promotion_gate": True,
                "_promotion_gate_passed": False,
                "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
            }
        return {
            **selected[0],
            "_used_backlog_frontier_pressure": selected[2] > 0,
            "_used_hypothesis_frontier_pressure": selected[3] > 0,
            "_used_promotion_gate": promotion_gate["used_promotion_gate"],
            "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
            "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
        }

    ranked = sorted(
        scored_pool,
        key=lambda item: (
            -item[1],
            item[0].get("experiment_id") or "",
        ),
    )
    if not ranked:
        return None
    reserve_candidate = _select_persistent_rising_reserve_backlog_candidate(
        pool,
        hypothesis_state,
        backlog_state,
        expansion_summary,
    )
    if reserve_candidate is not None and ranked[0][0].get("experiment_id") != reserve_candidate.get("experiment_id"):
        reserve_backlog_pressure = _score_frontier_pressure(reserve_candidate, backlog_state)
        reserve_hypothesis_pressure = _score_hypothesis_frontier_pressure(reserve_candidate, hypothesis_state)
        return {
            **reserve_candidate,
            "_used_backlog_frontier_pressure": reserve_backlog_pressure > 0,
            "_used_hypothesis_frontier_pressure": reserve_hypothesis_pressure > 0,
            "_used_promotion_gate": promotion_gate["used_promotion_gate"],
            "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
            "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
        }
    candidate, _score, backlog_pressure, hypothesis_pressure = ranked[0]
    if (
        promotion_gate["used_promotion_gate"]
        and not promotion_gate["promotion_gate_passed"]
        and candidate.get("experiment_id") == challenger_id
        and leader_candidate is not None
    ):
        if _allows_joint_pending_candidate_override(
            candidate.get("experiment_id"),
            hypothesis_state,
            expansion_summary,
        ):
            return {
                **candidate,
                "_used_backlog_frontier_pressure": backlog_pressure > 0,
                "_used_hypothesis_frontier_pressure": hypothesis_pressure > 0,
                "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
            }
        if _allows_joint_recovery_candidate_override(
            candidate.get("experiment_id"),
            hypothesis_state,
            expansion_summary,
        ):
            return {
                **candidate,
                "_used_backlog_frontier_pressure": backlog_pressure > 0,
                "_used_hypothesis_frontier_pressure": hypothesis_pressure > 0,
                "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
            }
        if _allows_joint_promotion_ready_candidate_override(
            candidate.get("experiment_id"),
            hypothesis_state,
            expansion_summary,
        ):
            return {
                **candidate,
                "_used_backlog_frontier_pressure": backlog_pressure > 0,
                "_used_hypothesis_frontier_pressure": hypothesis_pressure > 0,
                "_used_promotion_gate": promotion_gate["used_promotion_gate"],
                "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
                "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
            }
        return {
            **leader_candidate,
            "_used_backlog_frontier_pressure": False,
            "_used_hypothesis_frontier_pressure": False,
            "_used_promotion_gate": True,
            "_promotion_gate_passed": False,
            "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
        }
    return {
        **candidate,
        "_used_backlog_frontier_pressure": backlog_pressure > 0,
        "_used_hypothesis_frontier_pressure": hypothesis_pressure > 0,
        "_used_promotion_gate": promotion_gate["used_promotion_gate"],
        "_promotion_gate_passed": promotion_gate["promotion_gate_passed"],
        "_promotion_gate_blocker": promotion_gate["promotion_gate_blocker"],
    }


def _merge_backlog_candidates_with_persisted_state(
    backlog: list[dict],
    persisted_state: dict | None = None,
) -> list[dict]:
    backlog_state = (persisted_state or {}).get("campaign_backlog") or {}
    tracked_candidates = list(backlog_state.get("tracked_candidates") or [])
    tracked_index = {
        item.get("experiment_id"): dict(item)
        for item in tracked_candidates
        if item.get("experiment_id")
    }

    merged: list[dict] = []
    for candidate in backlog:
        experiment_id = candidate.get("experiment_id")
        tracked = tracked_index.get(experiment_id, {})
        merged_candidate = dict(candidate)
        for key, value in tracked.items():
            if key in ("experiment_id", "objective", "hypothesis_links"):
                continue
            merged_candidate[key] = value
        merged.append(merged_candidate)
    return merged


def _select_candidate(base_objective: str, backlog_file: str | None, persisted_state: dict | None = None) -> dict:
    if not backlog_file:
        backlog_state = (persisted_state or {}).get("campaign_backlog") or {}
        hypothesis_state = (persisted_state or {}).get("campaign_hypotheses") or {}
        backlog_evolution_summary = (persisted_state or {}).get("backlog_evolution_summary")
        hypothesis_evolution_summary = (persisted_state or {}).get("hypothesis_evolution_summary")
        active_candidate = _select_tracked_candidate(
            backlog_state,
            hypothesis_state,
            backlog_evolution_summary,
            hypothesis_evolution_summary,
            (persisted_state or {}).get("expansion_summary"),
        ) or backlog_state.get("active_candidate")
        if active_candidate:
            rationale_candidate = active_candidate
            if rationale_candidate.get("status") is None:
                tracked_candidate = next(
                    (
                        item
                        for item in list(backlog_state.get("tracked_candidates") or [])
                        if item.get("experiment_id") == active_candidate.get("experiment_id")
                    ),
                    None,
                )
                if tracked_candidate is not None:
                    rationale_candidate = tracked_candidate
            return {
                "experiment_id": active_candidate.get("experiment_id"),
                "objective": active_candidate.get("objective", base_objective),
                "hypothesis_links": list(active_candidate.get("hypothesis_links") or ["h1"]),
                "expected_information_gain": active_candidate.get("expected_information_gain"),
                "risk_reduction": active_candidate.get("risk_reduction"),
                "cost_score": active_candidate.get("cost_score"),
                "candidate_count": backlog_state.get("candidate_count"),
                "source_path": backlog_state.get("source_path"),
                "candidate_pool": list(backlog_state.get("tracked_candidates") or []),
        "selection_rationale": _build_selection_rationale(
            rationale_candidate,
            source="durable_state",
            selection_mode="tracked_reprioritization",
            used_linked_hypothesis_state=bool(active_candidate.get("hypothesis_links")),
            used_expansion_recommendations=bool(backlog_evolution_summary or hypothesis_evolution_summary),
            used_backlog_frontier_pressure=bool(active_candidate.get("_used_backlog_frontier_pressure")),
            used_hypothesis_frontier_pressure=bool(active_candidate.get("_used_hypothesis_frontier_pressure")),
            used_promotion_gate=bool(active_candidate.get("_used_promotion_gate")),
            promotion_gate_passed=active_candidate.get("_promotion_gate_passed"),
            promotion_gate_blocker=active_candidate.get("_promotion_gate_blocker"),
            ranked_alternatives=_build_ranked_selection_frontier(
                active_candidate,
                candidate_pool=list(backlog_state.get("tracked_candidates") or []),
            ),
        ),
            }
        return {
            "objective": base_objective,
            "hypothesis_links": ["h1"],
            "expected_information_gain": None,
            "risk_reduction": None,
            "cost_score": None,
            "candidate_count": None,
            "source_path": None,
            "candidate_pool": None,
            "selection_rationale": None,
        }

    backlog = json.loads(Path(backlog_file).read_text(encoding="utf-8"))
    enriched_backlog = _merge_backlog_candidates_with_persisted_state(backlog, persisted_state)
    backlog_evolution_summary = (persisted_state or {}).get("backlog_evolution_summary")
    hypothesis_evolution_summary = (persisted_state or {}).get("hypothesis_evolution_summary")
    selected = _select_tracked_candidate(
        {"tracked_candidates": enriched_backlog},
        (persisted_state or {}).get("campaign_hypotheses"),
        backlog_evolution_summary,
        hypothesis_evolution_summary,
        (persisted_state or {}).get("expansion_summary"),
    )
    selection_mode = "tracked_reprioritization"
    if selected is None:
        selected = select_next_experiment(backlog)
        selection_mode = "planner_scored"
    rationale_candidate = selected
    if rationale_candidate.get("status") is None:
        tracked_candidate = next(
            (
                item
                for item in enriched_backlog
                if item.get("experiment_id") == selected.get("experiment_id")
            ),
            None,
        )
        if tracked_candidate is not None:
            rationale_candidate = tracked_candidate
    return {
        "experiment_id": selected.get("experiment_id"),
        "objective": selected.get("objective", base_objective),
        "hypothesis_links": list(selected.get("hypothesis_links") or ["h1"]),
        "expected_information_gain": selected.get("expected_information_gain"),
        "risk_reduction": selected.get("risk_reduction"),
        "cost_score": selected.get("cost_score"),
        "candidate_count": len(backlog),
        "source_path": backlog_file,
        "candidate_pool": enriched_backlog,
        "selection_rationale": _build_selection_rationale(
            rationale_candidate,
            source="backlog_file",
            selection_mode=selection_mode,
            used_linked_hypothesis_state=bool(selected.get("hypothesis_links"))
            and selection_mode == "tracked_reprioritization",
            used_expansion_recommendations=selection_mode == "tracked_reprioritization"
            and bool(backlog_evolution_summary or hypothesis_evolution_summary),
            used_backlog_frontier_pressure=bool(selected.get("_used_backlog_frontier_pressure")),
            used_hypothesis_frontier_pressure=bool(selected.get("_used_hypothesis_frontier_pressure")),
            used_promotion_gate=bool(selected.get("_used_promotion_gate")),
            promotion_gate_passed=selected.get("_promotion_gate_passed"),
            promotion_gate_blocker=selected.get("_promotion_gate_blocker"),
            ranked_alternatives=_build_ranked_selection_frontier(
                selected,
                candidate_pool=enriched_backlog,
            ),
        ),
    }


def _save_state(campaign_dir: Path, state: dict) -> None:
    (campaign_dir / "campaign_state.json").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )


def _append_iteration_log(campaign_dir: Path, payload: dict) -> None:
    log_path = campaign_dir / "iteration_log.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _record_iteration_result(
    campaign_dir: Path,
    *,
    decision: str,
    objective: str,
    research_question: str | None = None,
    task_intent: dict | None = None,
    brain_plan=None,
    experiment_brief: dict | None = None,
    task_packets: list[dict] | None = None,
    task_results: list[dict] | None = None,
    artifacts: dict | None = None,
    worker_result: dict | None = None,
    verification: dict | None = None,
    governance: dict | None = None,
    resume_metadata: dict | None = None,
    selected_candidate: dict | None = None,
    backlog_source: str | None = None,
    backlog_candidate_count: int | None = None,
    backlog_candidate_pool: list[dict] | None = None,
) -> dict:
    state = _load_state(campaign_dir)
    iteration_number = int(state.get("iterations_run", 0)) + 1
    resume_assessment = campaign_state.assess_resume_readiness(
        {
            "decision": decision,
            "verification": verification,
        }
    )
    operator_summary = campaign_state.build_operator_summary(
        task_intent=task_intent,
        verification=verification,
    )
    record = {
        "iteration": iteration_number,
        "objective": objective,
        "decision": decision,
        "governance": governance or {"decision": decision},
        "research_question": research_question,
        "task_intent": task_intent,
        "brain_plan": asdict(brain_plan) if brain_plan is not None else None,
        "experiment_brief": experiment_brief,
        "task_packets": task_packets,
        "task_results": task_results,
        "artifacts": artifacts,
        "worker_result": worker_result,
        "verification": verification,
        "round_summary": campaign_state.build_round_summary(
            decision=decision,
            task_intent=task_intent,
            verification=verification,
            brain_plan=brain_plan,
        ),
        "operator_summary": operator_summary,
        "resume": resume_metadata,
    }
    (campaign_dir / "latest_iteration.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    _append_iteration_log(campaign_dir, record)
    state["iterations_run"] = iteration_number
    state["last_decision"] = decision
    prior_failure_streak = int(state.get("failure_streak", 0))
    state["failure_streak"] = prior_failure_streak + 1 if decision == "REFINE" else 0
    state["campaign_summary"] = campaign_state.build_campaign_summary(
        research_question=research_question,
        iteration_number=iteration_number,
        operator_summary=operator_summary,
        verification=verification,
        resume_metadata=resume_metadata,
        resume_assessment=resume_assessment,
    )
    state["campaign_memory"] = campaign_state.build_campaign_memory(
        decision=decision,
        objective=objective,
        worker_result=worker_result,
        artifacts=artifacts,
        verification=verification,
        previous_memory=state.get("campaign_memory"),
    )
    state["memory_summary"] = campaign_state.build_campaign_memory_summary(state["campaign_memory"])
    state["continuation_anchor"] = campaign_state.build_continuation_anchor(
        memory=state["campaign_memory"],
        memory_summary=state["memory_summary"],
    )
    state["campaign_backlog"] = campaign_state.build_campaign_backlog(
        previous_backlog=state.get("campaign_backlog"),
        selected_candidate=selected_candidate,
        backlog_source=backlog_source,
        candidate_count=backlog_candidate_count,
        iteration_number=iteration_number,
        verification=verification,
        candidate_pool=backlog_candidate_pool,
    )
    state["backlog_summary"] = campaign_state.build_backlog_summary(state["campaign_backlog"])
    state["backlog_evolution_summary"] = campaign_state.build_backlog_evolution_summary(state["campaign_backlog"])
    experiment_hypothesis_links = list((experiment_brief or {}).get("hypothesis_links") or [])
    (
        selected_hypothesis_links,
        hypothesis_selection_mode,
        hypothesis_used_frontier_pressure,
        hypothesis_promotion_gate,
    ) = _select_hypothesis_links(
        state.get("campaign_hypotheses"),
        experiment_hypothesis_links,
        state.get("campaign_backlog"),
        state.get("backlog_evolution_summary"),
        state.get("expansion_summary"),
    )
    state["campaign_hypotheses"] = campaign_state.build_campaign_hypotheses(
        previous_hypotheses=state.get("campaign_hypotheses"),
        hypothesis_links=selected_hypothesis_links,
        verification=verification,
        iteration_number=iteration_number,
        projected_from_experiment_id=(selected_candidate or {}).get("experiment_id"),
        selection_mode=hypothesis_selection_mode,
        used_frontier_pressure=hypothesis_used_frontier_pressure,
        used_promotion_gate=bool(hypothesis_promotion_gate.get("used_promotion_gate")),
        promotion_gate_passed=hypothesis_promotion_gate.get("promotion_gate_passed"),
        promotion_gate_blocker=hypothesis_promotion_gate.get("promotion_gate_blocker"),
    )
    state["hypothesis_summary"] = campaign_state.build_hypothesis_summary(state["campaign_hypotheses"])
    state["hypothesis_evolution_summary"] = campaign_state.build_hypothesis_evolution_summary(
        state["campaign_hypotheses"]
    )
    state["expansion_summary"] = campaign_state.build_expansion_summary(
        backlog_summary=state["backlog_summary"],
        backlog_evolution_summary=state["backlog_evolution_summary"],
        hypothesis_summary=state["hypothesis_summary"],
        hypothesis_evolution_summary=state["hypothesis_evolution_summary"],
        previous_summary=state.get("expansion_summary"),
    )
    state["resume_assessment"] = resume_assessment
    state["campaign_lifecycle"] = campaign_state.derive_campaign_lifecycle(
        latest_outcome=state["campaign_summary"]["latest_outcome"],
        last_decision=decision,
        iterations_run=iteration_number,
    )
    _save_state(campaign_dir, state)
    return record


def _build_iteration_components(
    target: Path,
    objective: str,
    deliverables: list[str],
    timeout_sec: int,
    brain_plan,
    hypothesis_links: list[str] | None = None,
    decomposition_hint: str = "single_worker",
    worker_backend: str | None = None,
):
    question = _read_question(target)

    def planner(state, policy):  # noqa: ANN001
        return ExperimentBrief(
            experiment_id="exp_cli_001",
            objective=f"{objective}\n\nResearch question: {question}",
            hypothesis_links=hypothesis_links or ["h1"],
            inputs={"repo_path": str(target), "artifact_refs": [], "dataset_refs": []},
            constraints={
                "max_runtime_minutes": max(1, timeout_sec // 60),
                "max_api_cost_usd": 5.0,
                "allowed_backends": ["claude_code", "codex"],
            },
            deliverables=deliverables,
            acceptance_criteria=[f"{item} exists" for item in deliverables],
            decomposition_hint=decomposition_hint,
            preferred_worker_profile="coder_plus_runner",
        )

    def decomposer(brief):  # noqa: ANN001
        intent = derive_task_intent(brain_plan)
        if worker_backend and worker_backend != "any":
            intent = intent.model_copy(update={"worker_preference": worker_backend})
        return [task.model_dump() for task in decompose_experiment(brief, intent)]

    def verifier(brief, artifacts, result):  # noqa: ANN001
        intent = derive_task_intent(brain_plan)
        return verify_completion(
            {
                "deliverables": brief.deliverables,
                "objective": brief.objective,
                "acceptance_emphasis": intent.acceptance_emphasis,
            },
            artifacts,
            result,
        )

    def governor(state, verification, _policy):  # noqa: ANN001
        policy = build_policy_for_mode("moderate_autonomy")
        return make_governance_decision(state, verification, policy)

    return planner, decomposer, verifier, governor


@app.command("run-iteration")
def run_iteration_command(
    campaign_dir: str,
    objective: str = typer.Option(..., "--objective"),
    backlog_file: str | None = typer.Option(None, "--backlog-file"),
    deliverable: list[str] = typer.Option([], "--deliverable"),
    timeout_sec: int = typer.Option(120, "--timeout-sec"),
    resume: bool = typer.Option(False, "--resume"),
    decomposition_hint: str = typer.Option("single_worker", "--decomposition-hint"),
    worker_backend: str = typer.Option("any", "--worker-backend"),
) -> None:
    target = Path(campaign_dir)
    deliverables = deliverable or ["metrics.json", "result_note.md"]
    research_question = _read_question(target)
    persisted_state = _load_state(target)
    worker_registry = _load_worker_registry(target)
    governor_state = _build_governor_state(persisted_state)
    last_record = _load_resume_record(target, resume=resume)
    selected_candidate = _select_candidate(objective, backlog_file, persisted_state)
    selected_objective = selected_candidate["objective"]
    transition_context = _build_candidate_transition_context(None, selected_candidate, persisted_state)
    if last_record is not None:
        previous_objective = last_record.get("objective") or objective
        initial_plan = plan_next_iteration_with_candidate_transition(
            selected_objective,
            last_record,
            previous_objective=previous_objective,
            transition_context=transition_context,
        )
    else:
        use_transition_aware_cold_start = selected_objective != objective
        if use_transition_aware_cold_start:
            initial_plan = plan_next_iteration_with_candidate_transition(
                selected_objective,
                last_record,
                previous_objective=objective,
                transition_context=transition_context,
            )
        else:
            initial_plan = plan_next_iteration(selected_objective, last_record)
    task_intent = derive_task_intent(initial_plan).model_dump()
    resume_metadata = {"requested": True, "source_iteration": last_record.get("iteration")} if last_record is not None else None
    policy = build_policy_for_mode("moderate_autonomy")
    planner, decomposer, verifier, governor = _build_iteration_components(
        target,
        initial_plan.next_objective,
        deliverables,
        timeout_sec,
        initial_plan,
        selected_candidate["hypothesis_links"],
        decomposition_hint,
        worker_backend,
    )
    last: dict = {}
    governance_inputs: dict = {}

    def recording_planner(state, policy):  # noqa: ANN001
        brief = planner(state, policy)
        last["experiment_brief"] = brief.model_dump()
        return brief

    def recording_decomposer(brief):  # noqa: ANN001
        tasks = decomposer(brief)
        last["task_packets"] = tasks
        return tasks

    def recording_verifier(brief, artifacts, result):  # noqa: ANN001
        last["artifacts"] = artifacts
        last["task_results"] = list(artifacts.get("task_results") or [])
        last["worker_result"] = result
        verification = verifier(brief, artifacts, result)
        last["verification"] = verification
        return verification

    def recording_governor(state, verification, runtime_policy):  # noqa: ANN001
        governance_inputs["state"] = state
        governance_inputs["verification"] = verification
        governance_inputs["policy"] = runtime_policy
        return governor(state, verification, runtime_policy)

    governance_result = run_iteration(
        campaign_dir=target,
        planner=recording_planner,
        decomposer=recording_decomposer,
        launcher=None,
        verifier=recording_verifier,
        governor=recording_governor,
        launcher_factory=(
            (lambda task_packet: resolve_launcher_for_task(task_packet, registry=worker_registry))
            if worker_registry is not None
            else None
        ),
        initial_state=governor_state,
    )
    if isinstance(governance_result, dict):
        decision = governance_result["decision"]
        governance = governance_result
    else:
        decision = governance_result
        governance = campaign_state.build_governance_summary(
            decision=decision,
            state=governance_inputs.get("state", governor_state),
            verification=governance_inputs.get("verification", last.get("verification")),
            policy=policy,
        )
    record = _record_iteration_result(
        target,
        decision=decision,
        objective=initial_plan.next_objective,
        research_question=research_question,
        task_intent=task_intent,
        brain_plan=initial_plan,
        experiment_brief=last.get("experiment_brief"),
        task_packets=last.get("task_packets"),
        task_results=last.get("task_results"),
        artifacts=last.get("artifacts"),
        worker_result=last.get("worker_result"),
        verification=last.get("verification"),
        governance=governance,
        resume_metadata=resume_metadata,
        selected_candidate=selected_candidate,
        backlog_source=selected_candidate.get("source_path"),
        backlog_candidate_count=selected_candidate.get("candidate_count"),
        backlog_candidate_pool=selected_candidate.get("candidate_pool"),
    )
    state = _load_state(target)
    typer.echo(
        json.dumps(
            {
                "campaign_dir": str(target),
                "decision": decision,
                "expansion_summary": state.get("expansion_summary"),
            }
        )
    )


@app.command("run-campaign")
def run_campaign_command(
    campaign_dir: str,
    objective: str = typer.Option(..., "--objective"),
    backlog_file: str | None = typer.Option(None, "--backlog-file"),
    deliverable: list[str] = typer.Option([], "--deliverable"),
    timeout_sec: int = typer.Option(120, "--timeout-sec"),
    max_rounds: int = typer.Option(3, "--max-rounds"),
    resume: bool = typer.Option(False, "--resume"),
    decomposition_hint: str = typer.Option("single_worker", "--decomposition-hint"),
    worker_backend: str = typer.Option("any", "--worker-backend"),
) -> None:
    target = Path(campaign_dir)
    deliverables = deliverable or ["metrics.json", "result_note.md"]
    research_question = _read_question(target)
    persisted_state = _load_state(target)
    worker_registry = _load_worker_registry(target)
    iteration_payloads: list[dict] = []
    last_record = _load_resume_record(target, resume=resume)
    selected_candidate = _select_candidate(objective, backlog_file, persisted_state)
    selected_objective = selected_candidate["objective"]
    if last_record is not None:
        previous_objective = last_record.get("objective") or objective
        initial_plan = plan_next_iteration_with_candidate_transition(
            selected_objective,
            last_record,
            previous_objective=previous_objective,
            transition_context=_build_candidate_transition_context(None, selected_candidate, persisted_state),
        )
    else:
        use_transition_aware_cold_start = selected_objective != objective
        if use_transition_aware_cold_start:
            initial_plan = plan_next_iteration_with_candidate_transition(
                selected_objective,
                last_record,
                previous_objective=objective,
                transition_context=_build_candidate_transition_context(None, selected_candidate, persisted_state),
            )
        else:
            initial_plan = plan_next_iteration(selected_objective, last_record)
    resume_metadata = {"requested": True, "source_iteration": last_record.get("iteration")} if last_record is not None else None
    objective_state = {"current": initial_plan.next_objective, "plan": initial_plan, "selected_candidate": selected_candidate}
    policy = build_policy_for_mode("moderate_autonomy")

    def iteration_runner(active_campaign_dir):  # noqa: ANN001
        last: dict = {}
        governance_inputs: dict = {}
        current_objective = objective_state["current"]
        current_plan = objective_state["plan"]
        current_candidate = objective_state["selected_candidate"]
        current_governor_state = _build_governor_state(_load_state(target))
        inner_planner, inner_decomposer, inner_verifier, inner_governor = _build_iteration_components(
            target,
            current_objective,
            deliverables,
            timeout_sec,
            current_plan,
            current_candidate["hypothesis_links"],
            decomposition_hint,
            worker_backend,
        )

        def recording_planner(state, policy):  # noqa: ANN001
            brief = inner_planner(state, policy)
            last["experiment_brief"] = brief.model_dump()
            return brief

        def recording_decomposer(brief):  # noqa: ANN001
            tasks = inner_decomposer(brief)
            last["task_packets"] = tasks
            return tasks

        def recording_verifier(brief, artifacts, result):  # noqa: ANN001
            last["artifacts"] = artifacts
            last["task_results"] = list(artifacts.get("task_results") or [])
            last["worker_result"] = result
            verification = inner_verifier(brief, artifacts, result)
            last["verification"] = verification
            return verification

        def recording_governor(state, verification, runtime_policy):  # noqa: ANN001
            governance_inputs["state"] = state
            governance_inputs["verification"] = verification
            governance_inputs["policy"] = runtime_policy
            return inner_governor(state, verification, runtime_policy)

        governance_result = run_iteration(
            campaign_dir=active_campaign_dir,
            planner=recording_planner,
            decomposer=recording_decomposer,
            launcher=None,
            verifier=recording_verifier,
            governor=recording_governor,
            launcher_factory=(
                (lambda task_packet: resolve_launcher_for_task(task_packet, registry=worker_registry))
                if worker_registry is not None
                else None
            ),
            initial_state=current_governor_state,
        )
        if isinstance(governance_result, dict):
            decision = governance_result["decision"]
            governance = governance_result
        else:
            decision = governance_result
            governance = campaign_state.build_governance_summary(
                decision=decision,
                state=governance_inputs.get("state", current_governor_state),
                verification=governance_inputs.get("verification", last.get("verification")),
                policy=policy,
            )
        record = _record_iteration_result(
            active_campaign_dir,
            decision=decision,
            objective=current_objective,
            research_question=research_question,
            task_intent=derive_task_intent(current_plan).model_dump(),
            brain_plan=current_plan,
            experiment_brief=last.get("experiment_brief"),
            task_packets=last.get("task_packets"),
            task_results=last.get("task_results"),
            artifacts=last.get("artifacts"),
            worker_result=last.get("worker_result"),
            verification=last.get("verification"),
            governance=governance,
            resume_metadata=resume_metadata,
            selected_candidate=current_candidate,
            backlog_source=current_candidate.get("source_path"),
            backlog_candidate_count=current_candidate.get("candidate_count"),
            backlog_candidate_pool=current_candidate.get("candidate_pool"),
        )
        iteration_payloads.append(record)
        latest_state = _load_state(target)
        # After the first round, campaign continuation should evolve from durable campaign state,
        # not repeatedly restart selection from the original backlog file snapshot.
        next_candidate = _select_candidate(objective, None, latest_state)
        transition_context = _build_candidate_transition_context(current_candidate, next_candidate, latest_state)
        next_plan = plan_next_iteration_with_candidate_transition(
            next_candidate["objective"],
            record,
            previous_objective=current_candidate.get("objective"),
            transition_context=transition_context,
        )
        objective_state["selected_candidate"] = next_candidate
        objective_state["plan"] = next_plan
        objective_state["current"] = next_plan.next_objective
        return decision

    decisions = run_campaign_loop(
        target,
        iteration_runner=iteration_runner,
        max_rounds=max_rounds,
    )
    if not iteration_payloads:
        current_plan = initial_plan
        for decision in decisions:
            current_governor_state = _build_governor_state(_load_state(target))
            governance = campaign_state.build_governance_summary(
                decision=decision,
                state=current_governor_state,
                verification=None,
                policy=policy,
            )
            record = _record_iteration_result(
                target,
                decision=decision,
                objective=current_plan.next_objective,
                research_question=research_question,
                task_intent=derive_task_intent(current_plan).model_dump(),
                brain_plan=current_plan,
                governance=governance,
                resume_metadata=resume_metadata,
                selected_candidate=selected_candidate,
                backlog_source=selected_candidate.get("source_path"),
                backlog_candidate_count=selected_candidate.get("candidate_count"),
                backlog_candidate_pool=selected_candidate.get("candidate_pool"),
            )
            current_plan = plan_next_iteration(selected_objective, record)
    state = _load_state(target)
    typer.echo(
        json.dumps(
            {
                "campaign_dir": str(target),
                "decisions": decisions,
                "expansion_summary": state.get("expansion_summary"),
            }
        )
    )
