from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from elp_atlas.schemas import CandidateTask


class ReplayMemoryEntry(BaseModel):
    task_id: str
    domain: str
    skill_key: str
    reference_answer: str


def build_replay_memory(candidates: list[CandidateTask]) -> list[ReplayMemoryEntry]:
    entries: list[ReplayMemoryEntry] = []
    for candidate in candidates:
        skill_key = ".".join(candidate.skill_record.skill_tags) if candidate.skill_record.skill_tags else "unknown"
        entries.append(
            ReplayMemoryEntry(
                task_id=candidate.task_id,
                domain=candidate.domain,
                skill_key=skill_key,
                reference_answer=candidate.reference_answer,
            )
        )
    return entries


def save_replay_memory(path: Path, entries: list[ReplayMemoryEntry]) -> None:
    path.write_text(
        "[\n"
        + ",\n".join(entry.model_dump_json(indent=2) for entry in entries)
        + "\n]\n"
    )
