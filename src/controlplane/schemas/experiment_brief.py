from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ExperimentBrief(BaseModel):
    experiment_id: str
    objective: str
    hypothesis_links: list[str]
    inputs: dict
    constraints: dict
    deliverables: list[str]
    acceptance_criteria: list[str]
    decomposition_hint: Literal["single_worker", "multi_worker_serial", "multi_worker_parallel"]
    preferred_worker_profile: str
