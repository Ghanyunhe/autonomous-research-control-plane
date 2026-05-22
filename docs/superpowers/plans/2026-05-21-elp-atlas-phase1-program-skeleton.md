# ELP-Atlas Phase 1 Program Skeleton Implementation Plan

> **For agentic workers:** Use this plan to implement the first executable phase of the ELP-Atlas campaign. The goal is not to build training logic yet. The goal is to create a stable program skeleton, configuration surface, and schema contract that the control plane can reason about in later phases.

## Goal

Implement **Phase 1: Minimal ELP-Atlas Program Skeleton** from [`2026-05-21-elp-atlas-implementation-campaign.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/docs/superpowers/plans/2026-05-21-elp-atlas-implementation-campaign.md).

This phase should establish:

- an importable `elp_atlas` package layout
- explicit configuration entrypoints
- placeholder schema/data objects for core ELP-Atlas entities
- smoke-test coverage for imports and serialization
- enough artifact and documentation structure that later phases can plug in cleanly

## Non-Goals

This phase must **not** try to implement:

- real training loops
- real solver/challenger updates
- real gradient-alignment scoring
- real probe updates
- full benchmark integration
- full launcher/runtime integration for long-running jobs

If any task starts drifting into those areas, stop and narrow back to skeleton and contract work.

## Architecture

Create a new top-level package under `src/`:

- `src/elp_atlas/__init__.py`
- `src/elp_atlas/config/`
- `src/elp_atlas/schemas/`
- `src/elp_atlas/atlas/`
- `src/elp_atlas/skills/`
- `src/elp_atlas/rewards/`
- `src/elp_atlas/probe/`
- `src/elp_atlas/generation/`
- `src/elp_atlas/eval/`
- `src/elp_atlas/checkpoints/`

The first version should keep logic intentionally shallow and deterministic:

- config objects: typed and serializable
- schema objects: typed and serializable
- package modules: importable placeholders with clear docstrings
- no heavy runtime dependencies beyond the current project baseline unless required

Use the current repository style:

- Python 3.11+
- Pydantic models where structured serialization matters
- pytest for smoke coverage

## Deliverables

At the end of Phase 1, the repository should contain:

1. Importable package skeleton
- `elp_atlas` package and subpackages

2. Core schema contracts
- candidate task schema
- skill record schema
- atlas node schema
- probe result schema
- round checkpoint schema

3. Config surface
- root config model for ELP-Atlas runs
- nested config sections for:
  - atlas
  - generation
  - rewards
  - probe
  - evaluation
  - checkpoints

4. Minimal docs
- a short module-level README or doc section describing what each subpackage is for

5. Tests
- import smoke tests
- schema serialization / round-trip tests
- config default tests

## Task Breakdown

### Task 1: Add the importable `elp_atlas` package skeleton

**Files:**
- Add: `src/elp_atlas/__init__.py`
- Add: `src/elp_atlas/config/__init__.py`
- Add: `src/elp_atlas/schemas/__init__.py`
- Add: `src/elp_atlas/atlas/__init__.py`
- Add: `src/elp_atlas/skills/__init__.py`
- Add: `src/elp_atlas/rewards/__init__.py`
- Add: `src/elp_atlas/probe/__init__.py`
- Add: `src/elp_atlas/generation/__init__.py`
- Add: `src/elp_atlas/eval/__init__.py`
- Add: `src/elp_atlas/checkpoints/__init__.py`

- [ ] Create the package tree with minimal module docstrings
- [ ] Keep each package purpose explicit and narrow
- [ ] Do not add placeholder code that implies unsupported runtime behavior

**Definition of done:**
- `import elp_atlas` works
- each subpackage imports cleanly

### Task 2: Define core schema models

**Files:**
- Add: `src/elp_atlas/schemas/candidate_task.py`
- Add: `src/elp_atlas/schemas/skill_record.py`
- Add: `src/elp_atlas/schemas/atlas_node.py`
- Add: `src/elp_atlas/schemas/probe_result.py`
- Add: `src/elp_atlas/schemas/round_checkpoint.py`
- Modify: `src/elp_atlas/schemas/__init__.py`

- [ ] Add a `CandidateTask` model with the minimal fields needed by future phases:
  - `problem`
  - `reference_answer`
  - `verifier`
  - `skill_record`
  - optional metadata fields for rationale or difficulty
- [ ] Add a `SkillRecord` model capturing the structured skill surface from the research design
- [ ] Add an `AtlasNode` model with state fields for competence, uncertainty, learning progress, forgetting risk, density, and bookkeeping IDs
- [ ] Add a `ProbeResult` model with before/after metrics, learning-progress estimate, and regression estimate
- [ ] Add a `RoundCheckpoint` model capturing round id, artifact pointers, config snapshot, and summary metadata
- [ ] Export the models from `schemas/__init__.py`

**Definition of done:**
- all schema models serialize and parse cleanly
- field naming is stable enough for later artifact contracts

### Task 3: Define the ELP-Atlas config surface

**Files:**
- Add: `src/elp_atlas/config/models.py`
- Modify: `src/elp_atlas/config/__init__.py`

- [ ] Add nested config models for:
  - atlas settings
  - generation settings
  - reward settings
  - probe settings
  - evaluation settings
  - checkpoint settings
- [ ] Add one top-level `ELPAtlasConfig`
- [ ] Keep defaults intentionally small and local-test friendly
- [ ] Avoid embedding real training hyperparameter claims unless already grounded in the design

**Definition of done:**
- config can be instantiated with defaults
- config can be dumped to and loaded from structured JSON-like data

### Task 4: Add minimal package placeholders for future logic seams

**Files:**
- Add: `src/elp_atlas/atlas/state.py`
- Add: `src/elp_atlas/skills/encoding.py`
- Add: `src/elp_atlas/rewards/cheap_elp.py`
- Add: `src/elp_atlas/probe/harness.py`
- Add: `src/elp_atlas/generation/filtering.py`
- Add: `src/elp_atlas/eval/domain_a.py`
- Add: `src/elp_atlas/eval/domain_b.py`
- Add: `src/elp_atlas/checkpoints/manifest.py`

- [ ] Add minimal placeholder functions or classes with explicit docstrings
- [ ] Keep signatures narrow and honest
- [ ] Prefer `NotImplementedError` over fake behavior where runtime semantics are not yet defined

**Definition of done:**
- the future insertion points exist
- later phases can modify focused files rather than invent structure from scratch

### Task 5: Add smoke and serialization tests

**Files:**
- Add: `tests/test_elp_atlas_schemas.py`
- Add: `tests/test_elp_atlas_config.py`
- Add: `tests/test_elp_atlas_imports.py`

- [ ] Add import smoke tests for the package and key submodules
- [ ] Add round-trip schema tests for:
  - `SkillRecord`
  - `CandidateTask`
  - `AtlasNode`
  - `ProbeResult`
  - `RoundCheckpoint`
- [ ] Add config default tests and config dump/load tests

**Definition of done:**
- tests fail before implementation
- tests pass after implementation

### Task 6: Add a short orientation doc for the new package

**Files:**
- Add: `docs/ELP_ATLAS_SKELETON.md`
- Modify: `docs/README.md`

- [ ] Write a short doc that explains:
  - why `elp_atlas/` exists
  - what is real in Phase 1
  - what is intentionally stubbed
  - how future phases should extend the package
- [ ] Link it from `docs/README.md`

**Definition of done:**
- a new agent can find the package purpose without reading every module

## Testing Strategy

Run at least:

```bash
pytest tests/test_elp_atlas_imports.py tests/test_elp_atlas_schemas.py tests/test_elp_atlas_config.py -q
```

Then run a broader regression slice:

```bash
pytest tests/test_task_intent.py tests/test_campaign_state.py tests/test_cli.py tests/test_objective_evolver.py tests/test_elp_atlas_imports.py tests/test_elp_atlas_schemas.py tests/test_elp_atlas_config.py -q
```

The goal is to prove:

- the new package skeleton is valid
- the new config/schema contracts are stable
- the existing control-plane foundation remains green

## Verification Expectations

For this phase, verifier-style completion should require:

- package and modules exist
- import smoke tests pass
- schema round-trip tests pass
- config tests pass
- a short orientation doc exists

This phase should **not** require:

- benchmark results
- training summaries
- checkpoint learning deltas
- end-to-end solver/challenger loops

## Risks

### Risk 1: Overbuilding the skeleton

Symptom:
- too much fake implementation appears in placeholder modules

Mitigation:
- keep modules shallow
- prefer docstrings and explicit `NotImplementedError`

### Risk 2: Under-specifying schemas

Symptom:
- Phase 2 and Phase 3 immediately need schema churn

Mitigation:
- include the small set of fields clearly implied by `research_design.md`
- do not collapse everything into generic `dict` fields

### Risk 3: Letting config imply unsupported behavior

Symptom:
- defaults read like the system already trains full models

Mitigation:
- keep defaults lightweight and descriptive
- separate contract presence from implementation completeness

## Expected Outcome

After this phase:

- the repository has a real home for ELP-Atlas implementation work
- the control plane has a stable contract to reference in later phases
- future rounds can implement atlas logic, skill abstraction, scoring, and evaluation without reopening package structure questions

## Commit Boundary

If implemented in one change set, the scoped diff should mostly include:

- `src/elp_atlas/**`
- `tests/test_elp_atlas_*.py`
- `docs/ELP_ATLAS_SKELETON.md`
- `docs/README.md`
- this plan document if updated during implementation
