from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from elp_atlas.rewards import CheapELPScore


class ChallengerUpdateResult(BaseModel):
    round_id: int
    phase_label: str
    samples_consumed: int
    reward_mean: float
    reward_max: float
    summary: str


def run_challenger_update(
    *,
    round_id: int,
    phase_label: str,
    rewards: list[CheapELPScore],
) -> ChallengerUpdateResult:
    reward_values = [reward.cheap_score for reward in rewards]
    samples_consumed = len(reward_values)
    reward_mean = 0.0 if not reward_values else round(sum(reward_values) / samples_consumed, 4)
    reward_max = 0.0 if not reward_values else round(max(reward_values), 4)
    return ChallengerUpdateResult(
        round_id=round_id,
        phase_label=phase_label,
        samples_consumed=samples_consumed,
        reward_mean=reward_mean,
        reward_max=reward_max,
        summary=f"Updated challenger from {samples_consumed} scored samples.",
    )


def save_challenger_update(path: Path, result: ChallengerUpdateResult) -> None:
    path.write_text(result.model_dump_json(indent=2))
