from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from controlplane.schemas.task_packet import TaskType


WorkerPreference = Literal["any", "claude_code", "codex"]
AcceptanceEmphasis = Literal["balanced", "artifact_presence", "scientific_validity"]


class TaskIntent(BaseModel):
    task_type: TaskType
    worker_preference: WorkerPreference
    acceptance_emphasis: AcceptanceEmphasis
    goal_hint: str
    focus_areas: list[str]
