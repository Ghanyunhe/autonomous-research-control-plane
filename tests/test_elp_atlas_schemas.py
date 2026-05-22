from __future__ import annotations

from elp_atlas.schemas import AtlasNode, CandidateTask, ProbeResult, RoundCheckpoint, SkillRecord


def test_skill_record_round_trip() -> None:
    record = SkillRecord(
        domain="math",
        skill_tags=["linear_equation", "entity_tracking"],
        reasoning_ops=["extract_quantities", "solve_equation"],
        failure_modes_targeted=["entity_confusion"],
        dependency_tags=["arithmetic"],
        difficulty_estimate=0.62,
        notes="Synthetic fixture",
    )
    restored = SkillRecord.model_validate(record.model_dump())
    assert restored == record


def test_candidate_task_round_trip() -> None:
    candidate = CandidateTask(
        task_id="cand_1",
        domain="math",
        problem="If x + 2 = 5, what is x?",
        reference_answer="3",
        verifier={"type": "exact_match", "spec": {"normalize_whitespace": True}},
        skill_record={
            "domain": "math",
            "skill_tags": ["linear_equation"],
            "reasoning_ops": ["solve_equation"],
            "failure_modes_targeted": ["sign_error"],
        },
        solution_outline="Subtract 2 from both sides.",
        difficulty_rationale="Single-step equation.",
        anti_leakage_check="No answer leak.",
        metadata={"seed": "fixture"},
    )
    restored = CandidateTask.model_validate(candidate.model_dump())
    assert restored == candidate


def test_atlas_node_round_trip() -> None:
    node = AtlasNode(
        node_id="skill_1",
        centroid_key="math.linear_equation",
        competence=0.45,
        uncertainty=0.10,
        learning_progress=0.05,
        forgetting_risk=0.02,
        density=1.8,
        sample_count=12,
        transfer_targets=["skill_2"],
        notes="Synthetic node",
    )
    restored = AtlasNode.model_validate(node.model_dump())
    assert restored == node


def test_probe_result_round_trip() -> None:
    result = ProbeResult(
        probe_id="probe_1",
        skill_node_id="skill_1",
        before_score=0.33,
        after_score=0.41,
        learning_progress_estimate=0.08,
        regression_estimate=0.01,
        eval_set_sizes={"frontier": 32, "old": 64},
        notes="Synthetic probe result",
    )
    restored = ProbeResult.model_validate(result.model_dump())
    assert restored == result


def test_round_checkpoint_round_trip() -> None:
    checkpoint = RoundCheckpoint(
        round_id=1,
        phase_label="phase1_program_skeleton",
        config_snapshot={"experiment_name": "elp_atlas_mvp"},
        artifact_paths=["artifacts/elp_atlas/round_1.json"],
        metrics={"schema_tests_passed": 1.0},
        summary="Skeleton artifacts persisted.",
    )
    restored = RoundCheckpoint.model_validate(checkpoint.model_dump())
    assert restored == checkpoint
