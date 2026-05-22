from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class RegressionReport(BaseModel):
    checkpoint_id: str
    total_regression: float
    regressed_skills: list[str]
    notes: str


def build_regression_report(
    *,
    checkpoint_id: str,
    old_skill_scores: dict[str, float],
    new_skill_scores: dict[str, float],
) -> RegressionReport:
    regressed_skills: list[str] = []
    total_regression = 0.0
    for skill, old_score in old_skill_scores.items():
        new_score = new_skill_scores.get(skill, old_score)
        if new_score < old_score:
            regressed_skills.append(skill)
            total_regression += round(old_score - new_score, 4)
    return RegressionReport(
        checkpoint_id=checkpoint_id,
        total_regression=round(total_regression, 4),
        regressed_skills=sorted(regressed_skills),
        notes="Synthetic anti-regression report.",
    )


def save_regression_report(path: Path, report: RegressionReport) -> None:
    path.write_text(report.model_dump_json(indent=2))
