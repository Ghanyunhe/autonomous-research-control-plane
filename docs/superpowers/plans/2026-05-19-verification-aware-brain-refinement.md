# Verification-Aware Brain Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `plan_next_iteration()` generate more targeted `REFINE` plans by consuming structured verifier signals such as `failed_check_types` and `rework_priority`.

**Architecture:** Keep the runtime shape unchanged and localize the behavior change to the Brain planning layer. Extend `src/controlplane/brain/objective_evolver.py` with a small normalization path for structured verification signals, then prove the behavior through focused tests in `tests/test_objective_evolver.py`.

**Tech Stack:** Python 3.11+, pytest, dataclasses, pydantic-backed schemas already present in the repo

---

### Task 1: Add failing tests for structured refinement behavior

**Files:**
- Modify: `tests/test_objective_evolver.py`
- Test: `tests/test_objective_evolver.py`

- [ ] **Step 1: Write the failing tests**

```python
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
    assert "deliverables" in plan.reason.lower()
    assert "deliverables" in plan.next_objective.lower()


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
    assert "execution" in plan.reason.lower()
    assert "stability" in plan.next_objective.lower()


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
    assert "scientific" in plan.reason.lower()
    assert "evidence" in plan.next_objective.lower()


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
    assert "urgent" in plan.reason.lower()
    assert "deliverables" in plan.next_objective.lower()
    assert "stability" in plan.next_objective.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_objective_evolver.py -q`
Expected: FAIL because the current implementation still returns raw failure strings in `focus_areas` and does not mention deliverables, stability, evidence, or urgency in the asserted ways.

- [ ] **Step 3: Commit the red test state only if your workflow requires it**

```bash
git diff -- tests/test_objective_evolver.py
```

- [ ] **Step 4: Do not add production code yet**

```text
The implementation change starts in Task 2 only after the tests fail for the expected behavioral reasons.
```

### Task 2: Implement structured refinement mapping in the Brain

**Files:**
- Modify: `src/controlplane/brain/objective_evolver.py`
- Test: `tests/test_objective_evolver.py`

- [ ] **Step 1: Write the minimal implementation**

```python
FAILED_CHECK_GUIDANCE = {
    "artifact_presence": {
        "focus": "artifact_presence",
        "reason": "required deliverables were missing",
        "objective": "Regenerate the required deliverables and validate that each expected output is present.",
    },
    "worker_execution": {
        "focus": "worker_execution",
        "reason": "worker execution was not stable",
        "objective": "Stabilize execution, resolve worker failures, and rerun the task cleanly.",
    },
    "scientific_validity": {
        "focus": "scientific_validity",
        "reason": "scientific validity checks were not satisfied",
        "objective": "Strengthen the evidence, methodology, and answer quality before continuing.",
    },
}
```

```python
structured_failures = verification.get("failed_check_types") or []
rework_priority = verification.get("rework_priority") or "medium"
```

```python
if decision == "REFINE" and structured_failures:
    guidance = [FAILED_CHECK_GUIDANCE[item] for item in structured_failures if item in FAILED_CHECK_GUIDANCE]
    focus_areas = [item["focus"] for item in guidance]
    reason_bits = [item["reason"] for item in guidance]
    objective_bits = [item["objective"] for item in guidance]
    urgency = "Urgent remediation is required because " if rework_priority == "high" else "Refinement is needed because "
    return NextIterationPlan(
        next_objective=f"{base_objective}\n\nRefine the previous attempt. {' '.join(objective_bits)}",
        strategy="refine",
        reason=f"{urgency}{'; '.join(reason_bits)}.",
        focus_areas=focus_areas,
    )
```

- [ ] **Step 2: Preserve fallback behavior for older verification records**

```python
if decision == "REFINE":
    suffix = ", ".join(failures) if failures else "the gaps surfaced in the previous attempt"
    return NextIterationPlan(
        next_objective=f"{base_objective}\n\nRefine the previous attempt. Explicitly address: {suffix}.",
        strategy="refine",
        reason=f"Previous round requested refinement because: {suffix}.",
        focus_areas=failures or ["stabilize_previous_attempt"],
    )
```

- [ ] **Step 3: Run the focused test file**

Run: `pytest tests/test_objective_evolver.py -q`
Expected: PASS

- [ ] **Step 4: Refactor only if needed to keep the file readable**

```python
def _guidance_for_failed_checks(failed_check_types: list[str]) -> list[dict[str, str]]:
    ...
```

- [ ] **Step 5: Re-run the focused test file after any refactor**

Run: `pytest tests/test_objective_evolver.py -q`
Expected: PASS

### Task 3: Verify the change against the whole project

**Files:**
- Modify: `src/controlplane/brain/objective_evolver.py`
- Modify: `tests/test_objective_evolver.py`
- Test: `tests/`

- [ ] **Step 1: Run the full test suite**

Run: `pytest -q`
Expected: PASS with all existing tests green.

- [ ] **Step 2: Review the diff for accidental scope creep**

Run: `git diff -- src/controlplane/brain/objective_evolver.py tests/test_objective_evolver.py docs/superpowers/specs/2026-05-19-verification-aware-brain-refinement-design.md docs/superpowers/plans/2026-05-19-verification-aware-brain-refinement.md`
Expected: Only the Brain logic, the new tests, and the short design/plan docs appear.

- [ ] **Step 3: Commit the implementation**

```bash
git add src/controlplane/brain/objective_evolver.py tests/test_objective_evolver.py docs/superpowers/specs/2026-05-19-verification-aware-brain-refinement-design.md docs/superpowers/plans/2026-05-19-verification-aware-brain-refinement.md
git commit -m "feat: add verification-aware brain refinement"
```
