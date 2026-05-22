# Scientific Validity MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal verifier heuristic that emits `scientific_validity` failures when scientific-validity-focused tasks produce only operational or insufficient summaries.

**Architecture:** Keep the change localized to `src/controlplane/verifier/completion_judge.py` and `tests/test_verifier.py`. The verifier will gate the new heuristic behind `acceptance_emphasis == "scientific_validity"` and use a tiny summary-based check rather than inspecting deliverable files.

**Tech Stack:** Python 3.11+, pytest

---

### Task 1: Add failing verifier tests for scientific-validity emphasis

**Files:**
- Modify: `tests/test_verifier.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_verify_completion_marks_scientific_validity_when_summary_is_operational_only() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "rework"
    assert "scientific_validity" in report["failed_check_types"]
    assert "insufficient_scientific_explanation" in report["failures"]
    assert report["recommended_brain_action"] == "REFINE"


def test_verify_completion_accepts_scientific_validity_when_summary_contains_findings() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Evaluate robustness",
        "acceptance_emphasis": "scientific_validity",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "The experiment suggests robustness drops under noise, with evidence from the reported metrics.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]


def test_verify_completion_leaves_non_scientific_emphasis_unchanged_for_thin_summary() -> None:
    brief = {
        "deliverables": ["metrics.json"],
        "objective": "Generate metrics",
        "acceptance_emphasis": "artifact_presence",
    }
    artifacts = {"deliverable_paths": ["metrics.json"]}
    worker_result = {
        "status": "success",
        "task_id": "task_1",
        "summary": "Created metrics.json successfully.",
    }

    report = verify_completion(brief, artifacts, worker_result)

    assert report["status"] == "accept"
    assert "scientific_validity" not in report["failed_check_types"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verifier.py -q`
Expected: FAIL because the verifier does not yet emit `scientific_validity` based on summary quality.

- [ ] **Step 3: Do not modify production code yet**

```text
Keep the verifier implementation untouched until the new scientific-validity tests fail for the expected reason.
```

### Task 2: Implement a minimal scientific-validity heuristic

**Files:**
- Modify: `src/controlplane/verifier/completion_judge.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Add a small helper that judges whether a summary looks scientifically meaningful**

```python
def has_minimal_scientific_explanation(summary: str) -> bool:
    ...
```

- [ ] **Step 2: Gate the new check behind scientific-validity emphasis**

```python
if (
    acceptance_emphasis == "scientific_validity"
    and worker_result["status"] == "success"
    and not has_minimal_scientific_explanation(worker_result.get("summary", ""))
):
    failures.append("insufficient_scientific_explanation")
    failed_check_types.append("scientific_validity")
```

- [ ] **Step 3: Reuse the existing status and recommendation flow**

```python
status = "accept" if not failures else "rework"
recommended_brain_action = "CONTINUE" if status == "accept" else "REFINE"
```

- [ ] **Step 4: Run the focused verifier tests**

Run: `pytest tests/test_verifier.py -q`
Expected: PASS

### Task 3: Verify the project remains green

**Files:**
- Modify: `src/controlplane/verifier/completion_judge.py`
- Modify: `tests/test_verifier.py`
- Test: `tests/`

- [ ] **Step 1: Run the full test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 2: Review the scoped diff**

Run: `git diff -- src/controlplane/verifier/completion_judge.py tests/test_verifier.py docs/superpowers/specs/2026-05-19-scientific-validity-mvp-design.md docs/superpowers/plans/2026-05-19-scientific-validity-mvp.md`
Expected: Only the verifier logic, tests, and short design/plan docs appear.

- [ ] **Step 3: Commit the implementation**

```bash
git add src/controlplane/verifier/completion_judge.py tests/test_verifier.py docs/superpowers/specs/2026-05-19-scientific-validity-mvp-design.md docs/superpowers/plans/2026-05-19-scientific-validity-mvp.md
git commit -m "feat: add scientific validity verifier heuristic"
```
