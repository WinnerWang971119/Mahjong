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


def test_elo_tracker_update_magnitude():
    """ELO update should match textbook formula for equal-rated players."""
    tracker = EloTracker(initial_elo=1000.0, k=32.0)
    tracker.update(winner="a", losers=["b"])
    # Equal ELO: expected score = 0.5, gain = K * (1 - 0.5) = 16.0
    assert abs(tracker.get_elo("a") - 1016.0) < 0.01
    assert abs(tracker.get_elo("b") - 984.0) < 0.01


def test_elo_tracker_multi_loser_no_compounding():
    """Winner ELO should not compound when beating multiple equal-rated losers."""
    tracker = EloTracker(initial_elo=1000.0, k=32.0)
    tracker.update(winner="a", losers=["b", "c", "d"])
    # Each matchup: expected = 0.5, delta = 16.0. Three losers = 48.0 total.
    assert abs(tracker.get_elo("a") - 1048.0) < 0.01
    for loser in ["b", "c", "d"]:
        assert abs(tracker.get_elo(loser) - 984.0) < 0.01


def test_league_manager_pool_pruning(tmp_path):
    """Pool should never exceed pool_max_size after pruning."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path, pool_max_size=5)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    mgr = LeagueManager(cfg)
    for ep in range(0, 5000, 500):
        mgr.add_checkpoint(episode=ep, network=net, elo=1000.0 + ep * 0.01)
    assert mgr.pool_size == 5


def test_load_opponent_network(tmp_path):
    """Loading opponent weights should produce matching parameters."""
    cfg = TrainingConfig(checkpoint_dir=tmp_path)
    net = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    mgr = LeagueManager(cfg)
    mgr.add_checkpoint(episode=100, network=net, elo=1050.0)

    net2 = MahjongNetwork(obs_size=290, action_size=128, cfg=cfg)
    mgr.load_opponent_network(100, net2)
    for p1, p2 in zip(net.parameters(), net2.parameters()):
        assert torch.allclose(p1, p2)
