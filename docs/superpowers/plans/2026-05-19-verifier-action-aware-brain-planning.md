# Verifier-Action-Aware Brain Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `plan_next_iteration()` prefer verifier `recommended_brain_action` over `last_record.decision` while keeping the current structured refinement behavior and backward compatibility.

**Architecture:** Extend the Brain planning layer with a tiny action-resolution step that derives an `effective_action` from verifier output before branching into `CONTINUE`, `REFINE`, or conservative hold behavior. Keep all changes localized to `src/controlplane/brain/objective_evolver.py` and prove them through focused tests in `tests/test_objective_evolver.py`.

**Tech Stack:** Python 3.11+, pytest, dataclasses

---

### Task 1: Add failing tests for verifier action precedence

**Files:**
- Modify: `tests/test_objective_evolver.py`
- Test: `tests/test_objective_evolver.py`

- [ ] **Step 1: Write the failing tests**

```python
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


def test_plan_next_iteration_uses_hold_for_verifier_escalate() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "CONTINUE",
            "verification": {"recommended_brain_action": "ESCALATE"},
        },
    )

    assert plan.strategy == "hold"
    assert "ESCALATE" in plan.reason


def test_plan_next_iteration_uses_hold_for_verifier_stop() -> None:
    plan = plan_next_iteration(
        "Create metrics.json",
        {
            "decision": "CONTINUE",
            "verification": {"recommended_brain_action": "STOP"},
        },
    )

    assert plan.strategy == "hold"
    assert "STOP" in plan.reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_objective_evolver.py -q`
Expected: FAIL because the current implementation still branches on `last_record.decision` before considering `verification.recommended_brain_action`.

- [ ] **Step 3: Do not edit production code yet**

```text
Keep the implementation untouched until the new tests fail for the expected precedence reason.
```

### Task 2: Implement effective action precedence in the Brain

**Files:**
- Modify: `src/controlplane/brain/objective_evolver.py`
- Test: `tests/test_objective_evolver.py`

- [ ] **Step 1: Add effective action resolution**

```python
recommended_action = verification.get("recommended_brain_action")
effective_action = recommended_action or decision
```

- [ ] **Step 2: Route planning branches through the effective action**

```python
if effective_action == "REFINE":
    ...

if effective_action == "CONTINUE":
    ...
```

- [ ] **Step 3: Add conservative handling for verifier-driven hold-like actions**

```python
if effective_action in {"ESCALATE", "STOP", "PIVOT"}:
    return NextIterationPlan(
        next_objective=base_objective,
        strategy="hold",
        reason=f"Verifier recommended {effective_action}, so the base objective is retained pending higher-level handling.",
        focus_areas=[],
    )
```

- [ ] **Step 4: Preserve existing fallback behavior when no verifier action is present**

```python
return NextIterationPlan(
    next_objective=base_objective,
    strategy="hold",
    reason=f"Previous decision was {decision or 'unknown'}, so the base objective is retained.",
    focus_areas=[],
)
```

- [ ] **Step 5: Run the focused test file**

Run: `pytest tests/test_objective_evolver.py -q`
Expected: PASS

### Task 3: Verify the full project remains green

**Files:**
- Modify: `src/controlplane/brain/objective_evolver.py`
- Modify: `tests/test_objective_evolver.py`
- Test: `tests/`

- [ ] **Step 1: Run the full test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 2: Review the scoped diff**

Run: `git diff -- src/controlplane/brain/objective_evolver.py tests/test_objective_evolver.py docs/superpowers/specs/2026-05-19-verifier-action-aware-brain-planning-design.md docs/superpowers/plans/2026-05-19-verifier-action-aware-brain-planning.md`
Expected: Only the Brain logic, the new tests, and the short design/plan docs appear.

- [ ] **Step 3: Commit the implementation**

```bash
git add src/controlplane/brain/objective_evolver.py tests/test_objective_evolver.py docs/superpowers/specs/2026-05-19-verifier-action-aware-brain-planning-design.md docs/superpowers/plans/2026-05-19-verifier-action-aware-brain-planning.md
git commit -m "feat: prefer verifier brain action in iteration planning"
```
