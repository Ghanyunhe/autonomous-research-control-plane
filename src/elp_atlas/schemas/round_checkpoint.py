from __future__ import annotations

from pydantic import BaseModel, Field


class RoundCheckpoint(BaseModel):
    round_id: int
    phase_label: str
    config_snapshot: dict[str, object] = Field(default_factory=dict)
    artifact_paths: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    summary: str = ""
