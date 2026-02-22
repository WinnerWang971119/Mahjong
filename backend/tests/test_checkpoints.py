"""Tests for checkpoint save/load/retention."""
from __future__ import annotations

import json

import torch

from training.checkpoints import CheckpointManager
from training.network import MahjongNetwork
from training.config import TrainingConfig


def test_save_and_load(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=500, elo=1050.0)

    net2 = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer2 = torch.optim.Adam(net2.parameters())
    info = mgr.load_latest(net2, optimizer2)
    assert info["episode"] == 500
    assert info["elo"] == 1050.0

    # Weights should match
    for p1, p2 in zip(net.parameters(), net2.parameters()):
        assert torch.allclose(p1, p2)


def test_best_elo_tracking(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=100, elo=1000.0)
    mgr.save(net, optimizer, episode=200, elo=1100.0)
    mgr.save(net, optimizer, episode=300, elo=1050.0)

    assert mgr.best_elo == 1100.0
    assert (tmp_path / "best_elo.pt").exists()


def test_retention_policy(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path, pool_max_size=3)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    for ep in range(0, 3000, 500):
        mgr.save(net, optimizer, episode=ep, elo=1000.0 + ep * 0.1)

    # Should keep: latest, best_elo, last pool_max_size periodic
    periodic = list(tmp_path.glob("ep_*.pt"))
    assert len(periodic) <= cfg.pool_max_size


def test_metadata_json(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=500, elo=1050.0)

    meta_path = tmp_path / "metadata.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert "elo_history" in meta
    assert len(meta["elo_history"]) == 1


def test_load_latest_without_optimizer(tmp_path):
    """load_latest should work even when optimizer is None."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=100, elo=1000.0)

    net2 = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    info = mgr.load_latest(net2, optimizer=None)
    assert info["episode"] == 100
    assert info["elo"] == 1000.0


def test_load_best(tmp_path):
    """load_best should load the checkpoint with highest ELO."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=100, elo=1000.0)
    mgr.save(net, optimizer, episode=200, elo=1200.0)
    mgr.save(net, optimizer, episode=300, elo=1100.0)

    net2 = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    info = mgr.load_best(net2)
    assert info["episode"] == 200
    assert info["elo"] == 1200.0


def test_resume_from_existing_metadata(tmp_path):
    """Creating a new CheckpointManager should restore state from metadata.json."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=100, elo=1050.0)
    mgr.save(net, optimizer, episode=200, elo=1100.0)

    # Simulate a restart by creating a new manager
    mgr2 = CheckpointManager(cfg)
    assert mgr2.best_elo == 1100.0
    assert len(mgr2._elo_history) == 2


def test_list_checkpoints(tmp_path):
    """list_checkpoints should return periodic checkpoints sorted by name."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    optimizer = torch.optim.Adam(net.parameters())
    mgr = CheckpointManager(cfg)

    mgr.save(net, optimizer, episode=100, elo=1000.0)
    mgr.save(net, optimizer, episode=200, elo=1010.0)

    cps = mgr.list_checkpoints()
    assert len(cps) == 2
    assert cps[0].name == "ep_000100.pt"
    assert cps[1].name == "ep_000200.pt"
