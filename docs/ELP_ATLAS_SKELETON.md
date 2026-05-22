# ELP-Atlas Skeleton

## Purpose

`src/elp_atlas/` is the implementation home for the future ELP-Atlas research system.

It is intentionally separate from [`src/controlplane/`](/vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign/src/controlplane/), which remains the orchestration layer for multi-round autonomous research campaigns.

## What Is Real In Phase 1

Phase 1 establishes:

- a real importable Python package
- explicit config models
- explicit schema models
- named module seams for future atlas, skills, reward, probe, generation, evaluation, and checkpoint logic
- smoke and serialization tests

## What Is Intentionally Stubbed

Phase 1 does **not** implement:

- real capability-atlas logic
- real skill encoding
- real learning-progress scoring
- real probe updates
- real domain benchmarks
- real solver or challenger training loops

Those modules currently expose honest placeholders that raise `NotImplementedError` instead of pretending to work.

## How Future Phases Should Extend This Package

- Phase 2 should deepen `elp_atlas/atlas/`
- Phase 3 should deepen `elp_atlas/schemas/` and `elp_atlas/skills/`
- Phase 4 should deepen `elp_atlas/rewards/`
- Phase 5 should deepen `elp_atlas/probe/`
- later phases should deepen `elp_atlas/eval/`, `elp_atlas/generation/`, and `elp_atlas/checkpoints/`

The control plane should continue to manage those implementation phases as bounded campaign rounds, rather than absorbing ELP-Atlas logic into `src/controlplane/`.
