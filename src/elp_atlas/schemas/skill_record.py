from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SkillDomain = Literal["math", "tool_use", "open_ended", "unknown"]


class SkillRecord(BaseModel):
    domain: SkillDomain
    skill_tags: list[str] = Field(default_factory=list)
    reasoning_ops: list[str] = Field(default_factory=list)
    failure_modes_targeted: list[str] = Field(default_factory=list)
    dependency_tags: list[str] = Field(default_factory=list)
    difficulty_estimate: float | None = None
    notes: str = ""
