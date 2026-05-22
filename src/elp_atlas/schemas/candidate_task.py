from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from elp_atlas.schemas.skill_record import SkillRecord


VerifierType = Literal["exact_match", "symbolic", "unit_test", "tool_call", "custom"]


class CandidateVerifier(BaseModel):
    type: VerifierType
    spec: dict[str, Any] = Field(default_factory=dict)


class CandidateTask(BaseModel):
    task_id: str
    domain: str
    problem: str
    reference_answer: str
    verifier: CandidateVerifier
    skill_record: SkillRecord
    solution_outline: str = ""
    difficulty_rationale: str = ""
    anti_leakage_check: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
