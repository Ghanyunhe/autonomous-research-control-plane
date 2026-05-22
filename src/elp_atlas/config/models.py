from __future__ import annotations

from pydantic import BaseModel, Field


class AtlasConfig(BaseModel):
    assignment_similarity_threshold: float = 0.78
    frontier_memory_size: int = 64
    old_memory_size: int = 128
    density_penalty: float = 0.3


class GenerationConfig(BaseModel):
    num_target_nodes: int = 16
    samples_per_node: int = 8
    max_candidate_chars: int = 8000
    top_k_per_skill: int = 8


class RewardConfig(BaseModel):
    cheap_learning_progress_weight: float = 1.0
    frontier_weight: float = 0.3
    novelty_weight: float = 0.25
    noise_weight: float = 0.8
    cost_weight: float = 0.05


class ProbeConfig(BaseModel):
    enabled: bool = True
    lora_rank: int = 8
    lora_alpha: int = 16
    learning_rate: float = 2.0e-5
    steps: int = 1
    batch_size: int = 8


class EvaluationConfig(BaseModel):
    domain_a_enabled: bool = True
    domain_b_enabled: bool = True
    max_eval_examples: int = 32
    pre_eval_rollouts: int = 1


class CheckpointConfig(BaseModel):
    output_dir: str = "artifacts/elp_atlas"
    save_every_round: bool = True
    keep_historical_manifests: bool = True


class ELPAtlasConfig(BaseModel):
    experiment_name: str = "elp_atlas_mvp"
    phase_label: str = "phase1_program_skeleton"
    atlas: AtlasConfig = Field(default_factory=AtlasConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    rewards: RewardConfig = Field(default_factory=RewardConfig)
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    checkpoints: CheckpointConfig = Field(default_factory=CheckpointConfig)
