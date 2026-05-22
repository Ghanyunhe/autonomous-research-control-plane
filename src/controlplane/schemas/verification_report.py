from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


ReworkPriority = Literal["none", "low", "medium", "high"]
FailedCheckType = Literal["artifact_presence", "worker_execution", "scientific_validity"]


class VerificationReport(BaseModel):
    task_id: str
    status: Literal["accept", "reject", "rework"]
    failures: list[str]
    failed_check_types: list[FailedCheckType]
    rework_priority: ReworkPriority
    warnings: list[str]
    recommended_brain_action: Literal["CONTINUE", "REFINE", "PIVOT", "ESCALATE", "STOP"]
