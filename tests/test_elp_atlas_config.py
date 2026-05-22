from __future__ import annotations

from elp_atlas.config import ELPAtlasConfig


def test_elp_atlas_config_accepts_defaults() -> None:
    config = ELPAtlasConfig()
    assert config.experiment_name == "elp_atlas_mvp"
    assert config.phase_label == "phase1_program_skeleton"
    assert config.atlas.assignment_similarity_threshold == 0.78


def test_elp_atlas_config_round_trip() -> None:
    config = ELPAtlasConfig()
    dumped = config.model_dump()
    restored = ELPAtlasConfig.model_validate(dumped)
    assert restored == config
