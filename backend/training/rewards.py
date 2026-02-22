"""Score-based reward computation for RL training."""
from __future__ import annotations

# Max tai cap from scorer.py
MAX_TAI = 81


def compute_rewards(
    *,
    winner_idx: int | None,
    total_tai: int,
    num_players: int = 4,
) -> list[float]:
    """Compute per-player rewards after a hand ends.

    Winner gets +normalized_score, losers split the negative equally.
    Draw gives small negative to all players.

    Returns:
        List of floats, one per player seat.
    """
    if winner_idx is None:
        # Draw: small penalty for everyone (incentivize winning)
        return [-0.1] * num_players

    # Normalize tai to [0, 1] range using MAX_TAI cap
    normalized = total_tai / MAX_TAI
    winner_reward = normalized

    # Zero-sum: losers split the negative
    loser_reward = -winner_reward / (num_players - 1)

    rewards = [loser_reward] * num_players
    rewards[winner_idx] = winner_reward
    return rewards
