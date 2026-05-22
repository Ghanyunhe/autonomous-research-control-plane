from __future__ import annotations

from elp_atlas import AtlasNode, CandidateTask, ELPAtlasConfig, ProbeResult, RoundCheckpoint, SkillRecord
from elp_atlas.atlas import state as atlas_state
from elp_atlas.checkpoints import manifest
from elp_atlas.eval import domain_a, domain_b
from elp_atlas.generation import filtering
from elp_atlas.probe import harness
from elp_atlas.rewards import cheap_elp
from elp_atlas.skills import encoding


def test_elp_atlas_root_exports_core_models() -> None:
    assert AtlasNode is not None
    assert CandidateTask is not None
    assert ELPAtlasConfig is not None
    assert ProbeResult is not None
    assert RoundCheckpoint is not None
    assert SkillRecord is not None


def test_elp_atlas_future_seam_modules_import() -> None:
    assert atlas_state is not None
    assert manifest is not None
    assert domain_a is not None
    assert domain_b is not None
    assert filtering is not None
    assert harness is not None
    assert cheap_elp is not None
    assert encoding is not None
