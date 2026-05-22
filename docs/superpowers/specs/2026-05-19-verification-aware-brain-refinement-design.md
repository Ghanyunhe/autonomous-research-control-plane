# Verification-Aware Brain Refinement Design

## Summary

This change upgrades the Brain's iteration-planning behavior so `plan_next_iteration()` reacts to structured verifier output instead of relying only on the coarse `decision` and string failure list.

The scope is intentionally narrow:

- keep the existing `NextIterationPlan` schema unchanged
- keep `CONTINUE` and non-`REFINE` behavior stable unless a test requires otherwise
- improve `REFINE` behavior by reading `verification.failed_check_types` and `verification.rework_priority`

## Problem

The verifier already emits structured signals:

- `failed_check_types`
- `rework_priority`
- `recommended_brain_action`

But the Brain currently ignores most of that structure. During `REFINE`, it only copies `verification.failures` into free-form text and `focus_areas`. This means the next objective does not meaningfully distinguish between:

- a missing artifact
- a worker execution failure
- a future scientific validity failure

As a result, the control plane has richer verifier data than the Brain can use.

## Goals

- Make `REFINE` plans sensitive to verifier failure categories.
- Preserve the existing public shape of `NextIterationPlan`.
- Keep the change local to the Brain planning layer and its tests.
- Produce clearer `focus_areas`, `reason`, and `next_objective` text for follow-up rounds.

## Non-Goals

- No schema changes to `VerificationReport` or `NextIterationPlan`.
- No CLI behavior changes.
- No dispatcher, governor, or verifier refactor.
- No new persistence format.

## Chosen Approach

`plan_next_iteration()` will normalize verification input into a small set of refinement signals derived from:

- `failed_check_types`
- `rework_priority`
- fallback `failures`

During `REFINE`, it will build a targeted follow-up objective:

- `artifact_presence` maps to a recovery focus on regenerating and validating required deliverables
- `worker_execution` maps to a recovery focus on stabilizing execution and resolving runtime or tool failures
- `scientific_validity` maps to a recovery focus on strengthening experimental rigor, evidence, or reasoning

If more than one failed check type is present, the next objective should mention all applicable recovery concerns. `focus_areas` should prefer these structured categories over raw failure strings.

`rework_priority` will influence the wording of the reason:

- `high` should signal urgent remediation before expansion
- `medium` and `low` should still indicate refinement, but with less urgency

If structured fields are absent, the Brain should fall back to the current behavior so older records remain supported.

## Expected Behavior

For a `REFINE` decision with `failed_check_types=["artifact_presence"]`, the next iteration should emphasize recreating missing outputs and validating deliverables.

For `failed_check_types=["worker_execution"]`, the next iteration should emphasize fixing execution reliability before attempting broader progress.

For `failed_check_types=["scientific_validity"]`, the next iteration should emphasize improving evidence quality, methodology, or answer quality rather than only rerunning.

For mixed failure categories, the next iteration should mention combined remediation goals and set `focus_areas` to the structured categories in a stable order.

## Testing Strategy

Add test-first coverage in `tests/test_objective_evolver.py` for:

- artifact-focused refinement
- worker-execution-focused refinement
- scientific-validity-focused refinement
- mixed structured failures with high rework priority
- fallback behavior when structured verification data is missing

The implementation is complete when the new tests fail before code changes, pass after the Brain update, and the full project test suite stays green.
