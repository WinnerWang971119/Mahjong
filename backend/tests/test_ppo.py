"""Tests for PPO rollout buffer and update."""
import torch
import numpy as np

from training.ppo import RolloutBuffer, ppo_update
from training.network import MahjongNetwork
from training.config import TrainingConfig


def test_rollout_buffer_add_and_get():
    buf = RolloutBuffer(capacity=16, obs_size=290, action_size=128)
    for _ in range(16):
        buf.add(
            obs=np.random.randn(290).astype(np.float32),
            action=5,
            reward=0.1,
            done=False,
            log_prob=-1.5,
            value=0.3,
            action_mask=np.ones(128, dtype=np.float32),
        )
    assert buf.size == 16
    batch = buf.get_all()
    assert batch["obs"].shape == (16, 290)
    assert batch["actions"].shape == (16,)


def test_rollout_buffer_compute_gae():
    cfg = TrainingConfig()
    buf = RolloutBuffer(capacity=8, obs_size=290, action_size=128)
    for i in range(8):
        buf.add(
            obs=np.random.randn(290).astype(np.float32),
            action=0,
            reward=1.0 if i == 7 else 0.0,
            done=(i == 7),
            log_prob=-1.0,
            value=0.5,
            action_mask=np.ones(128, dtype=np.float32),
        )
    buf.compute_gae(last_value=0.0, gamma=cfg.gamma, gae_lambda=cfg.gae_lambda)
    batch = buf.get_all()
    assert "advantages" in batch
    assert "returns" in batch
    assert batch["advantages"].shape == (8,)


def test_ppo_update_runs():
    """PPO update should complete without error and return loss dict."""
    cfg = TrainingConfig(n_epochs=1, batch_size=4)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters(), lr=cfg.learning_rate)

    buf = RolloutBuffer(capacity=8, obs_size=290, action_size=128)
    for i in range(8):
        buf.add(
            obs=np.random.randn(290).astype(np.float32),
            action=np.random.randint(0, 128),
            reward=0.1,
            done=(i == 7),
            log_prob=-2.0,
            value=0.5,
            action_mask=np.ones(128, dtype=np.float32),
        )
    buf.compute_gae(last_value=0.0, gamma=cfg.gamma, gae_lambda=cfg.gae_lambda)

    losses = ppo_update(net, optimizer, buf, cfg, device="cpu")
    assert "policy_loss" in losses
    assert "value_loss" in losses
    assert "entropy" in losses
    assert "clip_fraction" in losses
