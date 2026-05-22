from __future__ import annotations

import math
from pathlib import Path

from pydantic import BaseModel, Field

from elp_atlas.schemas import AtlasNode


class AtlasState(BaseModel):
    nodes: list[AtlasNode] = Field(default_factory=list)


def _tokenize_centroid_key(value: str) -> set[str]:
    return {token for token in value.replace("-", ".").replace("_", ".").split(".") if token}


def _similarity(left: str, right: str) -> float:
    left_tokens = _tokenize_centroid_key(left)
    right_tokens = _tokenize_centroid_key(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union


def assign_skill_node(skill_key: str, atlas: AtlasState, threshold: float = 0.78) -> AtlasNode:
    if not atlas.nodes:
        node = AtlasNode(node_id="node_1", centroid_key=skill_key, sample_count=1, density=math.log(2.0))
        atlas.nodes.append(node)
        return node

    nearest = max(atlas.nodes, key=lambda node: _similarity(skill_key, node.centroid_key))
    similarity = _similarity(skill_key, nearest.centroid_key)
    if similarity < threshold:
        node = AtlasNode(
            node_id=f"node_{len(atlas.nodes) + 1}",
            centroid_key=skill_key,
            sample_count=1,
            density=math.log(2.0),
        )
        atlas.nodes.append(node)
        return node

    nearest.sample_count += 1
    nearest.density = math.log(1 + nearest.sample_count)
    if skill_key not in nearest.centroid_key:
        nearest.centroid_key = f"{nearest.centroid_key}|{skill_key}"
    return nearest


def update_atlas_node(
    node: AtlasNode,
    *,
    solver_pass_rate: float,
    observed_delta: float,
    old_competence: float,
    ema_weight: float = 0.5,
) -> AtlasNode:
    competence = ((1 - ema_weight) * node.competence) + (ema_weight * solver_pass_rate)
    learning_progress = ((1 - ema_weight) * node.learning_progress) + (ema_weight * observed_delta)
    sample_count = node.sample_count + 1
    uncertainty = math.sqrt(max(0.0, competence * (1 - competence)) / (sample_count + 1))
    forgetting_risk = max(0.0, old_competence - competence)
    density = math.log(1 + sample_count)

    return node.model_copy(
        update={
            "competence": competence,
            "learning_progress": learning_progress,
            "sample_count": sample_count,
            "uncertainty": uncertainty,
            "forgetting_risk": forgetting_risk,
            "density": density,
        }
    )


def save_atlas_state(path: Path, atlas: AtlasState) -> None:
    path.write_text(atlas.model_dump_json(indent=2))


def load_atlas_state(path: Path) -> AtlasState:
    return AtlasState.model_validate_json(path.read_text())
