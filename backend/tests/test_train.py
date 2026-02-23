"""Integration test for training loop."""
from __future__ import annotations

import pytest
from training.train import run_training
from training.config import TrainingConfig


@pytest.mark.slow
def test_warmup_runs_briefly(tmp_path):
    """Run a few warmup episodes to verify the full pipeline works."""
    cfg = TrainingConfig(
        warmup_episodes=4,
        total_episodes=4,
        eval_interval=2,
        eval_games=2,
        checkpoint_interval=2,
        n_steps=64,
        n_epochs=1,
        batch_size=16,
        n_envs=1,
        checkpoint_dir=tmp_path / "ckpt",
        log_dir=tmp_path / "logs",
        device="cpu",
    )
    run_training(cfg)
    assert (tmp_path / "ckpt" / "latest.pt").exists()
    log_files = list((tmp_path / "logs").rglob("events.out.*"))
    assert len(log_files) > 0
