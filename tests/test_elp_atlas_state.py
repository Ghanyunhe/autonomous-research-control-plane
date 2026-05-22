from __future__ import annotations

from pathlib import Path

from elp_atlas.atlas.state import (
    AtlasState,
    assign_skill_node,
    load_atlas_state,
    save_atlas_state,
    update_atlas_node,
)
from elp_atlas.schemas import AtlasNode


def test_assign_skill_node_creates_first_node_for_empty_atlas() -> None:
    atlas = AtlasState()
    node = assign_skill_node("math.linear_equation", atlas, threshold=0.78)

    assert node.node_id == "node_1"
    assert node.centroid_key == "math.linear_equation"
    assert atlas.nodes == [node]


def test_assign_skill_node_reuses_existing_node_when_similarity_is_high() -> None:
    atlas = AtlasState(
        nodes=[
            AtlasNode(
                node_id="node_1",
                centroid_key="math.linear_equation",
                competence=0.3,
                uncertainty=0.1,
                density=1.0,
                sample_count=3,
            )
        ]
    )

    node = assign_skill_node("math.linear_equation.variant", atlas, threshold=0.50)

    assert node.node_id == "node_1"
    assert len(atlas.nodes) == 1
    assert atlas.nodes[0].sample_count == 4


def test_assign_skill_node_creates_new_node_when_similarity_is_low() -> None:
    atlas = AtlasState(
        nodes=[
            AtlasNode(
                node_id="node_1",
                centroid_key="math.linear_equation",
                competence=0.3,
                uncertainty=0.1,
                density=1.0,
                sample_count=3,
            )
        ]
    )

    node = assign_skill_node("tool_use.multi_call_dependency", atlas, threshold=0.90)

    assert node.node_id == "node_2"
    assert len(atlas.nodes) == 2


def test_update_atlas_node_updates_statistics_from_observed_signals() -> None:
    node = AtlasNode(
        node_id="node_1",
        centroid_key="math.linear_equation",
        competence=0.20,
        uncertainty=0.30,
        learning_progress=0.05,
        forgetting_risk=0.10,
        density=1.0,
        sample_count=4,
    )

    updated = update_atlas_node(
        node,
        solver_pass_rate=0.80,
        observed_delta=0.25,
        old_competence=0.20,
    )

    assert updated.sample_count == 5
    assert updated.competence > 0.20
    assert updated.learning_progress > 0.05
    assert updated.forgetting_risk == 0.0
    assert updated.density > 1.0


def test_load_and_save_atlas_state_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "atlas_state.json"
    original = AtlasState(
        nodes=[
            AtlasNode(
                node_id="node_1",
                centroid_key="math.linear_equation",
                competence=0.45,
                uncertainty=0.10,
                learning_progress=0.08,
                forgetting_risk=0.02,
                density=1.7,
                sample_count=9,
            )
        ]
    )

    save_atlas_state(path, original)
    restored = load_atlas_state(path)

    assert restored == original
