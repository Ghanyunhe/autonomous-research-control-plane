# Scientific Validity MVP Design

## Summary

This change adds a minimal `scientific_validity` verification signal to the control plane so the verifier can distinguish between:

- a task that executed successfully
- a task that also produced a minimally meaningful research explanation

The scope is intentionally narrow:

- only change the verifier logic and its tests
- only enable the new check when `acceptance_emphasis == "scientific_validity"`
- do not inspect deliverable file contents
- do not add heavyweight scientific review logic

## Problem

The verifier currently checks only:

- artifact presence
- worker execution status

But the rest of the system already understands `scientific_validity`:

- the schema includes it as a failed check type
- `TaskIntent` can request it as an `acceptance_emphasis`
- the Brain already knows how to refine around it

So the signal exists in the protocol but never gets emitted by runtime verification.

## Goals

- Emit a real `scientific_validity` failure in at least one meaningful runtime case.
- Keep the check cheap, deterministic, and text-only.
- Restrict the new behavior to workflows that explicitly ask for scientific-validity emphasis.
- Preserve existing verifier behavior for `balanced` and `artifact_presence` emphasis.

## Non-Goals

- No file parsing of `result_note.md` or other deliverables.
- No LLM-based judgment.
- No deep semantic research scoring.
- No changes to Brain schemas, Governor, or CLI contracts.

## Chosen Approach

When `acceptance_emphasis == "scientific_validity"` and the worker run is otherwise successful enough to evaluate, the verifier will inspect `worker_result["summary"]` using a very small heuristic.

It will treat the result as scientifically insufficient when the summary is missing, too thin, or purely operational without any sign of conclusion/evidence language.

Examples of summary characteristics that should count as insufficient:

- empty summary
- very short summary with no substantive explanation
- operational-only text such as “done”, “created metrics.json”, or similar artifact-only status text

Examples of summary characteristics that should count as sufficient for this MVP:

- mentions a finding, conclusion, result, evidence, hypothesis, or similar research-oriented explanation
- contains a minimally descriptive explanation of what was learned, not just that files were produced

When the heuristic fails, the verifier should:

- append `insufficient_scientific_explanation` to `failures`
- append `scientific_validity` to `failed_check_types`
- return `status == "rework"`
- return `recommended_brain_action == "REFINE"`

This new failure should combine naturally with the existing artifact/execution checks and feed the Brain’s existing refinement logic.

## Expected Behavior

If a scientific-validity-focused task succeeds technically but returns a summary like “created metrics.json”, the verifier should reject it as `rework` with `scientific_validity`.

If a scientific-validity-focused task succeeds and returns a summary like “The robustness experiment suggests the baseline degrades under noise, with metrics indicating a 12% drop”, the verifier should accept it if no other checks fail.

If `acceptance_emphasis` is not `scientific_validity`, the new check should stay dormant so existing non-analysis workflows keep their current verifier behavior.

## Testing Strategy

Add test-first coverage in `tests/test_verifier.py` for:

- scientific-validity emphasis + operational-only summary -> `scientific_validity` failure
- scientific-validity emphasis + research-style summary -> accepted if other checks pass
- non-scientific emphasis + thin summary -> unchanged existing behavior
- combined failure case where scientific validity stacks with another verifier failure

The implementation is complete when the new verifier tests fail before code changes, pass after the heuristic is added, and the full test suite remains green.
