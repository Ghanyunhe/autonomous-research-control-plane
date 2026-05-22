# Scientific Validity Hardening And Result Note Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten the scientific-validity verifier contract and allow `result_note.md` to satisfy the MVP explanation requirement when launcher summaries are thin.

**Architecture:** Keep the work localized to `src/controlplane/verifier/completion_judge.py` and `tests/test_verifier.py`. First harden the test contract around summary-only boundary cases, then extend the verifier to read a single optional note file and judge combined explanatory text under `scientific_validity` emphasis only.

**Tech Stack:** Python 3.11+, pytest, pathlib

---

### Task 1: Add failing verifier tests for summary boundaries and result-note behavior

**Files:**
- Modify: `tests/test_verifier.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_verify_completion_marks_scientific_validity_when_summary_is_empty() -> None:
    ...


def test_verify_completion_marks_scientific_validity_when_summary_is_too_short() -> None:
    ...


def test_verify_completion_accepts_thin_summary_when_result_note_contains_findings(tmp_path: Path) -> None:
    ...


def test_verify_completion_rejects_thin_summary_when_result_note_is_also_weak(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run test to verify the new coverage fails for the expected reason**

Run: `pytest tests/test_verifier.py -q`
Expected: FAIL because the current verifier only checks `worker_result.summary` and does not yet use `result_note.md` as explanatory evidence.

- [ ] **Step 3: Do not modify production code yet**

```text
Keep the verifier implementation untouched until the new note-backed scientific-validity tests fail in the expected way.
```

### Task 2: Implement combined summary-and-note scientific-validity checking

**Files:**
- Modify: `src/controlplane/verifier/completion_judge.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Add a helper that reads optional explanatory note text**

```python
def load_result_note_text(brief: dict, artifacts: dict) -> str:
    ...
```

- [ ] **Step 2: Combine summary and note text for scientific-validity evaluation**

```python
summary_text = worker_result.get("summary", "")
note_text = load_result_note_text(brief, artifacts)
combined_text = "\n".join(part for part in [summary_text, note_text] if part)
```

- [ ] **Step 3: Reuse the existing heuristic on the combined text**

```python
if (
    acceptance_emphasis == "scientific_validity"
    and worker_result["status"] == "success"
    and not has_minimal_scientific_explanation(combined_text)
):
    ...
```

- [ ] **Step 4: Keep missing/unreadable note files non-fatal**

```python
try:
    ...
except OSError:
    return ""
```

- [ ] **Step 5: Run the focused verifier tests**

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

Run: `git diff -- src/controlplane/verifier/completion_judge.py tests/test_verifier.py docs/superpowers/specs/2026-05-19-scientific-validity-hardening-and-result-note-design.md docs/superpowers/plans/2026-05-19-scientific-validity-hardening-and-result-note.md`
Expected: Only verifier logic, verifier tests, and short design/plan docs appear.

- [ ] **Step 3: Commit the implementation**

```bash
git add src/controlplane/verifier/completion_judge.py tests/test_verifier.py docs/superpowers/specs/2026-05-19-scientific-validity-hardening-and-result-note-design.md docs/superpowers/plans/2026-05-19-scientific-validity-hardening-and-result-note.md
git commit -m "feat: harden scientific validity verification"
```
