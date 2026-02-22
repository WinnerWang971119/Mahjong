"""Tests for training configuration."""
from training.config import TrainingConfig


def test_default_config_creation():
    cfg = TrainingConfig()
    assert cfg.learning_rate == 3e-4
    assert cfg.n_envs == 8
    assert cfg.hidden_sizes == [512, 512, 256]


def test_config_override():
    cfg = TrainingConfig(learning_rate=1e-3, n_envs=4)
    assert cfg.learning_rate == 1e-3
    assert cfg.n_envs == 4
