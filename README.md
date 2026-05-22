# Autonomous Research Control Plane

A greenfield control-plane sandbox for running autonomous research as a multi-round campaign instead of a single one-off agent task.

The project separates:

- `Brain`: decides what the next round should try
- `Decomposer`: turns that decision into bounded work
- `Dispatcher`: routes work to a backend
- `Verifier`: checks whether the round actually produced a usable result
- `Governor`: decides whether to continue, refine, hold, or escalate

The current shape is intentionally narrow: one research question, bounded rounds, durable state, and strong CLI-level workflow evidence.

## What It Does

Today this repository can:

- run a single research question as a real multi-round campaign
- persist round-by-round campaign state to disk
- resume from durable state with `run-iteration --resume` and `run-campaign --resume`
- route execution through launcher backends such as Claude Code and Codex
- verify outcomes using artifacts and research-facing summaries, not only process success
- steer follow-up behavior through structured `continue`, `refine`, `hold`, and `escalate` decisions
- exercise backlog-driven, multi-hypothesis, and multi-worker-serial seams in tests

## Why This Exists

Most "autonomous agent" demos flatten planning, execution, judging, and retry logic into one loop.

This project explores a more explicit control-plane architecture where:

- planning is separate from execution
- verification is separate from both
- governance decisions are durable and inspectable
- campaigns can be resumed and audited after each round
- richer future seams such as backlog evolution, hypothesis competition, and worker heterogeneity can be added without collapsing boundaries

## Current Status

This repository is well beyond scaffold stage.

- Core workflow status: working
- Current authoritative verification:
  - `pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py -q`
  - `342 passed in 19.69s`
- Audit status:
  - success criteria `1` through `6` are treated as proved
  - success criterion `7` remains partial

That remaining `partial` is not about basic functionality being broken. It means broader future-readiness for richer multi-hypothesis and backlog-evolution semantics is not yet proved as broadly as the rest of the system.

See [docs/COMPLETION_AUDIT.md](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md) for the criterion-by-criterion breakdown.

## Quick Start

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Run Tests

```bash
pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py -q
```

### Initialize Campaign State

```bash
controlplane init demo_state --question "Can this workflow run a bounded autonomous research campaign?"
```

### Run One Iteration

```bash
controlplane run-iteration demo_state --objective "Collect initial evidence and summarize the result."
```

### Run a Multi-Round Campaign

```bash
controlplane run-campaign demo_state --objective "Evaluate the question across multiple rounds." --max-rounds 3
```

## Architecture

Source lives under [`src/controlplane/`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/).

Main modules:

- `brain/`
  - planning, task-intent shaping, decomposition, thin backlog scoring
- `dispatcher/`
  - worker selection and launcher integration
- `verifier/`
  - completion judging and structured failure typing
- `governor/`
  - continue/refine/hold/escalate decisions
- `orchestrator/`
  - per-round and multi-round campaign loops
- `state/`
  - durable campaign/backlog/hypothesis/expansion summaries
- `cli.py`
  - persistence and entrypoints

## Repository Docs

- [docs/AGENT_HANDOFF.md](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/AGENT_HANDOFF.md): project background, current boundaries, and future work
- [docs/COMPLETION_AUDIT.md](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/COMPLETION_AUDIT.md): what is proved, what remains partial, and why
- [docs/EXTENSION_SEAMS.md](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/EXTENSION_SEAMS.md): where future backlog, hypothesis, worker, verifier, and launcher expansion should plug in

## Not Yet Done

The biggest unfinished areas are not "make the loop run at all." They are:

- richer multi-hypothesis state evolution beyond the current lightweight tracked model
- richer campaign backlog evolution beyond the current lightweight reprioritization model
- stronger end-to-end launcher realism with less dependence on fake or patched backends in the strongest workflow proofs

Those are deliberate next-step problems, not hidden breakages.

## Project Intent

This repository is a focused sandbox for control-plane architecture, not a polished end-user product.

If you are evaluating it, the most useful question is:

`Does this codebase already provide a credible, test-backed foundation for autonomous research campaigns with explicit planning, verification, governance, persistence, and future expansion seams?`

Right now, the answer is:

- yes for the workflow foundation
- not yet fully proved for the broadest future-expansion claims
