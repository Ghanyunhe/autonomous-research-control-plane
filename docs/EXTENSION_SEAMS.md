# Extension Seams

This document records the current extension seams in `autonomous_research_campaign`. It is not a promise that expansion is complete. It is a map of where future work is expected to plug in without collapsing the existing module boundaries.

## Purpose

The control plane now has enough structure that future work should extend explicit seams rather than cut across modules ad hoc. This document identifies those seams so later agents can build on the current workflow foundation with less guesswork.

## Brain Seams

- [src/controlplane/brain/objective_evolver.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/objective_evolver.py:1)
  - consumes last-round `verification`, `worker_result`, and decision state
  - current seam for:
    - richer research-memory consumption
    - richer verifier-action handling
    - future backlog/hypothesis-aware planning
- [src/controlplane/brain/task_intent.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/task_intent.py:1)
  - converts strategy into a bounded execution intent
  - current seam for:
    - richer task classes
    - worker preferences
    - additional acceptance modes
- [src/controlplane/brain/planner.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/planner.py:1)
  - thin backlog scoring seam
  - current placeholder for backlog-driven campaign selection

## Dispatcher Seams

- [src/controlplane/dispatcher/router.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/dispatcher/router.py:1)
  - worker selection seam
  - current place to introduce:
    - multi-worker routing policies
    - richer worker capabilities
    - task-type-aware placement
- launchers:
  - [src/controlplane/dispatcher/launchers/claude_code.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/dispatcher/launchers/claude_code.py:1)
  - [src/controlplane/dispatcher/launchers/codex.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/dispatcher/launchers/codex.py:1)
  - current seam for adding heterogeneous execution backends without changing Brain or Verifier contracts

## Verifier Seams

- [src/controlplane/verifier/completion_judge.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/verifier/completion_judge.py:1)
  - current seam for:
    - richer artifact interpretation
    - stronger scientific-validity checks
    - evidence-aware evaluation
  - outputs structured signals already consumed downstream:
    - `failed_check_types`
    - `rework_priority`
    - `recommended_brain_action`

## Governor Seams

- [src/controlplane/governor/decisions.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/governor/decisions.py:1)
  - now owns structured governance decision records
  - seam for:
    - richer governance policies
    - human-review requirements
    - budget/escalation evolution
- [src/controlplane/governor/presets.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/governor/presets.py:1)
  - seam for autonomy-policy expansion

## State Seams

- [src/controlplane/state/campaign_state.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/state/campaign_state.py:1)
  - central derived-state seam
  - currently owns:
    - lifecycle
    - campaign summary
    - governance summary fallback
    - campaign memory
    - memory summary
    - continuation anchor
    - resume readiness
  - future seam for:
    - richer research memory
    - hypothesis/evidence summaries
    - operator-facing campaign reports

## Orchestrator Seams

- [src/controlplane/orchestrator/iteration_loop.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/orchestrator/iteration_loop.py:1)
  - bounded per-round orchestration seam
  - current place to evolve:
    - multi-task rounds
    - richer launcher lifecycles
    - stronger result aggregation
- [src/controlplane/orchestrator/campaign_loop.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/orchestrator/campaign_loop.py:1)
  - multi-round loop seam
  - future place for:
    - backlog-driven round selection
    - campaign-level stop/pause rules

## CLI And Persistence Seams

- [src/controlplane/cli.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/cli.py:1)
  - persistence and entrypoint seam
  - should remain focused on:
    - file I/O
    - CLI parameters
    - wiring modules together
  - should not become the long-term home for research semantics that belong in Brain, Verifier, Governor, or State

## Schema Seams

- [src/controlplane/schemas/task_intent.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/task_intent.py:1)
- [src/controlplane/schemas/task_packet.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/task_packet.py:1)
- [src/controlplane/schemas/verification_report.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/verification_report.py:1)
- [src/controlplane/schemas/worker_result.py](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/worker_result.py:1)

These are the most important protocol seams to extend carefully. Any future multi-worker, hypothesis-aware, or backlog-driven work should prefer schema evolution over hidden ad hoc dict growth.

## Current Readiness Claim

What this document supports:

- the architecture has identifiable module and protocol seams for expansion
- later work has clear insertion points
- expansion can happen with less risk of collapsing boundaries

What this document does not prove:

- that multi-worker, multi-hypothesis, or backlog-driven behavior is already implemented
- that every seam is stable under real external integrations
- that future expansion will require no refactoring
