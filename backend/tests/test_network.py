"""Tests for neural network architecture."""
import torch
import numpy as np

from training.network import MahjongNetwork
from training.config import TrainingConfig


def test_network_creation():
    cfg = TrainingConfig()
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    total_params = sum(p.numel() for p in net.parameters())
    assert total_params > 0
    assert total_params < 2_000_000  # Should be ~650K


def test_network_forward_shape():
    cfg = TrainingConfig()
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    obs = torch.randn(4, 290)  # batch of 4
    mask = torch.ones(4, 128)  # all legal
    logits, value = net(obs, mask)
    assert logits.shape == (4, 128)
    assert value.shape == (4, 1)


def test_network_masking():
    """Masked actions should have -inf logits."""
    cfg = TrainingConfig()
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    obs = torch.randn(1, 290)
    mask = torch.zeros(1, 128)
    mask[0, 0] = 1.0  # Only action 0 is legal
    mask[0, 5] = 1.0  # And action 5
    logits, _ = net(obs, mask)
    # Masked actions should be -inf
    assert logits[0, 1].item() == float("-inf")
    assert logits[0, 0].item() != float("-inf")
    assert logits[0, 5].item() != float("-inf")


def test_network_get_action_and_value():
    cfg = TrainingConfig()
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    obs = torch.randn(1, 290)
    mask = torch.ones(1, 128)
    action, log_prob, entropy, value = net.get_action_and_value(obs, mask)
    assert action.shape == (1,)
    assert log_prob.shape == (1,)
    assert entropy.shape == (1,)
    assert value.shape == (1, 1)
    assert 0 <= action.item() < 128


def test_network_evaluate_actions():
    cfg = TrainingConfig()
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    obs = torch.randn(8, 290)
    mask = torch.ones(8, 128)
    actions = torch.randint(0, 128, (8,))
    log_prob, entropy, value = net.evaluate_actions(obs, mask, actions)
    assert log_prob.shape == (8,)
    assert entropy.shape == (8,)
    assert value.shape == (8, 1)
