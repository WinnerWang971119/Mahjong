"""CleanRL-style PPO with action masking for multi-agent mahjong."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from training.config import TrainingConfig
from training.network import MahjongNetwork


class RolloutBuffer:
    """Fixed-size buffer for collecting rollout transitions."""

    def __init__(self, capacity: int, obs_size: int, action_size: int) -> None:
        self.capacity = capacity
        self.obs = np.zeros((capacity, obs_size), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)
        self.log_probs = np.zeros(capacity, dtype=np.float32)
        self.values = np.zeros(capacity, dtype=np.float32)
        self.action_masks = np.zeros((capacity, action_size), dtype=np.float32)
        self.advantages = np.zeros(capacity, dtype=np.float32)
        self.returns = np.zeros(capacity, dtype=np.float32)
        self.size = 0

    def add(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        done: bool,
        log_prob: float,
        value: float,
        action_mask: np.ndarray,
    ) -> None:
        """Store a single transition at the current position."""
        idx = self.size
        self.obs[idx] = obs
        self.actions[idx] = action
        self.rewards[idx] = reward
        self.dones[idx] = float(done)
        self.log_probs[idx] = log_prob
        self.values[idx] = value
        self.action_masks[idx] = action_mask
        self.size += 1

    def compute_gae(
        self,
        last_value: float,
        gamma: float,
        gae_lambda: float,
    ) -> None:
        """Compute Generalized Advantage Estimation."""
        last_adv = 0.0
        for t in reversed(range(self.size)):
            if t == self.size - 1:
                next_value = last_value
                next_non_terminal = 1.0 - self.dones[t]
            else:
                next_value = self.values[t + 1]
                next_non_terminal = 1.0 - self.dones[t]

            delta = (
                self.rewards[t]
                + gamma * next_value * next_non_terminal
                - self.values[t]
            )
            self.advantages[t] = last_adv = (
                delta + gamma * gae_lambda * next_non_terminal * last_adv
            )
        self.returns[: self.size] = (
            self.advantages[: self.size] + self.values[: self.size]
        )

    def get_all(self) -> dict[str, np.ndarray]:
        """Return dict of all stored arrays, sliced to current size."""
        s = self.size
        return {
            "obs": self.obs[:s],
            "actions": self.actions[:s],
            "rewards": self.rewards[:s],
            "dones": self.dones[:s],
            "log_probs": self.log_probs[:s],
            "values": self.values[:s],
            "action_masks": self.action_masks[:s],
            "advantages": self.advantages[:s],
            "returns": self.returns[:s],
        }

    def reset(self) -> None:
        """Reset buffer position to allow re-use without re-allocation."""
        self.size = 0


def ppo_update(
    network: MahjongNetwork,
    optimizer: torch.optim.Optimizer,
    buffer: RolloutBuffer,
    cfg: TrainingConfig,
    device: str = "cpu",
) -> dict[str, float]:
    """Run PPO update epochs on buffer data. Returns loss metrics."""
    data = buffer.get_all()

    obs_t = torch.tensor(data["obs"], device=device)
    actions_t = torch.tensor(data["actions"], dtype=torch.long, device=device)
    old_log_probs_t = torch.tensor(data["log_probs"], device=device)
    advantages_t = torch.tensor(data["advantages"], device=device)
    returns_t = torch.tensor(data["returns"], device=device)
    masks_t = torch.tensor(data["action_masks"], device=device)

    # Normalize advantages
    if advantages_t.numel() > 1:
        advantages_t = (advantages_t - advantages_t.mean()) / (
            advantages_t.std() + 1e-8
        )

    total_policy_loss = 0.0
    total_value_loss = 0.0
    total_entropy = 0.0
    total_clip_frac = 0.0
    num_updates = 0

    n = obs_t.shape[0]

    for _epoch in range(cfg.n_epochs):
        indices = torch.randperm(n, device=device)
        for start in range(0, n, cfg.batch_size):
            end = min(start + cfg.batch_size, n)
            mb_idx = indices[start:end]

            mb_obs = obs_t[mb_idx]
            mb_actions = actions_t[mb_idx]
            mb_old_log_probs = old_log_probs_t[mb_idx]
            mb_advantages = advantages_t[mb_idx]
            mb_returns = returns_t[mb_idx]
            mb_masks = masks_t[mb_idx]

            new_log_probs, entropy, values = network.evaluate_actions(
                mb_obs, mb_masks, mb_actions
            )

            # Policy loss (clipped surrogate)
            ratio = torch.exp(new_log_probs - mb_old_log_probs)
            surr1 = ratio * mb_advantages
            surr2 = (
                torch.clamp(ratio, 1.0 - cfg.clip_epsilon, 1.0 + cfg.clip_epsilon)
                * mb_advantages
            )
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            value_loss = nn.functional.mse_loss(values.squeeze(-1), mb_returns)

            # Entropy bonus
            entropy_loss = entropy.mean()

            # Total loss
            loss = (
                policy_loss
                + cfg.value_coef * value_loss
                - cfg.entropy_coef * entropy_loss
            )

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(network.parameters(), cfg.max_grad_norm)
            optimizer.step()

            # Track metrics
            with torch.no_grad():
                clip_frac = ((ratio - 1.0).abs() > cfg.clip_epsilon).float().mean()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy_loss.item()
            total_clip_frac += clip_frac.item()
            num_updates += 1

    return {
        "policy_loss": total_policy_loss / max(num_updates, 1),
        "value_loss": total_value_loss / max(num_updates, 1),
        "entropy": total_entropy / max(num_updates, 1),
        "clip_fraction": total_clip_frac / max(num_updates, 1),
    }
