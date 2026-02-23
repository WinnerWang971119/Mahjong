"""TensorBoard metrics logging for training pipeline."""
from __future__ import annotations

from pathlib import Path

from torch.utils.tensorboard import SummaryWriter


class MetricsLogger:
    """Wraps TensorBoard SummaryWriter with typed logging methods."""

    def __init__(self, log_dir: Path | str) -> None:
        self._writer = SummaryWriter(log_dir=str(log_dir))

    def log_training(self, step: int, policy_loss: float, value_loss: float,
                     entropy: float, clip_fraction: float, learning_rate: float) -> None:
        self._writer.add_scalar("train/policy_loss", policy_loss, step)
        self._writer.add_scalar("train/value_loss", value_loss, step)
        self._writer.add_scalar("train/entropy", entropy, step)
        self._writer.add_scalar("train/clip_fraction", clip_fraction, step)
        self._writer.add_scalar("train/learning_rate", learning_rate, step)

    def log_evaluation(self, step: int, win_rate: float, avg_reward: float,
                       avg_hand_value: float, draw_rate: float) -> None:
        self._writer.add_scalar("eval/win_rate_vs_rule_based", win_rate, step)
        self._writer.add_scalar("eval/avg_episode_reward", avg_reward, step)
        self._writer.add_scalar("eval/avg_hand_value_on_win", avg_hand_value, step)
        self._writer.add_scalar("eval/draw_rate", draw_rate, step)

    def log_league(self, step: int, current_elo: float, best_elo: float, pool_size: int) -> None:
        self._writer.add_scalar("league/current_elo", current_elo, step)
        self._writer.add_scalar("league/best_elo", best_elo, step)
        self._writer.add_scalar("league/pool_size", pool_size, step)

    def log_episode(self, step: int, episode_length: int, tiles_remaining: int) -> None:
        self._writer.add_scalar("env/episode_length", episode_length, step)
        self._writer.add_scalar("env/tiles_remaining", tiles_remaining, step)

    def close(self) -> None:
        self._writer.close()
