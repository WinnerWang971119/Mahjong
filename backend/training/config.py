"""Training configuration as a single dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrainingConfig:
    """All hyperparameters and paths for the RL training pipeline."""

    # PPO hyperparameters
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    n_steps: int = 2048
    n_epochs: int = 4
    batch_size: int = 256
    n_envs: int = 8

    # Training phases
    warmup_episodes: int = 10_000
    warmup_win_rate_threshold: float = 0.5
    total_episodes: int = 200_000
    eval_interval: int = 100
    eval_games: int = 100
    checkpoint_interval: int = 500

    # League
    pool_max_size: int = 20
    pool_sample_recent: float = 0.7
    pool_sample_old: float = 0.2
    pool_sample_rule_based: float = 0.1

    # Network
    hidden_sizes: list[int] = field(default_factory=lambda: [512, 512, 256])
    head_hidden_size: int = 256

    # Paths
    checkpoint_dir: Path = Path("checkpoints")
    log_dir: Path = Path("runs")

    # Device
    device: str = "cuda"

    # ELO
    elo_initial: float = 1000.0
    elo_k: float = 32.0
