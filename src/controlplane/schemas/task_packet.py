from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


TaskType = Literal["retrieval", "code_only", "code_and_run", "analysis", "repair"]


class TaskPacket(BaseModel):
    task_id: str
    experiment_id: str
    task_type: TaskType
    goal: str
    worker_requirements: dict
    deliverables: list[str]
    acceptance_criteria: list[str]
    retry_policy: dict
