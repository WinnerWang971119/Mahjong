"""Tests for reward computation."""
from training.rewards import compute_rewards


def test_winner_gets_positive_reward():
    """Winner receives positive reward proportional to score."""
    rewards = compute_rewards(
        winner_idx=0,
        total_tai=5,
        num_players=4,
    )
    assert rewards[0] > 0
    assert all(rewards[i] < 0 for i in range(1, 4))


def test_draw_gives_small_negative():
    rewards = compute_rewards(
        winner_idx=None,
        total_tai=0,
        num_players=4,
    )
    for r in rewards:
        assert r < 0
        assert r > -1.0  # Small penalty


def test_higher_tai_bigger_reward():
    r_low = compute_rewards(winner_idx=0, total_tai=2, num_players=4)
    r_high = compute_rewards(winner_idx=0, total_tai=10, num_players=4)
    assert r_high[0] > r_low[0]


def test_rewards_sum_to_roughly_zero():
    """Zero-sum game: total rewards across players ~ 0 (except draw penalty)."""
    rewards = compute_rewards(winner_idx=0, total_tai=5, num_players=4)
    assert abs(sum(rewards)) < 0.01
