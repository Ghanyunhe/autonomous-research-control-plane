# Verifier-Action-Aware Brain Planning Design

## Summary

This change makes `plan_next_iteration()` prefer the verifier's structured `recommended_brain_action` when it is available, instead of relying only on `last_record.decision`.

The scope remains intentionally small:

- keep `NextIterationPlan` unchanged
- keep CLI, Governor, and Verifier schemas unchanged
- localize the behavior change to `src/controlplane/brain/objective_evolver.py`
- extend only the Brain's action-selection logic and its tests

## Problem

The verifier already returns a direct recommendation about what the Brain should do next:

- `CONTINUE`
- `REFINE`
- future values such as `ESCALATE`, `STOP`, or `PIVOT`

But `plan_next_iteration()` currently ignores this field and chooses its branch from `last_record.decision` only. That means the Brain can understand:

- what failed
- how severe the rework is

but still cannot consume the verifier's direct suggestion for the next reasoning step.

## Goals

- Make `recommended_brain_action` the Brain's preferred action signal when present.
- Preserve the existing structured `REFINE` behavior already added for failed check types.
- Allow verifier-driven `CONTINUE` planning even when `last_record.decision` is not `CONTINUE`.
- Treat verifier-driven `ESCALATE`, `STOP`, and `PIVOT` conservatively without expanding scope.

## Non-Goals

- No Governor policy changes.
- No CLI recording format changes.
- No schema changes.
- No new action types in Brain output.
- No orchestration rewiring between Governor and Brain.

## Chosen Approach

`plan_next_iteration()` will derive an `effective_action` using this precedence:

1. `verification.recommended_brain_action` when present
2. `last_record.decision` otherwise

Then it will branch on that effective action:

- `REFINE`: reuse the existing structured-refinement path
- `CONTINUE`: reuse the current continuation path based on worker summary
- `ESCALATE`, `STOP`, `PIVOT`: return a conservative `hold` strategy that preserves the base objective and explains that verifier recommended a non-continuation action

This keeps the runtime model small while allowing the Brain to benefit from verifier intent immediately.

## Expected Behavior

If `decision` is `ESCALATE` but verifier recommends `CONTINUE`, the Brain should produce a continuation plan based on the successful worker result.

If `decision` is `CONTINUE` but verifier recommends `REFINE`, the Brain should produce a refine plan and still use structured failed check handling when available.

If verifier recommends `ESCALATE`, `STOP`, or `PIVOT`, the Brain should not continue or refine. It should return a `hold` strategy with a reason that makes the verifier-originated recommendation explicit.

If `recommended_brain_action` is missing, existing behavior should remain intact.

## Testing Strategy

Add test-first coverage in `tests/test_objective_evolver.py` for:

- verifier `CONTINUE` overriding a non-continue `decision`
- verifier `REFINE` overriding a non-refine `decision`
- verifier `ESCALATE` producing a conservative hold result
- verifier `STOP` or `PIVOT` also producing conservative hold behavior
- backward compatibility when `recommended_brain_action` is absent

The implementation is complete when the new tests fail before code changes, pass after the Brain update, and the full test suite remains green.
