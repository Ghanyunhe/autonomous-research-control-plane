from __future__ import annotations

from pydantic import BaseModel, Field


class AtlasNode(BaseModel):
    node_id: str
    centroid_key: str
    competence: float = 0.0
    uncertainty: float = 0.0
    learning_progress: float = 0.0
    forgetting_risk: float = 0.0
    density: float = 0.0
    sample_count: int = 0
    transfer_targets: list[str] = Field(default_factory=list)
    notes: str = ""
