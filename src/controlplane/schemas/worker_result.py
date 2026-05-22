from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class WorkerResult(BaseModel):
    task_id: str
    worker_id: str
    status: Literal["success", "partial", "failed", "blocked"]
    deliverable_paths: list[str]
    summary: str
