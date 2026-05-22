# Scientific Validity Hardening And Result Note Design

## Summary

This increment takes the existing `scientific_validity` MVP one step further in two tightly related ways:

1. harden the heuristic contract with better boundary tests
2. allow the verifier to inspect `result_note.md` as a lightweight evidence source in addition to `worker_result.summary`

The goal is to move from:

- “summary-only keyword heuristic”

to:

- “summary plus optional result-note content, still cheap and deterministic”

without turning the verifier into a full semantic evaluator.

## Problem

The current MVP emits a real `scientific_validity` signal, which is useful, but it still has two major limitations:

- its boundary behavior is under-specified in tests
- it only reads `worker_result.summary`, even though many runs already produce `result_note.md`, which is a more natural place to explain findings

That means:

- the heuristic is easier to accidentally regress
- a good run with a thin launcher summary but a meaningful `result_note.md` may be judged too harshly

## Goals

- Add explicit tests for empty/short summary behavior under `scientific_validity`.
- Make verifier judgment less dependent on launcher summary wording alone.
- Support a lightweight “summary or result note can satisfy the explanation requirement” rule.
- Keep the implementation cheap, deterministic, and local to the verifier.

## Non-Goals

- No deep NLP or LLM-based review.
- No broad file parsing beyond a single expected note file.
- No changes to launcher output schema.
- No cross-file evidence graph or artifact manifest.

## Chosen Approach

The verifier will gain a small helper that gathers explanatory text from two places:

1. `worker_result.summary`
2. `result_note.md` if it is present in `artifacts["deliverable_paths"]` and readable from the repo path context

The scientific-validity heuristic will judge the combined explanatory text instead of summary alone.

This preserves the MVP shape while making the signal more aligned with how campaign outputs are already written.

For safety and scope:

- the file check only targets `result_note.md`
- the verifier only attempts to read it when scientific-validity emphasis is active
- unreadable or missing note files should not crash verification; they simply contribute no extra explanatory text

## Expected Behavior

Under `scientific_validity` emphasis:

- empty or very short summary with no note should still fail
- thin operational summary with a meaningful `result_note.md` should pass
- thin operational summary with a thin `result_note.md` should still fail

Under non-scientific emphasis:

- verifier behavior should stay unchanged even if `result_note.md` exists

## Testing Strategy

Add test-first coverage for:

- empty summary under scientific-validity emphasis
- short operational summary under scientific-validity emphasis
- thin summary plus meaningful `result_note.md` passing
- thin summary plus weak `result_note.md` failing
- non-scientific emphasis ignoring note-file semantics

The implementation is complete when the new verifier tests fail first, pass after the verifier update, and the full suite remains green.
