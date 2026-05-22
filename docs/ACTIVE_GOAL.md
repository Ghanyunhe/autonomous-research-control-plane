# Active Goal

## Status

`paused`

This goal is intentionally paused at a stable green baseline. It is not declared complete.

Pause snapshot:

- success criteria `1` through `6`: treated as proved
- success criterion `7`: still `partial`
- latest focused authoritative verification:
  - `pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py -q`
  - `342 passed in 19.69s`

Resume starting point:

- use [`docs/COMPLETION_AUDIT.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md) as the source of truth for what remains open
- prioritize criterion `7`, especially richer multi-hypothesis evolution semantics, richer campaign backlog evolution semantics, and stronger backend realism

## Goal

Deliver a production-shaped autonomous research workflow foundation for `autonomous_research_campaign` that can run a single research-question campaign end-to-end with clear `Brain / Dispatcher / Verifier / Governor` boundaries, reliable execution, structured verification, evidence-aware iteration, durable campaign state, failure recovery, and operator-visible traceability, while remaining extensible toward multi-worker, multi-hypothesis, and backlog-driven research automation.

## Success Criteria

- A single research question can be executed as a real multi-round campaign, not just a one-off task run.
- Each round produces durable, inspectable state: objective, task packet, worker result, artifacts, verification outcome, governance decision, and next-step rationale.
- The system cleanly distinguishes execution failure, artifact failure, insufficient scientific explanation, successful continuation, and hold/escalation cases.
- Verification uses real workflow outputs, including worker summaries and research-facing artifacts such as `result_note.md`, not only process status.
- Failure paths produce actionable recovery behavior: continue, refine, hold, or escalate.
- A human operator can understand what happened in a campaign from saved state and iteration traces without reading internal code.
- The architecture stays modular and ready for later expansion to multi-worker, multi-hypothesis, and backlog-driven workflows.

## Non-Goals

- Full autonomous science or deep scientific reasoning.
- Broad workflow orchestration beyond the research campaign domain.
- Heavyweight or opaque evaluation where deterministic checks are sufficient.
- Full multi-worker parallel execution unless required to complete the single-question production workflow.
- Complete hypothesis/evidence graph infrastructure in this phase.
- Feature breadth over workflow completeness, correctness, and extensibility.

## Milestone Themes

- End-to-end campaign reliability
- Artifact and evidence quality
- Verifier maturity
- Brain and governance quality
- Durable campaign memory
- Operator traceability
- Protocol hardening
- Expansion readiness
