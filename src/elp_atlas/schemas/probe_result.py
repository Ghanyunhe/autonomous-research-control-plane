from __future__ import annotations

from pydantic import BaseModel, Field


class ProbeResult(BaseModel):
    probe_id: str
    skill_node_id: str
    before_score: float
    after_score: float
    learning_progress_estimate: float
    regression_estimate: float
    eval_set_sizes: dict[str, int] = Field(default_factory=dict)
    notes: str = ""
