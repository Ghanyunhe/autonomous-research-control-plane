from __future__ import annotations

from elp_atlas.schemas import CandidateTask, SkillRecord


def make_math_candidate_fixture(task_id: str = "math_fixture") -> CandidateTask:
    return CandidateTask(
        task_id=task_id,
        domain="math",
        problem="If x + 2 = 5, what is x?",
        reference_answer="3",
        verifier={"type": "exact_match", "spec": {"normalize_whitespace": True}},
        skill_record=SkillRecord(
            domain="math",
            skill_tags=["linear_equation", "entity_tracking"],
            reasoning_ops=["extract_quantities", "solve_equation"],
            failure_modes_targeted=["sign_error"],
            dependency_tags=["arithmetic"],
            difficulty_estimate=0.35,
            notes="Math fixture",
        ),
        solution_outline="Subtract 2 from both sides.",
        difficulty_rationale="Single-step algebra fixture.",
        anti_leakage_check="No answer leak in the prompt.",
    )


def make_tool_use_candidate_fixture(task_id: str = "tool_fixture") -> CandidateTask:
    return CandidateTask(
        task_id=task_id,
        domain="tool_use",
        problem="Check the inventory for product 42 and reserve one unit for tomorrow.",
        reference_answer='{"tool":"reserve_item","arguments":{"product_id":42,"date":"tomorrow"}}',
        verifier={"type": "tool_call", "spec": {"tool": "reserve_item"}},
        skill_record=SkillRecord(
            domain="tool_use",
            skill_tags=["tool_selection", "argument_grounding", "multi_call_dependency"],
            reasoning_ops=["search_inventory", "reserve_item"],
            failure_modes_targeted=["wrong_tool", "missing_dependency"],
            dependency_tags=["inventory_lookup"],
            difficulty_estimate=0.58,
            notes="Tool-use fixture",
        ),
        solution_outline="Look up the product and reserve one unit.",
        difficulty_rationale="Simple two-step tool-use fixture.",
        anti_leakage_check="Reference call is not exposed in the problem text.",
    )
