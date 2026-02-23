"""MLP network with policy + value heads and action masking."""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.distributions import Categorical

from training.config import TrainingConfig


def _layer_init(layer: nn.Linear, std: float = 0.01) -> nn.Linear:
    """Orthogonal initialization (CleanRL convention)."""
    nn.init.orthogonal_(layer.weight, std)
    nn.init.constant_(layer.bias, 0.0)
    return layer


class MahjongNetwork(nn.Module):
    """Shared backbone with separate policy and value heads."""

    def __init__(self, obs_size: int, action_size: int, cfg: TrainingConfig) -> None:
        super().__init__()
        self.action_size = action_size

        # Shared backbone
        layers: list[nn.Module] = []
        in_size = obs_size
        for h in cfg.hidden_sizes:
            layers.append(_layer_init(nn.Linear(in_size, h), std=1.0))
            layers.append(nn.ReLU())
            in_size = h
        self.backbone = nn.Sequential(*layers)

        # Policy head
        self.policy_head = nn.Sequential(
            _layer_init(nn.Linear(in_size, cfg.head_hidden_size), std=1.0),
            nn.ReLU(),
            _layer_init(nn.Linear(cfg.head_hidden_size, action_size), std=0.01),
        )

        # Value head
        self.value_head = nn.Sequential(
            _layer_init(nn.Linear(in_size, cfg.head_hidden_size), std=1.0),
            nn.ReLU(),
            _layer_init(nn.Linear(cfg.head_hidden_size, 1), std=1.0),
        )

    def forward(
        self, obs: torch.Tensor, action_mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning masked logits and value estimate.

        Args:
            obs: Observation tensor of shape (batch, obs_size).
            action_mask: Binary mask of shape (batch, action_size).
                         1 = legal action, 0 = illegal action.

        Returns:
            logits: Policy logits with illegal actions set to -inf.
            value: Value estimate of shape (batch, 1).
        """
        features = self.backbone(obs)
        logits = self.policy_head(features)
        value = self.value_head(features)
        logits = logits.masked_fill(action_mask == 0, float("-inf"))
        return logits, value

    def get_action_and_value(
        self, obs: torch.Tensor, action_mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample an action and return log_prob, entropy, and value.

        Used during rollout collection (inference).

        Args:
            obs: Observation tensor of shape (batch, obs_size).
            action_mask: Binary mask of shape (batch, action_size).

        Returns:
            action: Sampled action indices of shape (batch,).
            log_prob: Log probability of sampled actions, shape (batch,).
            entropy: Distribution entropy, shape (batch,).
            value: Value estimate of shape (batch, 1).
        """
        logits, value = self(obs, action_mask)
        dist = Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return action, log_prob, entropy, value

    def evaluate_actions(
        self,
        obs: torch.Tensor,
        action_mask: torch.Tensor,
        actions: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Evaluate given actions under current policy.

        Used during PPO update to compute new log_probs for the ratio.

        Args:
            obs: Observation tensor of shape (batch, obs_size).
            action_mask: Binary mask of shape (batch, action_size).
            actions: Previously taken actions of shape (batch,).

        Returns:
            log_prob: Log probability of the given actions, shape (batch,).
            entropy: Distribution entropy, shape (batch,).
            value: Value estimate of shape (batch, 1).
        """
        logits, value = self(obs, action_mask)
        dist = Categorical(logits=logits)
        log_prob = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_prob, entropy, value
