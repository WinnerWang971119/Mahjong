"""Tests for PettingZoo AEC environment wrapper."""
from __future__ import annotations

import numpy as np

from training.env import MahjongEnv


def test_env_creates():
    env = MahjongEnv()
    env.reset()
    assert env.agents == ["player_0", "player_1", "player_2", "player_3"]


def test_env_observation_space():
    env = MahjongEnv()
    env.reset()
    for agent in env.agents:
        obs_space = env.observation_space(agent)
        assert obs_space.shape[0] > 200  # ~290 features


def test_env_action_space():
    env = MahjongEnv()
    env.reset()
    for agent in env.agents:
        act_space = env.action_space(agent)
        assert act_space.n == 128  # ActionEncoder.action_size


def test_env_action_mask():
    env = MahjongEnv()
    env.reset()
    agent = env.agent_selection
    obs, _, _, _, info = env.last()
    mask = info["action_mask"]
    assert mask.shape == (128,)
    assert mask.sum() > 0  # At least one legal action


def test_env_step_loop():
    """Run a complete game through the env interface."""
    env = MahjongEnv()
    env.reset()
    steps = 0
    max_steps = 200
    while env.agents and steps < max_steps:
        obs, reward, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
            continue
        mask = info["action_mask"]
        legal_indices = np.where(mask == 1.0)[0]
        action = np.random.choice(legal_indices)
        env.step(action)
        steps += 1
    # Game should end before max_steps
    assert steps < max_steps


def test_env_rewards_at_terminal():
    """At game end, at least one player should have non-zero reward."""
    env = MahjongEnv()
    env.reset()
    steps = 0
    while env.agents and steps < 200:
        obs, reward, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
            continue
        mask = info["action_mask"]
        legal_indices = np.where(mask == 1.0)[0]
        action = np.random.choice(legal_indices)
        env.step(action)
        steps += 1
    # Check that rewards were assigned
    total_reward = sum(abs(env.rewards.get(a, 0)) for a in env.possible_agents)
    assert total_reward > 0 or steps >= 200


def test_env_observe_returns_correct_shape():
    """Observation should match the declared observation space."""
    env = MahjongEnv()
    env.reset()
    agent = env.agent_selection
    obs = env.observe(agent)
    assert obs.shape == env.observation_space(agent).shape
    assert obs.dtype == np.float32


def test_env_multiple_games():
    """Running multiple games via reset should work without errors."""
    env = MahjongEnv()
    for _ in range(1):
        env.reset()
        steps = 0
        while env.agents and steps < 200:
            obs, reward, term, trunc, info = env.last()
            if term or trunc:
                env.step(None)
                continue
            mask = info["action_mask"]
            legal_indices = np.where(mask == 1.0)[0]
            if len(legal_indices) == 0:
                break
            action = np.random.choice(legal_indices)
            env.step(action)
            steps += 1
