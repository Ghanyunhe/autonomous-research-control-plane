# Agent Handoff

## Phase Status

This project phase is intentionally paused at a stable green baseline.

That means:

- the current workflow foundation is considered strong enough to stop on purpose
- the goal is not declared complete
- future work should resume from the remaining `partial` in [`docs/COMPLETION_AUDIT.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md), not by reopening already-proved criteria

Pause snapshot:

- success criteria `1` through `6`: treated as proved
- success criterion `7`: still `partial`
- latest focused authoritative verification:
  - `pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py -q`
  - `342 passed in 19.69s`

## Project Background

`autonomous_research_campaign/` is a greenfield MVP for a multi-agent control plane focused on a single research question campaign.

The design goal is not "one agent does the whole experiment", but:

- `Brain` decides how research should progress
- `Decomposer` turns that into bounded execution tasks
- `Dispatcher` picks a worker backend
- `Verifier` checks whether the round actually succeeded
- `Governor` decides whether to continue, refine, escalate, or stop

The intended long-term shape is a control plane that can coordinate heterogeneous agents such as Claude Code, Codex, and OpenCode, while keeping decision-making, execution, verification, and governance separated.

## Why This Directory Exists

This subtree was created as a standalone implementation sandbox. It does not depend on the rest of the repository's existing pipeline code.

That was deliberate:

- keep the architecture greenfield while ideas were still moving fast
- make it easy for future agents to refactor the control plane without worrying about unrelated repo behavior
- allow real launcher integration experiments without touching the older system

## Current Architecture

Source lives under `src/controlplane/`.

Main modules:

- `brain/`
  - `objective_evolver.py`: turns the last round into a structured `NextIterationPlan`
  - `task_intent.py`: converts a research plan into a thin execution intent
  - `decomposer.py`: turns intent + brief into a `TaskPacket`
  - `planner.py`: very small backlog scoring helper
- `dispatcher/`
  - `router.py`: default worker registry plus worker selection
  - `launchers/claude_code.py`: real local `ccb` launcher
  - `launchers/codex.py`: stub launcher for now
- `verifier/`
  - `completion_judge.py`: MVP verifier
- `governor/`
  - `presets.py`: autonomy mode presets
  - `decisions.py`: simple continue/refine/escalate/stop logic
- `orchestrator/`
  - `iteration_loop.py`: one bounded round
  - `campaign_loop.py`: multi-round loop
- `schemas/`
  - `ExperimentBrief`
  - `TaskIntent`
  - `TaskPacket`
  - `WorkerResult`
  - `VerificationReport`
- `cli.py`
  - `init`
  - `run-iteration`
  - `run-campaign`

Current control flow:

1. CLI or caller creates a base objective
2. `plan_next_iteration()` creates a `NextIterationPlan`
3. `derive_task_intent()` creates a `TaskIntent`
4. `decompose_experiment()` creates one bounded `TaskPacket`
5. `resolve_launcher_for_task()` chooses a backend
6. Worker runs
7. `verify_completion()` returns a structured verification result
8. Governor returns `CONTINUE`, `REFINE`, `ESCALATE`, or `STOP`
9. CLI records iteration artifacts to disk

## What Is Implemented

### Core MVP

- Single-question campaign loop
- Structured Brain output:
  - `next_objective`
  - `strategy`
  - `reason`
  - `focus_areas`
- Thin `TaskIntent` protocol between Brain and Decomposer
- Task intent currently controls:
  - `task_type`
  - `worker_preference`
  - `acceptance_emphasis`
- Default routing layer with:
  - `claude_code` primary
  - `codex` secondary
- Real local Claude Code open-source launcher via `ccb`
- Iteration and campaign CLI commands
- Campaign memory files:
  - `campaign_state.json`
  - `latest_iteration.json`
  - `iteration_log.jsonl`

### Verification Layer

Verifier currently emits:

- `status`
- `failures`
- `failed_check_types`
- `rework_priority`
- `warnings`
- `recommended_brain_action`

Current failed check types:

- `artifact_presence`
- `worker_execution`
- reserved in schema: `scientific_validity`

### Local Claude Code Integration

`ClaudeCodeLauncher` is not a stub.

It uses local `ccb` and supports:

- prompt-based non-interactive execution
- repo path injection via `--add-dir`
- bypass permissions mode
- root-safe fallback to a dedicated non-root user

Important environment fact:

- direct `ccb` execution as root is blocked by Claude Code safety rules
- launcher now auto-switches to user `ccbagent` when current process is root
- `ccbagent` home is `/home/ccbagent`
- that user has a working Claude config under `/home/ccbagent/.claude/settings.json`

This was already validated with a real local demo run that successfully produced:

- `demo_ccb_run/metrics.json`
- `demo_ccb_run/result_note.md`

## Current State of the Code

The MVP is functional, but still intentionally narrow.

What is stable enough to build on:

- module boundaries
- CLI flow
- Brain -> TaskIntent -> Decomposer -> Dispatcher wiring
- real `ccb` launcher path
- iteration/campaign result recording
- test suite

What is still shallow:

- Brain is still heuristic, not a real research planner
- Decomposer only supports `single_worker`
- Codex launcher is still stubbed
- Verifier is still artifact/execution heavy
- Governor barely uses structured verification richness
- no real backlog/hypothesis store beyond minimal scaffolding
- no true multi-worker parallel experiment execution yet

## Important Files for a New Agent

Read these first:

- [`README.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/README.md)
- [`src/controlplane/cli.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/cli.py)
- [`src/controlplane/brain/objective_evolver.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/objective_evolver.py)
- [`src/controlplane/brain/task_intent.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/task_intent.py)
- [`src/controlplane/brain/decomposer.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/decomposer.py)
- [`src/controlplane/dispatcher/router.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/dispatcher/router.py)
- [`src/controlplane/dispatcher/launchers/claude_code.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/dispatcher/launchers/claude_code.py)
- [`src/controlplane/verifier/completion_judge.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/verifier/completion_judge.py)
- [`src/controlplane/governor/decisions.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/governor/decisions.py)

If changing protocol boundaries, also read:

- [`src/controlplane/schemas/task_intent.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/task_intent.py)
- [`src/controlplane/schemas/task_packet.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/task_packet.py)
- [`src/controlplane/schemas/verification_report.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/schemas/verification_report.py)

## Execution Progress So Far

Completed design/protocol milestones:

- initial greenfield implementation plan
- multi-agent control plane design plan
- MVP plan
- MVP code scaffold
- real `ccb` launcher integration
- CLI-based iteration loop
- CLI-based multi-round campaign loop
- per-round persistence to campaign files
- Brain plan persistence
- TaskIntent protocol
- Brain influence over task type and worker preference
- Brain influence over verifier acceptance emphasis
- structured verification output with rework priority

Verification milestone:

- `pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py -q`
- latest confirmed result: `342 passed in 19.64s`

## Known Constraints and Caveats

### Functional Limits

- Campaign objectives still originate from CLI text, not a durable research backlog
- `run-campaign` evolves one base objective rather than selecting from a real experiment queue
- no real hypothesis confidence updates yet
- no real scientific validity checks yet
- no artifact manifest or evidence graph yet

### Environment Limits

- `ccb` depends on the local machine environment
- non-root execution matters
- if `ccbagent` disappears or its Claude config breaks, launcher behavior will regress

### Code Quality Limits

- several pieces still return plain dicts rather than schema instances through the full runtime path
- CLI still owns more orchestration glue than an eventual library-first design probably should
- verifier/governor integration is still MVP-grade

## Recommended Next Directions

### Current Completion Boundary

This sandbox is not blocked on broken functionality.

The current stopping point is audit-driven:

- success criteria `1` through `6` are treated as proved in [`docs/COMPLETION_AUDIT.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md)
- success criterion `7` remains `partial`

The remaining gap is not "can the campaign run?" It can.
The remaining gap is that broader expansion-readiness is still only directly proved up to a lightweight tracked model plus guidance.

### Highest-Value Future Work

1. Strengthen richer multi-hypothesis evolution semantics

- move beyond the current lightweight tracked frontier, reserve memory, pair memory, and divergence memory seams
- add broader exercised evidence for longer-lived population dynamics such as repeated promotion, suppression, revival, and cross-round reranking under real resumed workflows
- prefer live-policy and persisted-runtime evidence over additional wording polish

2. Strengthen richer campaign backlog evolution semantics

- move beyond the current lightweight tracked candidate reprioritization model
- add broader exercised evidence for a richer evolving backlog frontier, not only active-candidate swaps plus a few strong override seams
- prefer planner-backed backlog evolution behavior over more operator-facing micro-traceability

3. Reduce dependence on fake or patched launcher realism

- the CLI workflow evidence is now strong, including many real Codex and subprocess-backed paths
- the next realism step is less about more parallel proof variants and more about reducing reliance on fake binaries or patched launchers for the strongest end-to-end stories

### What Should Not Be the Default Next Step

Lower-leverage directions now include:

- additional operator-summary wording tweaks
- more micro-traceability fields with no policy impact
- more single-path twin proofs that do not materially strengthen criterion `7`

### Good First Files For The Next Agent

- [`docs/COMPLETION_AUDIT.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md)
- [`docs/EXTENSION_SEAMS.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/EXTENSION_SEAMS.md)
- [`tests/test_cli.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/tests/test_cli.py)
- [`src/controlplane/cli.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/cli.py)
- [`src/controlplane/state/campaign_state.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/state/campaign_state.py)
- [`src/controlplane/brain/objective_evolver.py`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/brain/objective_evolver.py)

- match the launcher shape already used for `ccb`

4. Support multi-worker decomposition

- `multi_worker_serial`
- `multi_worker_parallel`

5. Move campaign logic out of CLI over time

- keep CLI as entrypoint
- shift more reusable orchestration into library modules

## How to Run the Project

Initialize a demo campaign:

```bash
cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign
python -m controlplane.cli init ./demo_campaign --question "Does method X help Y?"
```

Run one round:

```bash
python -m controlplane.cli run-iteration ./demo_campaign \
  --objective "Create metrics.json and result_note.md for a bounded demo task" \
  --deliverable metrics.json \
  --deliverable result_note.md
```

Run multiple rounds:

```bash
python -m controlplane.cli run-campaign ./demo_campaign \
  --objective "Create metrics.json and result_note.md for a bounded demo task" \
  --deliverable metrics.json \
  --deliverable result_note.md \
  --max-rounds 3
```

Run tests:

```bash
pytest autonomous_research_campaign/tests -q
```

## Suggested Handoff Prompt for the Next Agent

Use this if you want to start a fresh handoff session quickly:

```text
You are taking over the greenfield control-plane MVP in autonomous_research_campaign/.
Read docs/AGENT_HANDOFF.md first, then inspect the Brain -> TaskIntent -> Decomposer -> Dispatcher -> Verifier -> Governor flow.
Assume the current state is a working MVP with a real ccb-backed ClaudeCodeLauncher, a stub CodexLauncher, and 41 passing tests.
Prefer incremental improvements that preserve the current protocol boundaries.
```
