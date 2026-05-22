# ELP-Atlas Implementation Campaign Plan

> **For future agents:** This is a campaign plan for using `autonomous_research_campaign` to autonomously advance the implementation of the `ELP-Atlas` research design captured in [`../research_design.md`](/vepfs_hyh/hyh/projects/AutoResearchClaw/research_design.md). It is not a claim that the current control plane already implements ELP-Atlas end-to-end.

## Goal

Use the current control-plane architecture to autonomously advance the implementation of **ELP-Atlas: Learning-Progress Guided Self-Evolution with Capability Atlas** as a staged research-engineering campaign.

The control plane is responsible for:

- deciding the next bounded research-engineering objective
- dispatching implementation or analysis work
- verifying deliverables and evidence quality
- governing continue/refine/hold/escalate behavior
- persisting campaign state and rationale across rounds

The control plane is **not** expected to already contain the full ELP-Atlas training stack. This campaign exists to build that stack incrementally.

## Why This Needs A Campaign Plan

`research_design.md` is a research blueprint:

- it defines the paper story
- it defines algorithmic components
- it defines domains, baselines, and training logic
- it defines what an eventual full system should prove

But the current control plane needs a narrower contract for each round:

- a bounded objective
- expected deliverables
- verifier-visible success checks
- escalation boundaries
- an exit condition for the current phase

This plan is the compilation layer between:

- the high-level ELP-Atlas design
- the current single-question autonomous research workflow foundation

## Campaign Architecture

The current repository should play four roles in the ELP-Atlas effort:

1. **Research program manager**
- tracks phases, blocked seams, evidence, and next-step rationale

2. **Implementation orchestrator**
- drives bounded code, experiment-harness, and analysis tasks

3. **Evidence gate**
- refuses to treat a phase as complete unless required artifacts and evaluation traces exist

4. **Durable memory layer**
- keeps the ELP-Atlas implementation campaign resumable and inspectable across rounds

The future ELP-Atlas implementation modules themselves will live beside or under the current repository as new training, evaluation, and data-generation components.

## Scope Boundary

### What This Campaign Should Implement

- planning and protocol support for managing the ELP-Atlas buildout
- phased implementation of:
  - capability-atlas data structures
  - skill abstraction scaffolding
  - ELP scoring proxies
  - probe-update evaluation harness
  - domain-specific benchmark harnesses
  - candidate generation, filtering, and replay memory scaffolds
  - solver/challenger round-loop orchestration
  - anti-regression evaluation
- experiment artifacts and verifier-visible evidence for those phases

### What This Campaign Should Not Assume Up Front

- a single round will produce a full working ELP-Atlas system
- the current verifier can already judge scientific merit of learning-progress claims without added artifacts
- the current Brain/task protocol is already rich enough for training-heavy workflows
- the existing launcher layer is already sufficient for long-running training/eval execution without refinement

## Recommended Campaign Phases

The control plane should treat the ELP-Atlas implementation as a sequence of bounded phases.

### Phase 0: Research Design Ingestion And Execution Contract

Purpose:

- translate `research_design.md` into concrete implementation seams, deliverables, and verifier expectations

Exit criteria:

- a committed campaign plan exists
- phase definitions, artifacts, and evaluation contracts are explicit
- future agents can start implementation without rereading the whole design document

Expected deliverables:

- this campaign plan
- optionally a matching design/spec if protocol changes are large

### Phase 1: Minimal ELP-Atlas Program Skeleton

Purpose:

- create the code skeleton for the ELP-Atlas implementation without claiming algorithmic completeness

Suggested module seams:

- `elp_atlas/atlas/`
- `elp_atlas/skills/`
- `elp_atlas/rewards/`
- `elp_atlas/probe/`
- `elp_atlas/generation/`
- `elp_atlas/eval/`
- `elp_atlas/config/`

Exit criteria:

- importable package/module layout exists
- configuration surface is explicit
- placeholder schema objects exist for:
  - candidate task
  - skill record
  - atlas node
  - probe result
  - round checkpoint

Expected deliverables:

- package skeleton
- baseline config files
- smoke tests for importability and serialization contracts

### Phase 2: Capability Atlas MVP

Purpose:

- implement the smallest real `Capability Atlas` that can store skill-node state and update it from observed signals

Core MVP behaviors:

- create or assign skill nodes from skill embeddings
- update node statistics:
  - competence
  - uncertainty
  - learning progress
  - forgetting risk
  - density
- persist atlas state across rounds

Exit criteria:

- atlas node assignment works on synthetic examples
- state update rules are tested
- atlas snapshot can be persisted and reloaded

Expected deliverables:

- atlas data model
- online assignment logic
- update logic tests
- example atlas state artifact

### Phase 3: Skill Abstraction And Candidate Schema MVP

Purpose:

- implement the structured candidate/skill record surface that the rest of ELP-Atlas depends on

Core MVP behaviors:

- represent:
  - problem/request
  - answer/verifier
  - skill tags
  - reasoning ops
  - failure modes
  - difficulty rationale
- support math/reasoning and tool-use variants

Exit criteria:

- structured skill records can be generated for synthetic tasks
- skill encoding path is explicit
- verifier can at least validate schema-level completeness

Expected deliverables:

- candidate task schema
- skill record schema
- synthetic fixtures for Domain A and Domain B

### Phase 4: Cheap ELP Scoring MVP

Purpose:

- implement the cheapest credible learning-progress proxy before probe updates

Core MVP behaviors:

- score novelty
- score frontier proximity
- estimate noise
- expose placeholder or real gradient-alignment scoring path

Important boundary:

- this phase does not need full solver training yet
- it does need a stable scoring contract and artifact outputs

Exit criteria:

- candidate scorer runs on synthetic batches
- score breakdown is persisted
- verifier can check for score completeness and ranking output

Expected deliverables:

- cheap ELP scorer
- scored candidate batch artifact
- tests covering score-field presence and ranking behavior

### Phase 5: Probe Update And Regression Check Harness

Purpose:

- implement the more expensive reranking path that estimates learning progress and regression after a temporary update

Core MVP behaviors:

- create a short-lived probe adapter/update
- evaluate before/after delta on:
  - frontier memory
  - old memory
- compute:
  - probe learning progress
  - regression penalty

Exit criteria:

- probe harness can run on a tiny synthetic or mocked solver
- outputs are serialized and testable
- failure to produce probe evidence is distinguishable from ordinary execution failure

Expected deliverables:

- probe harness module
- serialized probe result artifact
- tests for delta and regression calculation plumbing

### Phase 6: Domain A Benchmark Harness MVP

Purpose:

- give the campaign a real evaluation surface for math/reasoning

Core MVP behaviors:

- run a tiny benchmark subset or controlled synthetic proxy
- emit structured evaluation summaries
- persist per-domain metrics

Exit criteria:

- Domain A harness runs end-to-end on a tiny supported set
- benchmark artifact format is stable
- verifier can check that eval artifacts exist and are sufficiently populated

Expected deliverables:

- Domain A harness
- benchmark result schema
- tiny benchmark smoke test

### Phase 7: Domain B Tool-Use Harness MVP

Purpose:

- ensure ELP-Atlas is not hard-wired to only one domain

Core MVP behaviors:

- mock tool schemas
- executable mock tools
- deterministic tool-call verification

Exit criteria:

- Domain B harness runs on a held-out synthetic set
- tool-use result artifacts are persisted
- verifier can distinguish malformed tool outputs from genuine benchmark failure

Expected deliverables:

- mock tool registry
- tool-use benchmark harness
- result artifacts and tests

### Phase 8: Candidate Generation And Filtering Loop MVP

Purpose:

- make candidate generation, filtering, and shortlist creation concrete

Core MVP behaviors:

- generate candidate batches for target nodes
- filter invalid / noisy / leaky / oversized candidates
- attach skill records
- keep top-k per node

Exit criteria:

- a candidate batch can be produced and filtered
- shortlist artifacts are persisted
- filtering reasons are inspectable

Expected deliverables:

- generation/filter loop
- shortlist artifact
- tests for rejection reasons and shortlist balancing

### Phase 9: Solver Training Loop MVP

Purpose:

- add a bounded solver-update path with real artifact outputs, even if initially tiny or mocked

Core MVP behaviors:

- accept a selected train batch
- run a minimal update routine
- emit training summary artifacts
- persist checkpoint metadata

Exit criteria:

- a tiny solver-update round completes
- artifacts distinguish:
  - selected train batch
  - update config
  - checkpoint identity
  - training summary

Expected deliverables:

- solver update harness
- checkpoint metadata artifact
- training summary artifact

### Phase 10: Challenger Update Loop MVP

Purpose:

- close the other half of the self-evolution loop

Core MVP behaviors:

- consume rewards
- update the challenger/generator
- persist reward and update summaries

Exit criteria:

- tiny challenger update completes
- reward summaries and update metadata are durable

Expected deliverables:

- challenger update harness
- reward artifact
- update summary artifact

### Phase 11: Anti-Regression And Historical Memory MVP

Purpose:

- make anti-regression a first-class phase instead of a future note

Core MVP behaviors:

- persist old memory / replay memory
- run regression checks on old skills
- optionally track historical checkpoints for future TPAW-style comparisons

Exit criteria:

- regression artifact exists
- verifier can fail a round if regression evidence is missing or degraded past threshold

Expected deliverables:

- replay memory schema
- regression result artifact
- historical checkpoint manifest

### Phase 12: End-to-End Tiny ELP-Atlas Round

Purpose:

- prove that a tiny, bounded version of the intended ELP-Atlas loop can run end-to-end through the control plane

Core MVP behaviors:

- sample target nodes
- generate candidates
- filter
- score
- probe
- select train batch
- update solver
- evaluate
- update atlas
- save checkpoint

Exit criteria:

- all expected artifacts exist
- verifier can judge completeness of the round
- governor can meaningfully continue/refine/escalate based on the evidence

Expected deliverables:

- end-to-end round artifact bundle
- campaign state showing rationale for continuation or refinement

## Control-Plane Changes Required

To manage the ELP-Atlas buildout well, this repository will likely need control-plane upgrades before or during the above phases.

### 1. Richer TaskIntent Types

Current `TaskIntent` is still optimized for bounded analysis/coding/refine work.

Needed additions may include:

- `experiment_harness_build`
- `training_loop_implementation`
- `benchmark_integration`
- `probe_evaluation`
- `artifact_audit`
- `checkpoint_analysis`

### 2. Richer Verifier Contracts

The verifier must learn how to check:

- benchmark result completeness
- score artifact completeness
- checkpoint metadata completeness
- replay/regression evidence presence
- candidate shortlist quality signals

This does **not** require a full scientific evaluator up front. It does require more domain-aware deterministic artifact checks.

### 3. Richer Artifact Schema Expectations

The campaign should converge on standard artifact families such as:

- `atlas_state.json`
- `skill_records.jsonl`
- `candidate_scores.jsonl`
- `probe_results.json`
- `benchmark_results.json`
- `training_summary.json`
- `checkpoint_manifest.json`
- `regression_report.json`

### 4. Potential Decomposition Upgrades

Some phases may benefit from `multi_worker_serial`, for example:

- design/review first
- implementation second
- artifact audit third

But the control plane should only widen decomposition when a phase genuinely benefits from it.

## Round Contract Template For This Campaign

Each ELP-Atlas round should aim to produce:

- `objective`
- `task_packets`
- `worker_result`
- `artifacts`
- `verification`
- `governance`
- `round_summary`
- `operator_summary`

And, for ELP-Atlas-specific rounds, ideally also:

- implementation artifact(s)
- test or benchmark artifact(s)
- explicit result note explaining:
  - what was added
  - what was verified
  - what remains missing
  - what the next round should do

## Verifier Expectations By Phase

The verifier should judge phases differently.

### Early build phases

Prefer deterministic checks:

- module/file exists
- schema serializes
- tests pass
- required artifact files exist

### Mid-loop phases

Prefer structured artifact completeness:

- candidate scoring outputs present
- benchmark outputs present
- probe outputs present
- checkpoint metadata present

### Late end-to-end phases

Require:

- all expected round artifacts
- coherent `result_note.md`
- enough evidence to support continue vs refine

## Governance Guidance

Recommended governance defaults for this campaign:

- `continue`
  - when required artifacts exist and tests/evals are sufficient for the current phase
- `refine`
  - when the implementation exists but evidence artifacts are thin, missing, or internally inconsistent
- `hold`
  - when a phase boundary is reached but the next milestone needs explicit human reprioritization
- `escalate`
  - when long-running training/eval infrastructure or resource constraints exceed the repository's current safe orchestration assumptions

## Phase Ordering Recommendation

Recommended order:

1. Phase 0: design ingestion and campaign contract
2. Phase 1: program skeleton
3. Phase 2: capability atlas MVP
4. Phase 3: skill abstraction and candidate schema MVP
5. Phase 4: cheap ELP scoring MVP
6. Phase 5: probe update and regression harness
7. Phase 6: Domain A harness MVP
8. Phase 7: Domain B harness MVP
9. Phase 8: generation/filter loop MVP
10. Phase 9: solver training loop MVP
11. Phase 10: challenger update loop MVP
12. Phase 11: anti-regression and historical memory MVP
13. Phase 12: tiny end-to-end ELP-Atlas round

This order favors:

- explicit data contracts first
- evaluation and scoring seams before heavier training loops
- tiny end-to-end proof only after the core artifacts and checks exist

## What Counts As Success For This Campaign

This campaign is successful when the current control plane can autonomously advance ELP-Atlas implementation through bounded phases with:

- clear objectives
- durable artifacts
- meaningful verifier decisions
- resumable state
- credible next-step rationale

It does **not** require the full final paper result to exist before the campaign itself is considered successful.

## Immediate Next Step

The best next implementation step after this plan is:

- add the minimum protocol and artifact expectations needed for **Phase 1: Minimal ELP-Atlas Program Skeleton**

That keeps the first execution target small, testable, and aligned with the current control-plane strengths.
