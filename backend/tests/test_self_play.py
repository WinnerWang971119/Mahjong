"""Tests for self-play league manager."""
import torch

from training.self_play import LeagueManager, EloTracker
from training.network import MahjongNetwork
from training.config import TrainingConfig


def test_elo_tracker_initial():
    tracker = EloTracker(initial_elo=1000.0, k=32.0)
    assert tracker.get_elo("agent_a") == 1000.0


def test_elo_tracker_update():
    tracker = EloTracker(initial_elo=1000.0, k=32.0)
    tracker.update(winner="agent_a", losers=["agent_b", "agent_c", "agent_d"])
    assert tracker.get_elo("agent_a") > 1000.0
    assert tracker.get_elo("agent_b") < 1000.0


def test_league_manager_warmup_opponents(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    mgr = LeagueManager(cfg)
    opponents = mgr.sample_opponents(phase="warmup")
    assert len(opponents) == 3
    assert all(o == "rule_based" for o in opponents)


def test_league_manager_add_checkpoint(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    mgr = LeagueManager(cfg)
    mgr.add_checkpoint(episode=500, network=net, elo=1050.0)
    assert mgr.pool_size >= 1


def test_league_manager_selfplay_opponents(tmp_path):
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    mgr = LeagueManager(cfg)
    for ep in range(500, 3000, 500):
        mgr.add_checkpoint(episode=ep, network=net, elo=1000.0 + ep * 0.01)
    opponents = mgr.sample_opponents(phase="selfplay")
    assert len(opponents) == 3
    for o in opponents:
        assert isinstance(o, (str, int))
