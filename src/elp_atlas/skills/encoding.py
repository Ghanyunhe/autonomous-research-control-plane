from __future__ import annotations

from elp_atlas.schemas import CandidateTask, SkillRecord


def abstract_skill_record_from_candidate(candidate: CandidateTask) -> SkillRecord:
    """Return the normalized skill record attached to a candidate task."""
    return candidate.skill_record.model_copy(deep=True)


def encode_skill_record(skill_record: SkillRecord) -> str:
    """Return a deterministic key for atlas assignment and fixture-level clustering."""
    skill_segment = ",".join(sorted(skill_record.skill_tags)) or "no_skill_tags"
    op_segment = ",".join(sorted(skill_record.reasoning_ops)) or "no_reasoning_ops"
    return f"{skill_record.domain}:{skill_segment}:{op_segment}"


def summarize_skill_record(skill_record: SkillRecord) -> str:
    """Return a compact human-readable summary of a skill record."""
    first_skill = skill_record.skill_tags[0] if skill_record.skill_tags else "none"
    first_op = skill_record.reasoning_ops[0] if skill_record.reasoning_ops else "none"
    return f"domain={skill_record.domain}; skills={first_skill}; op={first_op}"
