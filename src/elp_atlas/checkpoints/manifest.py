from __future__ import annotations

from pathlib import Path

from elp_atlas.schemas import RoundCheckpoint


def build_checkpoint_manifest(checkpoints: list[RoundCheckpoint]) -> list[RoundCheckpoint]:
    return checkpoints


def save_checkpoint_manifest(path: Path, manifest: list[RoundCheckpoint]) -> None:
    path.write_text(
        "[\n"
        + ",\n".join(checkpoint.model_dump_json(indent=2) for checkpoint in manifest)
        + "\n]\n"
    )
