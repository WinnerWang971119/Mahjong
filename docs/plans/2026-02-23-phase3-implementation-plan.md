# Phase 3: RL Training Infrastructure — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a PPO self-play RL pipeline that trains a mahjong AI to beat the rule-based baseline in >80% of games.

**Architecture:** Monolithic `backend/training/` package wrapping the existing game engine via PettingZoo AEC. CleanRL-style PPO with action masking, self-play league, TensorBoard metrics, and Docker-based remote training.

**Tech Stack:** Python 3.11+, PyTorch 2.x, PettingZoo, TensorBoard, Docker

**Design doc:** `docs/plans/2026-02-23-phase3-rl-training-design.md`

---

## Task 0: Project Setup — Dependencies & Package Structure

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/training/__init__.py`
- Create: `backend/training/config.py`

**Step 1: Add `[train]` optional dependency group to pyproject.toml**

Add after the existing `[project.optional-dependencies]` entries:

```toml
train = [
    "torch>=2.2",
    "pettingzoo>=1.24",
    "tensorboard>=2.16",
    "gymnasium>=0.29",
    "numpy>=1.26",
    "pyyaml>=6.0",
]
```

**Step 2: Create package structure**

Create `backend/training/__init__.py` (empty file).

**Step 3: Write `config.py`**

```python
"""Training configuration as a single dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrainingConfig:
    """All hyperparameters and paths for the RL training pipeline."""

    # PPO hyperparameters
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    n_steps: int = 2048
    n_epochs: int = 4
    batch_size: int = 256
    n_envs: int = 8

    # Training phases
    warmup_episodes: int = 10_000
    warmup_win_rate_threshold: float = 0.5
    total_episodes: int = 200_000
    eval_interval: int = 100
    eval_games: int = 100
    checkpoint_interval: int = 500

    # League
    pool_max_size: int = 20
    pool_sample_recent: float = 0.7
    pool_sample_old: float = 0.2
    pool_sample_rule_based: float = 0.1

    # Network
    hidden_sizes: list[int] = field(default_factory=lambda: [512, 512, 256])
    head_hidden_size: int = 256

    # Paths
    checkpoint_dir: Path = Path("checkpoints")
    log_dir: Path = Path("runs")

    # Device
    device: str = "cuda"

    # ELO
    elo_initial: float = 1000.0
    elo_k: float = 32.0
```

**Step 4: Write test for config**

Create `backend/tests/test_config.py`:

```python
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
```

**Step 5: Run tests**

```bash
cd backend && uv pip install -e ".[train]" --system && uv run pytest tests/test_config.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/pyproject.toml backend/training/ backend/tests/test_config.py
git commit -m "feat: add training package skeleton and config dataclass"
```

---

## Task 1: Observation Encoder (`observation.py`)

**Files:**
- Create: `backend/training/observation.py`
- Create: `backend/tests/test_observation.py`

This module converts `GameState` into a flat numpy vector from one player's perspective.

**Step 1: Write failing tests**

Create `backend/tests/test_observation.py`:

```python
"""Tests for observation encoder."""
from __future__ import annotations

import numpy as np

from engine.game_session import GameSession
from training.observation import (
    ObservationEncoder,
    TILE_TYPES,
    tile_to_index,
)


def test_tile_to_index_covers_all_34():
    assert len(TILE_TYPES) == 34
    for i, tile in enumerate(TILE_TYPES):
        assert tile_to_index(tile) == i


def test_tile_to_index_number_tiles():
    assert tile_to_index("1m") == 0
    assert tile_to_index("9m") == 8
    assert tile_to_index("1p") == 9
    assert tile_to_index("9s") == 26


def test_tile_to_index_honor_tiles():
    assert tile_to_index("E") == 27
    assert tile_to_index("S") == 28
    assert tile_to_index("W") == 29
    assert tile_to_index("N") == 30
    assert tile_to_index("C") == 31
    assert tile_to_index("F") == 32
    assert tile_to_index("B") == 33


def test_encoder_obs_shape():
    enc = ObservationEncoder()
    session = GameSession()
    session.start_hand()
    obs = enc.encode(session.state, player_idx=0)
    assert isinstance(obs, np.ndarray)
    assert obs.dtype == np.float32
    assert obs.shape == (enc.obs_size,)
    assert np.all(obs >= 0.0)
    assert np.all(obs <= 1.0)


def test_encoder_different_perspectives():
    enc = ObservationEncoder()
    session = GameSession()
    session.start_hand()
    obs0 = enc.encode(session.state, player_idx=0)
    obs1 = enc.encode(session.state, player_idx=1)
    # Different players should have different hands → different obs
    assert not np.array_equal(obs0, obs1)


def test_encoder_hand_section_sums():
    """Hand tile counts should sum to roughly 16 (normalized)."""
    enc = ObservationEncoder()
    session = GameSession()
    session.start_hand()
    obs = enc.encode(session.state, player_idx=0)
    # First 34 features are hand counts / 4
    hand_section = obs[:34]
    hand_count = int(round(hand_section.sum() * 4))
    # Player should have ~16 tiles (may vary if dealer has 17)
    assert 13 <= hand_count <= 17
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_observation.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'training.observation'`

**Step 3: Implement `observation.py`**

```python
"""Encode GameState into flat observation vector from one player's perspective."""
from __future__ import annotations

import numpy as np

from engine.state import GameState, Meld


# Canonical tile ordering: 9m + 9p + 9s + 4 winds + 3 dragons = 34
TILE_TYPES: list[str] = (
    [f"{v}m" for v in range(1, 10)]
    + [f"{v}p" for v in range(1, 10)]
    + [f"{v}s" for v in range(1, 10)]
    + ["E", "S", "W", "N", "C", "F", "B"]
)

_TILE_TO_IDX: dict[str, int] = {t: i for i, t in enumerate(TILE_TYPES)}

FLOWER_TYPES: list[str] = [f"f{i}" for i in range(1, 9)]
_FLOWER_TO_IDX: dict[str, int] = {f: i for i, f in enumerate(FLOWER_TYPES)}

WIND_ORDER: list[str] = ["E", "S", "W", "N"]


def tile_to_index(tile: str) -> int:
    """Map tile string to index 0-33."""
    return _TILE_TO_IDX[tile]


def _count_tiles(tiles: list[str]) -> np.ndarray:
    """Count occurrences of each tile type, normalized to [0, 1] by /4."""
    counts = np.zeros(34, dtype=np.float32)
    for t in tiles:
        idx = _TILE_TO_IDX.get(t)
        if idx is not None:
            counts[idx] += 1.0
    return counts / 4.0


def _meld_tiles(melds: list[Meld]) -> list[str]:
    """Flatten melds into list of tiles."""
    tiles: list[str] = []
    for m in melds:
        tiles.extend(m.tiles)
    return tiles


class ObservationEncoder:
    """Encodes game state into flat float32 vector."""

    # Feature layout:
    #   [0:34]     own hand tile counts / 4
    #   [34:42]    own flowers (binary)
    #   [42:76]    opponent 1 discards / 4
    #   [76:110]   opponent 2 discards / 4
    #   [110:144]  opponent 3 discards / 4
    #   [144:178]  opponent 1 visible melds / 4
    #   [178:212]  opponent 2 visible melds / 4
    #   [212:246]  opponent 3 visible melds / 4
    #   [246:280]  own melds / 4
    #   [280:284]  seat wind one-hot
    #   [284:288]  prevailing wind one-hot
    #   [288]      tiles remaining in wall (normalized)
    #   [289]      tiles remaining in back wall (normalized)

    obs_size: int = 290

    def encode(self, gs: GameState, player_idx: int) -> np.ndarray:
        """Encode game state from player_idx's perspective."""
        obs = np.zeros(self.obs_size, dtype=np.float32)
        player = gs.players[player_idx]
        offset = 0

        # Own hand (34)
        obs[offset : offset + 34] = _count_tiles(player.hand)
        offset += 34

        # Own flowers (8)
        for f in player.flowers:
            fidx = _FLOWER_TO_IDX.get(f)
            if fidx is not None:
                obs[offset + fidx] = 1.0
        offset += 8

        # Opponents relative to player (3 × discards + 3 × melds)
        opp_indices = [(player_idx + i) % 4 for i in range(1, 4)]

        # Opponent discards (3 × 34)
        for opp_idx in opp_indices:
            opp = gs.players[opp_idx]
            obs[offset : offset + 34] = _count_tiles(opp.discards)
            offset += 34

        # Opponent visible melds (3 × 34)
        for opp_idx in opp_indices:
            opp = gs.players[opp_idx]
            obs[offset : offset + 34] = _count_tiles(_meld_tiles(opp.melds))
            offset += 34

        # Own melds (34)
        obs[offset : offset + 34] = _count_tiles(_meld_tiles(player.melds))
        offset += 34

        # Seat wind one-hot (4)
        seat_wind_idx = player.seat % 4
        obs[offset + seat_wind_idx] = 1.0
        offset += 4

        # Prevailing wind one-hot (4)
        round_wind_idx = WIND_ORDER.index(gs.round_wind)
        obs[offset + round_wind_idx] = 1.0
        offset += 4

        # Tiles remaining in wall (1) — normalized by initial wall size
        initial_wall = 144 - 8 - 16 * 4  # 144 total - 8 flowers - 64 dealt
        wall_count = len(gs.wall)
        obs[offset] = wall_count / max(initial_wall, 1)
        offset += 1

        # Tiles remaining in back wall (1)
        obs[offset] = len(gs.wall_back) / max(16, 1)
        offset += 1

        assert offset == self.obs_size
        return obs
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_observation.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/observation.py backend/tests/test_observation.py
git commit -m "feat: add observation encoder — flat binary encoding of game state"
```

---

## Task 2: Action Encoder (`observation.py` extension)

**Files:**
- Modify: `backend/training/observation.py`
- Modify: `backend/tests/test_observation.py`

Encode the discrete action space and provide action ↔ integer mapping + masking.

**Step 1: Write failing tests**

Append to `backend/tests/test_observation.py`:

```python
from engine.game_session import GameSession, Action
from training.observation import ActionEncoder


def test_action_encoder_space_size():
    enc = ActionEncoder()
    # 34 discard + chi combos + 1 pong + 4 kong + 1 win + 1 pass
    assert enc.action_size > 34


def test_action_to_int_discard():
    enc = ActionEncoder()
    action = Action(type="discard", tile="5m", combo=None, player_idx=0)
    idx = enc.action_to_int(action)
    assert 0 <= idx < enc.action_size
    roundtrip = enc.int_to_action(idx, player_idx=0)
    assert roundtrip.type == "discard"
    assert roundtrip.tile == "5m"


def test_action_to_int_pong():
    enc = ActionEncoder()
    action = Action(type="pong", tile="E", combo=None, player_idx=0)
    idx = enc.action_to_int(action)
    roundtrip = enc.int_to_action(idx, player_idx=0)
    assert roundtrip.type == "pong"


def test_action_to_int_win():
    enc = ActionEncoder()
    action = Action(type="win", tile="1m", combo=None, player_idx=0)
    idx = enc.action_to_int(action)
    roundtrip = enc.int_to_action(idx, player_idx=0)
    assert roundtrip.type == "win"


def test_action_to_int_pass():
    enc = ActionEncoder()
    action = Action(type="pass", tile=None, combo=None, player_idx=0)
    idx = enc.action_to_int(action)
    roundtrip = enc.int_to_action(idx, player_idx=0)
    assert roundtrip.type == "pass"


def test_action_mask_from_legal_actions():
    enc = ActionEncoder()
    session = GameSession()
    session.start_hand()
    # Dealer starts — should have legal actions
    legal = session.get_legal_actions(session.state.current_player)
    mask = enc.legal_actions_to_mask(legal)
    assert mask.shape == (enc.action_size,)
    assert mask.dtype == np.float32
    assert mask.sum() > 0  # At least one legal action
    # All 1s correspond to legal actions
    assert np.all((mask == 0.0) | (mask == 1.0))
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_observation.py::test_action_encoder_space_size -v
```

Expected: FAIL

**Step 3: Implement `ActionEncoder` in `observation.py`**

Add to `observation.py`:

```python
from engine.game_session import Action


# Action space layout:
#   [0:34]    discard tile_i
#   [34:97]   chi combos (max 63 = 7 starting values × 3 suits × 3 positions)
#   [97]      pong
#   [98]      open_kong
#   [99]      added_kong
#   [100]     concealed_kong  (tile encoded separately via tile field)
#   [101]     win
#   [102]     pass
#   [103]     draw
#
# For concealed_kong, we need per-tile variants → [100:134] = concealed_kong tile_i
# Revised layout:
#   [0:34]     discard tile_i
#   [34:97]    chi combo_j  (up to 63 combos, see _build_chi_combos)
#   [97]       pong
#   [98]       open_kong
#   [99:133]   added_kong tile_i  (which pong to extend)
#   [133:167]  concealed_kong tile_i (which tile to kong)
#   [167]      win
#   [168]      pass
#   [169]      draw

def _build_chi_combos() -> list[tuple[str, str, str]]:
    """Build all possible chi combos (sorted 3-tile sequences).

    For each suit, sequences start at value 1-7 → 7 × 3 suits = 21 sequences.
    For each sequence, the claimed tile can be any of the 3 positions → 63 combos.
    But in practice we enumerate unique sorted triples.
    """
    combos: list[tuple[str, str, str]] = []
    for suit in ("m", "p", "s"):
        for start in range(1, 8):
            combo = (f"{start}{suit}", f"{start+1}{suit}", f"{start+2}{suit}")
            combos.append(combo)
    return combos


_CHI_COMBOS: list[tuple[str, str, str]] = _build_chi_combos()
_CHI_COMBO_TO_IDX: dict[tuple[str, str, str], int] = {
    c: i for i, c in enumerate(_CHI_COMBOS)
}


class ActionEncoder:
    """Maps between Action objects and integer indices."""

    # Layout
    DISCARD_OFFSET = 0        # 34 actions
    CHI_OFFSET = 34           # 21 actions (one per unique sorted triple)
    PONG_OFFSET = 55          # 1 action
    OPEN_KONG_OFFSET = 56     # 1 action
    ADDED_KONG_OFFSET = 57    # 34 actions (which tile to extend)
    CONCEALED_KONG_OFFSET = 91  # 34 actions (which tile to kong)
    WIN_OFFSET = 125          # 1 action
    PASS_OFFSET = 126         # 1 action
    DRAW_OFFSET = 127         # 1 action

    action_size: int = 128

    def action_to_int(self, action: Action) -> int:
        """Convert Action to integer index."""
        if action.type == "discard":
            return self.DISCARD_OFFSET + tile_to_index(action.tile)
        elif action.type == "chi":
            combo = tuple(sorted(action.combo))
            return self.CHI_OFFSET + _CHI_COMBO_TO_IDX[combo]
        elif action.type == "pong":
            return self.PONG_OFFSET
        elif action.type == "open_kong":
            return self.OPEN_KONG_OFFSET
        elif action.type == "added_kong":
            return self.ADDED_KONG_OFFSET + tile_to_index(action.tile)
        elif action.type == "concealed_kong":
            return self.CONCEALED_KONG_OFFSET + tile_to_index(action.tile)
        elif action.type == "win":
            return self.WIN_OFFSET
        elif action.type == "pass":
            return self.PASS_OFFSET
        elif action.type == "draw":
            return self.DRAW_OFFSET
        else:
            raise ValueError(f"Unknown action type: {action.type}")

    def int_to_action(self, idx: int, player_idx: int) -> Action:
        """Convert integer index back to Action."""
        if self.DISCARD_OFFSET <= idx < self.DISCARD_OFFSET + 34:
            tile = TILE_TYPES[idx - self.DISCARD_OFFSET]
            return Action(type="discard", tile=tile, combo=None, player_idx=player_idx)
        elif self.CHI_OFFSET <= idx < self.CHI_OFFSET + len(_CHI_COMBOS):
            combo = list(_CHI_COMBOS[idx - self.CHI_OFFSET])
            return Action(type="chi", tile=None, combo=combo, player_idx=player_idx)
        elif idx == self.PONG_OFFSET:
            return Action(type="pong", tile=None, combo=None, player_idx=player_idx)
        elif idx == self.OPEN_KONG_OFFSET:
            return Action(type="open_kong", tile=None, combo=None, player_idx=player_idx)
        elif self.ADDED_KONG_OFFSET <= idx < self.ADDED_KONG_OFFSET + 34:
            tile = TILE_TYPES[idx - self.ADDED_KONG_OFFSET]
            return Action(type="added_kong", tile=tile, combo=None, player_idx=player_idx)
        elif self.CONCEALED_KONG_OFFSET <= idx < self.CONCEALED_KONG_OFFSET + 34:
            tile = TILE_TYPES[idx - self.CONCEALED_KONG_OFFSET]
            return Action(type="concealed_kong", tile=tile, combo=None, player_idx=player_idx)
        elif idx == self.WIN_OFFSET:
            return Action(type="win", tile=None, combo=None, player_idx=player_idx)
        elif idx == self.PASS_OFFSET:
            return Action(type="pass", tile=None, combo=None, player_idx=player_idx)
        elif idx == self.DRAW_OFFSET:
            return Action(type="draw", tile=None, combo=None, player_idx=player_idx)
        else:
            raise ValueError(f"Invalid action index: {idx}")

    def legal_actions_to_mask(self, legal_actions: list[Action]) -> np.ndarray:
        """Convert list of legal actions to binary mask."""
        mask = np.zeros(self.action_size, dtype=np.float32)
        for a in legal_actions:
            mask[self.action_to_int(a)] = 1.0
        return mask
```

**Step 4: Run all observation tests**

```bash
uv run pytest tests/test_observation.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/observation.py backend/tests/test_observation.py
git commit -m "feat: add action encoder with discrete action space and masking"
```

---

## Task 3: Reward Function (`rewards.py`)

**Files:**
- Create: `backend/training/rewards.py`
- Create: `backend/tests/test_rewards.py`

**Step 1: Write failing tests**

```python
"""Tests for reward computation."""
from training.rewards import compute_rewards


def test_winner_gets_positive_reward():
    """Winner receives positive reward proportional to score."""
    rewards = compute_rewards(
        winner_idx=0,
        total_tai=5,
        num_players=4,
    )
    assert rewards[0] > 0
    assert all(rewards[i] < 0 for i in range(1, 4))


def test_draw_gives_small_negative():
    rewards = compute_rewards(
        winner_idx=None,
        total_tai=0,
        num_players=4,
    )
    for r in rewards:
        assert r < 0
        assert r > -1.0  # Small penalty


def test_higher_tai_bigger_reward():
    r_low = compute_rewards(winner_idx=0, total_tai=2, num_players=4)
    r_high = compute_rewards(winner_idx=0, total_tai=10, num_players=4)
    assert r_high[0] > r_low[0]


def test_rewards_sum_to_roughly_zero():
    """Zero-sum game: total rewards across players ≈ 0 (except draw penalty)."""
    rewards = compute_rewards(winner_idx=0, total_tai=5, num_players=4)
    assert abs(sum(rewards)) < 0.01
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_rewards.py -v
```

**Step 3: Implement `rewards.py`**

```python
"""Score-based reward computation for RL training."""
from __future__ import annotations

# Max tai cap from scorer.py
MAX_TAI = 81


def compute_rewards(
    *,
    winner_idx: int | None,
    total_tai: int,
    num_players: int = 4,
) -> list[float]:
    """Compute per-player rewards after a hand ends.

    Winner gets +normalized_score, losers split the negative equally.
    Draw gives small negative to all players.

    Returns:
        List of 4 floats, one per player seat.
    """
    if winner_idx is None:
        # Draw: small penalty for everyone (incentivize winning)
        return [-0.1] * num_players

    # Normalize tai to [0, 1] range using MAX_TAI cap
    normalized = total_tai / MAX_TAI
    winner_reward = normalized

    # Zero-sum: losers split the negative
    loser_reward = -winner_reward / (num_players - 1)

    rewards = [loser_reward] * num_players
    rewards[winner_idx] = winner_reward
    return rewards
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_rewards.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/rewards.py backend/tests/test_rewards.py
git commit -m "feat: add sparse score-based reward function"
```

---

## Task 4: PettingZoo AEC Environment (`env.py`)

**Files:**
- Create: `backend/training/env.py`
- Create: `backend/tests/test_env.py`

**Step 1: Write failing tests**

```python
"""Tests for PettingZoo AEC environment wrapper."""
from __future__ import annotations

import numpy as np
from pettingzoo.test import api_test

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
    max_steps = 500
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
    while env.agents and steps < 500:
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
    assert total_reward > 0 or steps >= 500


def test_pettingzoo_api():
    """Run PettingZoo's standard API compliance test."""
    env = MahjongEnv()
    # api_test runs a series of checks on the env
    api_test(env, num_cycles=5, verbose_progress=False)
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_env.py -v
```

**Step 3: Implement `env.py`**

```python
"""PettingZoo AEC environment wrapper for Taiwan 16-tile Mahjong."""
from __future__ import annotations

import functools
from typing import Any

import gymnasium
import numpy as np
from pettingzoo import AECEnv
from pettingzoo.utils import wrappers

from engine.game_session import GameSession
from engine.scorer import score_hand
from engine.win_validator import decompose_hand
from training.observation import ActionEncoder, ObservationEncoder
from training.rewards import compute_rewards


def env(**kwargs: Any) -> MahjongEnv:
    """Create a wrapped MahjongEnv."""
    return MahjongEnv(**kwargs)


class MahjongEnv(AECEnv):
    """PettingZoo AEC environment for Taiwan 16-tile Mahjong."""

    metadata = {"render_modes": [], "name": "mahjong_v0"}

    def __init__(self) -> None:
        super().__init__()
        self.possible_agents = [f"player_{i}" for i in range(4)]
        self._obs_encoder = ObservationEncoder()
        self._act_encoder = ActionEncoder()

        self._session: GameSession | None = None
        self._cumulative_rewards: dict[str, float] = {}
        self._legal_actions_cache: dict[str, np.ndarray] = {}

    @functools.lru_cache(maxsize=4)
    def observation_space(self, agent: str) -> gymnasium.spaces.Box:
        return gymnasium.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self._obs_encoder.obs_size,),
            dtype=np.float32,
        )

    @functools.lru_cache(maxsize=4)
    def action_space(self, agent: str) -> gymnasium.spaces.Discrete:
        return gymnasium.spaces.Discrete(self._act_encoder.action_size)

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> None:
        self.agents = list(self.possible_agents)
        self._session = GameSession()
        self._session.start_hand()

        self.rewards = {a: 0.0 for a in self.agents}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.infos = {a: {} for a in self.agents}

        self._update_agent_selection()
        self._update_action_masks()

    def _agent_to_idx(self, agent: str) -> int:
        return int(agent.split("_")[1])

    def _idx_to_agent(self, idx: int) -> str:
        return f"player_{idx}"

    def _update_agent_selection(self) -> None:
        """Set agent_selection to the current player."""
        gs = self._session.state
        if gs.phase in ("win", "draw"):
            return
        self.agent_selection = self._idx_to_agent(gs.current_player)

    def _update_action_masks(self) -> None:
        """Cache action masks for all agents."""
        self._legal_actions_cache.clear()
        gs = self._session.state
        if gs.phase in ("win", "draw"):
            return
        for agent in self.agents:
            idx = self._agent_to_idx(agent)
            legal = self._session.get_legal_actions(idx)
            if legal:
                self._legal_actions_cache[agent] = self._act_encoder.legal_actions_to_mask(legal)
            else:
                self._legal_actions_cache[agent] = np.zeros(
                    self._act_encoder.action_size, dtype=np.float32
                )

    def observe(self, agent: str) -> np.ndarray:
        idx = self._agent_to_idx(agent)
        return self._obs_encoder.encode(self._session.state, idx)

    def last(
        self,
        observe: bool = True,
    ) -> tuple[np.ndarray | None, float, bool, bool, dict]:
        agent = self.agent_selection
        obs = self.observe(agent) if observe else None
        reward = self._cumulative_rewards.get(agent, 0.0)
        term = self.terminations.get(agent, False)
        trunc = self.truncations.get(agent, False)
        mask = self._legal_actions_cache.get(
            agent,
            np.zeros(self._act_encoder.action_size, dtype=np.float32),
        )
        info = {"action_mask": mask}
        return obs, reward, term, trunc, info

    def step(self, action: int | None) -> None:
        agent = self.agent_selection
        idx = self._agent_to_idx(agent)

        # Handle terminated agent
        if self.terminations[agent] or self.truncations[agent]:
            self._was_dead_step(action)
            return

        # Reset step rewards
        for a in self.agents:
            self.rewards[a] = 0.0

        # Convert int action to engine Action
        engine_action = self._act_encoder.int_to_action(action, player_idx=idx)

        # For pong/open_kong during claim phase, set the tile from pending discard
        gs = self._session.state
        if engine_action.type in ("pong", "open_kong") and gs.last_discard:
            engine_action.tile = gs.last_discard

        # Execute in engine
        self._session.step(engine_action)

        # Check for game end
        gs = self._session.state
        if gs.phase in ("win", "draw"):
            self._handle_game_end()
            return

        # Advance to next player
        self._update_agent_selection()
        self._update_action_masks()

        # If current agent has no legal actions, auto-advance
        # (This handles internal phases like flower replacement)
        safety = 0
        while (
            self.agents
            and gs.phase == "play"
            and self._legal_actions_cache.get(self.agent_selection, np.zeros(1)).sum() == 0
            and safety < 20
        ):
            safety += 1
            self._update_agent_selection()
            self._update_action_masks()

    def _handle_game_end(self) -> None:
        """Compute rewards and terminate all agents."""
        gs = self._session.state

        winner_idx = None
        total_tai = 0

        if gs.phase == "win":
            # Find winner: the player whose last action was "win"
            # In the engine, after a win step, current_player is the winner
            # We look for the player with a winning hand
            for i in range(4):
                p = gs.players[i]
                from engine.win_validator import is_winning_hand

                # Check if this player won (they'd have 17 tiles effectively)
                win_tile = gs.last_discard or (p.hand[-1] if p.hand else None)
                if win_tile and is_winning_hand(
                    p.hand, p.melds, p.flowers, win_tile
                ):
                    winner_idx = i
                    decomp = decompose_hand(p.hand, p.melds)
                    try:
                        result = score_hand(
                            gs,
                            winner_idx=i,
                            win_tile=win_tile,
                            win_type="self_draw" if gs.last_action == "draw" else "discard",
                            hand=p.hand,
                            melds=p.melds,
                            flowers=p.flowers,
                            decomp=decomp,
                        )
                        total_tai = result.total
                    except Exception:
                        total_tai = 1  # Fallback: minimum win
                    break

        rewards = compute_rewards(
            winner_idx=winner_idx,
            total_tai=total_tai,
        )

        for i, agent in enumerate(self.possible_agents):
            if agent in self.agents:
                self.rewards[agent] = rewards[i]
                self._cumulative_rewards[agent] = (
                    self._cumulative_rewards.get(agent, 0.0) + rewards[i]
                )
                self.terminations[agent] = True

        self.agents = []
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_env.py -v
```

Expected: PASS (PettingZoo API test may need iteration — address failures)

**Step 5: Commit**

```bash
git add backend/training/env.py backend/tests/test_env.py
git commit -m "feat: add PettingZoo AEC environment wrapper for mahjong"
```

---

## Task 5: Neural Network (`network.py`)

**Files:**
- Create: `backend/training/network.py`
- Create: `backend/tests/test_network.py`

**Step 1: Write failing tests**

```python
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
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_network.py -v
```

**Step 3: Implement `network.py`**

```python
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

    def __init__(
        self,
        obs_size: int,
        action_size: int,
        cfg: TrainingConfig,
    ) -> None:
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
        self,
        obs: torch.Tensor,
        action_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning masked logits and value.

        Args:
            obs: (batch, obs_size) float tensor
            action_mask: (batch, action_size) binary mask (1=legal, 0=illegal)

        Returns:
            logits: (batch, action_size) — illegal actions set to -inf
            value: (batch, 1)
        """
        features = self.backbone(obs)
        logits = self.policy_head(features)
        value = self.value_head(features)

        # Mask illegal actions
        logits = logits.masked_fill(action_mask == 0, float("-inf"))
        return logits, value

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        action_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample action from policy and return action, log_prob, entropy, value."""
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
        """Evaluate given actions under current policy."""
        logits, value = self(obs, action_mask)
        dist = Categorical(logits=logits)
        log_prob = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_prob, entropy, value
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_network.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/network.py backend/tests/test_network.py
git commit -m "feat: add MLP network with policy/value heads and action masking"
```

---

## Task 6: PPO Algorithm (`ppo.py`)

**Files:**
- Create: `backend/training/ppo.py`
- Create: `backend/tests/test_ppo.py`

**Step 1: Write failing tests**

```python
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
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_ppo.py -v
```

**Step 3: Implement `ppo.py`**

```python
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
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_ppo.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/ppo.py backend/tests/test_ppo.py
git commit -m "feat: add CleanRL-style PPO with rollout buffer and GAE"
```

---

## Task 7: Checkpoint System (`checkpoints.py`)

**Files:**
- Create: `backend/training/checkpoints.py`
- Create: `backend/tests/test_checkpoints.py`

**Step 1: Write failing tests**

```python
"""Tests for checkpoint save/load/retention."""
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
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_checkpoints.py -v
```

**Step 3: Implement `checkpoints.py`**

```python
"""Checkpoint save/load with retention policy and ELO tracking."""
from __future__ import annotations

import json
from pathlib import Path

import torch

from training.config import TrainingConfig
from training.network import MahjongNetwork


class CheckpointManager:
    """Manages saving, loading, and pruning of training checkpoints."""

    def __init__(self, cfg: TrainingConfig) -> None:
        self.cfg = cfg
        self.dir = Path(cfg.checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.best_elo: float = -float("inf")
        self._elo_history: list[dict] = []

        # Load existing metadata if resuming
        meta_path = self.dir / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self._elo_history = meta.get("elo_history", [])
            self.best_elo = meta.get("best_elo", -float("inf"))

    def save(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer,
        episode: int,
        elo: float,
    ) -> Path:
        """Save checkpoint and update metadata."""
        checkpoint = {
            "model_state_dict": network.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "episode": episode,
            "elo": elo,
        }

        # Save periodic checkpoint
        path = self.dir / f"ep_{episode:06d}.pt"
        torch.save(checkpoint, path)

        # Save latest
        torch.save(checkpoint, self.dir / "latest.pt")

        # Update best ELO
        if elo > self.best_elo:
            self.best_elo = elo
            torch.save(checkpoint, self.dir / "best_elo.pt")

        # Update metadata
        self._elo_history.append({"episode": episode, "elo": elo})
        self._save_metadata()

        # Prune old checkpoints
        self._prune()

        return path

    def load_latest(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> dict:
        """Load latest checkpoint into network and optimizer."""
        path = self.dir / "latest.pt"
        return self._load(path, network, optimizer)

    def load_best(
        self,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> dict:
        """Load best ELO checkpoint."""
        path = self.dir / "best_elo.pt"
        return self._load(path, network, optimizer)

    def load_episode(
        self,
        episode: int,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> dict:
        """Load specific episode checkpoint."""
        path = self.dir / f"ep_{episode:06d}.pt"
        return self._load(path, network, optimizer)

    def _load(
        self,
        path: Path,
        network: MahjongNetwork,
        optimizer: torch.optim.Optimizer | None,
    ) -> dict:
        checkpoint = torch.load(path, weights_only=True)
        network.load_state_dict(checkpoint["model_state_dict"])
        if optimizer is not None and "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        return {
            "episode": checkpoint.get("episode", 0),
            "elo": checkpoint.get("elo", self.cfg.elo_initial),
        }

    def list_checkpoints(self) -> list[Path]:
        """List all periodic checkpoint files sorted by episode."""
        return sorted(self.dir.glob("ep_*.pt"))

    def _prune(self) -> None:
        """Remove old periodic checkpoints beyond pool_max_size."""
        periodic = self.list_checkpoints()
        if len(periodic) > self.cfg.pool_max_size:
            to_remove = periodic[: len(periodic) - self.cfg.pool_max_size]
            for p in to_remove:
                p.unlink()

    def _save_metadata(self) -> None:
        meta = {
            "best_elo": self.best_elo,
            "elo_history": self._elo_history,
        }
        (self.dir / "metadata.json").write_text(json.dumps(meta, indent=2))
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_checkpoints.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/checkpoints.py backend/tests/test_checkpoints.py
git commit -m "feat: add checkpoint manager with save/load/retention/ELO tracking"
```

---

## Task 8: TensorBoard Metrics (`metrics.py`)

**Files:**
- Create: `backend/training/metrics.py`
- Create: `backend/tests/test_metrics.py`

**Step 1: Write failing tests**

```python
"""Tests for TensorBoard metrics logger."""
from training.metrics import MetricsLogger


def test_logger_creation(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    assert logger is not None


def test_log_training_step(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_training(
        step=100,
        policy_loss=0.5,
        value_loss=0.3,
        entropy=1.2,
        clip_fraction=0.1,
        learning_rate=3e-4,
    )
    logger.close()
    # Check that TensorBoard event file was created
    event_files = list((tmp_path / "runs").rglob("events.out.*"))
    assert len(event_files) > 0


def test_log_evaluation(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_evaluation(
        step=200,
        win_rate=0.55,
        avg_reward=0.3,
        avg_hand_value=3.5,
        draw_rate=0.15,
    )
    logger.close()


def test_log_league(tmp_path):
    logger = MetricsLogger(log_dir=tmp_path / "runs")
    logger.log_league(
        step=300,
        current_elo=1100.0,
        best_elo=1100.0,
        pool_size=5,
    )
    logger.close()
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_metrics.py -v
```

**Step 3: Implement `metrics.py`**

```python
"""TensorBoard metrics logging for training pipeline."""
from __future__ import annotations

from pathlib import Path

from torch.utils.tensorboard import SummaryWriter


class MetricsLogger:
    """Wraps TensorBoard SummaryWriter with typed logging methods."""

    def __init__(self, log_dir: Path | str) -> None:
        self._writer = SummaryWriter(log_dir=str(log_dir))

    def log_training(
        self,
        step: int,
        policy_loss: float,
        value_loss: float,
        entropy: float,
        clip_fraction: float,
        learning_rate: float,
    ) -> None:
        self._writer.add_scalar("train/policy_loss", policy_loss, step)
        self._writer.add_scalar("train/value_loss", value_loss, step)
        self._writer.add_scalar("train/entropy", entropy, step)
        self._writer.add_scalar("train/clip_fraction", clip_fraction, step)
        self._writer.add_scalar("train/learning_rate", learning_rate, step)

    def log_evaluation(
        self,
        step: int,
        win_rate: float,
        avg_reward: float,
        avg_hand_value: float,
        draw_rate: float,
    ) -> None:
        self._writer.add_scalar("eval/win_rate_vs_rule_based", win_rate, step)
        self._writer.add_scalar("eval/avg_episode_reward", avg_reward, step)
        self._writer.add_scalar("eval/avg_hand_value_on_win", avg_hand_value, step)
        self._writer.add_scalar("eval/draw_rate", draw_rate, step)

    def log_league(
        self,
        step: int,
        current_elo: float,
        best_elo: float,
        pool_size: int,
    ) -> None:
        self._writer.add_scalar("league/current_elo", current_elo, step)
        self._writer.add_scalar("league/best_elo", best_elo, step)
        self._writer.add_scalar("league/pool_size", pool_size, step)

    def log_episode(
        self,
        step: int,
        episode_length: int,
        tiles_remaining: int,
    ) -> None:
        self._writer.add_scalar("env/episode_length", episode_length, step)
        self._writer.add_scalar("env/tiles_remaining", tiles_remaining, step)

    def close(self) -> None:
        self._writer.close()
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/metrics.py backend/tests/test_metrics.py
git commit -m "feat: add TensorBoard metrics logger"
```

---

## Task 9: Self-Play League (`self_play.py`)

**Files:**
- Create: `backend/training/self_play.py`
- Create: `backend/tests/test_self_play.py`

**Step 1: Write failing tests**

```python
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
    # Add some checkpoints first
    for ep in range(500, 3000, 500):
        mgr.add_checkpoint(episode=ep, network=net, elo=1000.0 + ep * 0.01)
    opponents = mgr.sample_opponents(phase="selfplay")
    assert len(opponents) == 3
    # Should be mix of checkpoint IDs and "rule_based"
    for o in opponents:
        assert isinstance(o, (str, int))
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_self_play.py -v
```

**Step 3: Implement `self_play.py`**

```python
"""Self-play league manager with ELO tracking and opponent sampling."""
from __future__ import annotations

import math
import random
from pathlib import Path

import torch

from training.config import TrainingConfig
from training.network import MahjongNetwork


class EloTracker:
    """Tracks ELO ratings for agents."""

    def __init__(self, initial_elo: float = 1000.0, k: float = 32.0) -> None:
        self._elo: dict[str, float] = {}
        self._initial = initial_elo
        self._k = k

    def get_elo(self, agent_id: str) -> float:
        return self._elo.get(agent_id, self._initial)

    def set_elo(self, agent_id: str, elo: float) -> None:
        self._elo[agent_id] = elo

    def update(self, winner: str, losers: list[str]) -> None:
        """Update ELO after a game. Winner beat all losers."""
        winner_elo = self.get_elo(winner)
        for loser in losers:
            loser_elo = self.get_elo(loser)
            expected_w = 1.0 / (1.0 + math.pow(10, (loser_elo - winner_elo) / 400))
            expected_l = 1.0 - expected_w
            self._elo[winner] = self.get_elo(winner) + self._k * (1.0 - expected_w)
            self._elo[loser] = self.get_elo(loser) + self._k * (0.0 - expected_l)


class LeagueManager:
    """Manages opponent pool for self-play training."""

    def __init__(self, cfg: TrainingConfig) -> None:
        self.cfg = cfg
        self.elo_tracker = EloTracker(
            initial_elo=cfg.elo_initial,
            k=cfg.elo_k,
        )
        # Pool: list of (episode, state_dict, elo)
        self._pool: list[dict] = []

    @property
    def pool_size(self) -> int:
        return len(self._pool)

    def add_checkpoint(
        self,
        episode: int,
        network: MahjongNetwork,
        elo: float,
    ) -> None:
        """Add current network snapshot to the opponent pool."""
        entry = {
            "episode": episode,
            "state_dict": {k: v.cpu().clone() for k, v in network.state_dict().items()},
            "elo": elo,
        }
        self._pool.append(entry)

        # Prune to max size (keep most recent)
        if len(self._pool) > self.cfg.pool_max_size:
            # Keep best ELO entry
            best_idx = max(range(len(self._pool)), key=lambda i: self._pool[i]["elo"])
            best = self._pool[best_idx]
            # Keep last pool_max_size - 1 plus best
            recent = self._pool[-(self.cfg.pool_max_size - 1) :]
            if best not in recent:
                recent = [best] + recent[: self.cfg.pool_max_size - 1]
            self._pool = recent

    def sample_opponents(self, phase: str) -> list[str | int]:
        """Sample 3 opponent identifiers for a training game.

        Args:
            phase: "warmup" or "selfplay"

        Returns:
            List of 3 opponent IDs:
            - "rule_based" for rule-based AI
            - int (episode number) for a pool checkpoint
        """
        if phase == "warmup" or not self._pool:
            return ["rule_based"] * 3

        opponents: list[str | int] = []
        for _ in range(3):
            r = random.random()
            if r < self.cfg.pool_sample_rule_based:
                opponents.append("rule_based")
            elif r < self.cfg.pool_sample_rule_based + self.cfg.pool_sample_old:
                # Sample from older half of pool
                if len(self._pool) > 1:
                    mid = len(self._pool) // 2
                    entry = random.choice(self._pool[:mid])
                else:
                    entry = self._pool[0]
                opponents.append(entry["episode"])
            else:
                # Sample from recent half
                mid = max(len(self._pool) // 2, 1)
                entry = random.choice(self._pool[-mid:])
                opponents.append(entry["episode"])
        return opponents

    def load_opponent_network(
        self,
        opponent_id: str | int,
        network: MahjongNetwork,
    ) -> None:
        """Load opponent weights into the given network.

        Does nothing for 'rule_based' — caller handles that separately.
        """
        if opponent_id == "rule_based":
            return
        for entry in self._pool:
            if entry["episode"] == opponent_id:
                network.load_state_dict(entry["state_dict"])
                return
        raise ValueError(f"Checkpoint for episode {opponent_id} not found in pool")
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_self_play.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/training/self_play.py backend/tests/test_self_play.py
git commit -m "feat: add self-play league manager with ELO tracking"
```

---

## Task 10: Training Entry Point (`train.py`)

**Files:**
- Create: `backend/training/train.py`
- Create: `backend/tests/test_train_integration.py`

**Step 1: Write integration test (lightweight)**

```python
"""Integration test for training loop — runs a few episodes to verify wiring."""
from training.train import run_training
from training.config import TrainingConfig


def test_warmup_runs_briefly(tmp_path):
    """Run 2 warmup episodes to verify the full pipeline works."""
    cfg = TrainingConfig(
        warmup_episodes=2,
        total_episodes=2,
        eval_interval=1,
        eval_games=2,
        checkpoint_interval=1,
        n_steps=64,
        n_epochs=1,
        batch_size=16,
        n_envs=1,
        checkpoint_dir=tmp_path / "ckpt",
        log_dir=tmp_path / "logs",
        device="cpu",
    )
    run_training(cfg)
    # Check that checkpoint was saved
    assert (tmp_path / "ckpt" / "latest.pt").exists()
```

**Step 2: Run to verify fail**

```bash
uv run pytest tests/test_train_integration.py -v -s
```

**Step 3: Implement `train.py`**

```python
"""Main training entry point: warm-up → self-play → evaluate."""
from __future__ import annotations

import time

import numpy as np
import torch

from ai.rule_based import RuleBasedAI
from engine.game_session import GameSession
from training.checkpoints import CheckpointManager
from training.config import TrainingConfig
from training.env import MahjongEnv
from training.metrics import MetricsLogger
from training.network import MahjongNetwork
from training.observation import ActionEncoder, ObservationEncoder
from training.ppo import RolloutBuffer, ppo_update
from training.self_play import LeagueManager


def _evaluate_vs_rule_based(
    network: MahjongNetwork,
    obs_encoder: ObservationEncoder,
    act_encoder: ActionEncoder,
    n_games: int,
    device: str,
) -> dict[str, float]:
    """Play n_games with RL agent (seat 0) vs 3 rule-based AIs.

    Returns dict with win_rate, avg_reward, avg_hand_value, draw_rate.
    """
    rule_ai = RuleBasedAI()
    wins = 0
    draws = 0
    total_reward = 0.0
    total_hand_value = 0.0
    win_count_for_avg = 0

    for _ in range(n_games):
        env = MahjongEnv()
        env.reset()

        while env.agents:
            obs, reward, term, trunc, info = env.last()
            if term or trunc:
                env.step(None)
                continue

            agent = env.agent_selection
            idx = int(agent.split("_")[1])

            if idx == 0:
                # RL agent
                mask = info["action_mask"]
                obs_t = torch.tensor(obs, device=device).unsqueeze(0)
                mask_t = torch.tensor(mask, device=device).unsqueeze(0)
                with torch.no_grad():
                    action, _, _, _ = network.get_action_and_value(obs_t, mask_t)
                env.step(action.item())
            else:
                # Rule-based AI
                gs = env._session.state
                legal = env._session.get_legal_actions(idx)
                if legal:
                    chosen = rule_ai.choose_action(gs, idx, legal)
                    action_int = act_encoder.action_to_int(chosen)
                    env.step(action_int)
                else:
                    env.step(None)

        # Check outcome
        r = env._cumulative_rewards.get("player_0", 0.0)
        total_reward += r
        if r > 0:
            wins += 1
        elif r == -0.1:
            draws += 1

    return {
        "win_rate": wins / max(n_games, 1),
        "avg_reward": total_reward / max(n_games, 1),
        "avg_hand_value": total_hand_value / max(win_count_for_avg, 1),
        "draw_rate": draws / max(n_games, 1),
    }


def _collect_rollout(
    env: MahjongEnv,
    network: MahjongNetwork,
    buffer: RolloutBuffer,
    obs_encoder: ObservationEncoder,
    act_encoder: ActionEncoder,
    rule_ai: RuleBasedAI,
    n_steps: int,
    device: str,
) -> int:
    """Collect transitions from env into buffer. Returns episodes completed."""
    episodes_done = 0
    steps_collected = 0

    while steps_collected < n_steps:
        if not env.agents:
            env.reset()

        obs, reward, term, trunc, info = env.last()
        if term or trunc:
            env.step(None)
            continue

        agent = env.agent_selection
        idx = int(agent.split("_")[1])

        if idx == 0:
            # RL agent: collect transition
            mask = info["action_mask"]
            obs_t = torch.tensor(obs, device=device).unsqueeze(0)
            mask_t = torch.tensor(mask, device=device).unsqueeze(0)

            with torch.no_grad():
                action, log_prob, _, value = network.get_action_and_value(obs_t, mask_t)

            env.step(action.item())

            # Get reward after step
            _, step_reward, done, _, _ = env.last()
            if not env.agents:
                done = True
                step_reward = env._cumulative_rewards.get("player_0", 0.0)

            buffer.add(
                obs=obs,
                action=action.item(),
                reward=step_reward if done else 0.0,
                done=done,
                log_prob=log_prob.item(),
                value=value.item(),
                action_mask=mask,
            )
            steps_collected += 1

            if done:
                episodes_done += 1
        else:
            # Rule-based opponent
            gs = env._session.state
            legal = env._session.get_legal_actions(idx)
            if legal:
                chosen = rule_ai.choose_action(gs, idx, legal)
                action_int = act_encoder.action_to_int(chosen)
                env.step(action_int)
            else:
                env.step(None)

    return episodes_done


def run_training(cfg: TrainingConfig) -> None:
    """Main training loop."""
    device = cfg.device if torch.cuda.is_available() or cfg.device == "cpu" else "cpu"

    obs_encoder = ObservationEncoder()
    act_encoder = ActionEncoder()

    network = MahjongNetwork(
        obs_size=obs_encoder.obs_size,
        action_size=act_encoder.action_size,
        cfg=cfg,
    ).to(device)

    optimizer = torch.optim.Adam(network.parameters(), lr=cfg.learning_rate)
    ckpt_mgr = CheckpointManager(cfg)
    league = LeagueManager(cfg)
    logger = MetricsLogger(log_dir=cfg.log_dir)
    rule_ai = RuleBasedAI()

    buffer = RolloutBuffer(
        capacity=cfg.n_steps,
        obs_size=obs_encoder.obs_size,
        action_size=act_encoder.action_size,
    )

    total_episodes = 0
    phase = "warmup"
    current_elo = cfg.elo_initial

    print(f"Starting training on {device}")
    print(f"Phase: {phase}")

    while total_episodes < cfg.total_episodes:
        # Collect rollout
        env = MahjongEnv()
        env.reset()
        buffer.reset()

        episodes = _collect_rollout(
            env=env,
            network=network,
            buffer=buffer,
            obs_encoder=obs_encoder,
            act_encoder=act_encoder,
            rule_ai=rule_ai,
            n_steps=cfg.n_steps,
            device=device,
        )
        total_episodes += episodes

        # Compute advantages
        last_value = 0.0
        if env.agents:
            obs, _, _, _, _ = env.last()
            obs_t = torch.tensor(obs, device=device).unsqueeze(0)
            mask_t = torch.ones(1, act_encoder.action_size, device=device)
            with torch.no_grad():
                _, last_value_t = network(obs_t, mask_t)
                last_value = last_value_t.item()

        buffer.compute_gae(
            last_value=last_value,
            gamma=cfg.gamma,
            gae_lambda=cfg.gae_lambda,
        )

        # PPO update
        losses = ppo_update(network, optimizer, buffer, cfg, device=device)

        # Learning rate decay
        progress = total_episodes / cfg.total_episodes
        lr = cfg.learning_rate * (1.0 - progress)
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        # Log training metrics
        logger.log_training(
            step=total_episodes,
            policy_loss=losses["policy_loss"],
            value_loss=losses["value_loss"],
            entropy=losses["entropy"],
            clip_fraction=losses["clip_fraction"],
            learning_rate=lr,
        )

        # Evaluation
        if total_episodes % cfg.eval_interval < episodes or total_episodes <= episodes:
            eval_results = _evaluate_vs_rule_based(
                network=network,
                obs_encoder=obs_encoder,
                act_encoder=act_encoder,
                n_games=cfg.eval_games,
                device=device,
            )
            logger.log_evaluation(step=total_episodes, **eval_results)
            print(
                f"Episode {total_episodes} | "
                f"Win rate: {eval_results['win_rate']:.1%} | "
                f"Phase: {phase}"
            )

            # Phase transition check
            if (
                phase == "warmup"
                and eval_results["win_rate"] >= cfg.warmup_win_rate_threshold
            ):
                phase = "selfplay"
                print(f"Transitioning to self-play at episode {total_episodes}")

        # Checkpoint
        if total_episodes % cfg.checkpoint_interval < episodes or total_episodes <= episodes:
            ckpt_mgr.save(network, optimizer, episode=total_episodes, elo=current_elo)
            league.add_checkpoint(
                episode=total_episodes,
                network=network,
                elo=current_elo,
            )

    # Final save
    ckpt_mgr.save(network, optimizer, episode=total_episodes, elo=current_elo)
    logger.close()
    print(f"Training complete. Total episodes: {total_episodes}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Mahjong RL agent")
    parser.add_argument("--device", default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--episodes", type=int, default=200_000)
    parser.add_argument("--checkpoint-dir", default="checkpoints")
    parser.add_argument("--log-dir", default="runs")
    args = parser.parse_args()

    config = TrainingConfig(
        device=args.device,
        total_episodes=args.episodes,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
    )
    run_training(config)
```

**Step 4: Run integration test**

```bash
uv run pytest tests/test_train_integration.py -v -s --timeout=120
```

Expected: PASS (may take 30-60s for 2 episodes)

**Step 5: Commit**

```bash
git add backend/training/train.py backend/tests/test_train_integration.py
git commit -m "feat: add training entry point with warm-up and self-play loop"
```

---

## Task 11: Docker Setup

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ ./backend/

# Install Python deps
RUN pip install --no-cache-dir -e "./backend[train]"

# Default entrypoint
ENTRYPOINT ["python", "-m", "training.train"]
CMD ["--device", "cuda", "--episodes", "200000"]
```

**Step 2: Create .dockerignore**

```
frontend/
node_modules/
.git/
*.pyc
__pycache__/
checkpoints/
runs/
.env
```

**Step 3: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Docker setup for GPU training"
```

---

## Task 12: Final Integration Verification

**Step 1: Run full test suite**

```bash
cd backend && uv run pytest -v --ignore=tests/test_integration.py --ignore=tests/test_train_integration.py
```

Expected: All PASS

**Step 2: Run training integration test**

```bash
uv run pytest tests/test_train_integration.py -v -s --timeout=120
```

Expected: PASS

**Step 3: Run existing engine tests (regression check)**

```bash
uv run pytest --cov=engine --cov=ai --cov-fail-under=85 --ignore=tests/test_integration.py -q
```

Expected: Coverage ≥85%, all PASS

**Step 4: Final commit with any fixes**

```bash
git add -A
git commit -m "test: verify full pipeline integration and regression suite"
```

---

## Summary

| Task | Component | Est. Lines | Key Risk |
|------|-----------|-----------|----------|
| 0 | Config + deps | ~80 | PyTorch install issues |
| 1 | Observation encoder | ~120 | Feature alignment with game state |
| 2 | Action encoder | ~150 | Action space completeness |
| 3 | Rewards | ~30 | Reward scale tuning |
| 4 | PettingZoo env | ~200 | AEC compliance, step/claim logic |
| 5 | Neural network | ~100 | Masking correctness |
| 6 | PPO algorithm | ~200 | GAE computation, loss math |
| 7 | Checkpoint system | ~120 | Serialization, retention |
| 8 | Metrics logger | ~60 | TensorBoard compatibility |
| 9 | Self-play league | ~130 | Pool sampling, ELO math |
| 10 | Training loop | ~250 | Wiring all components, rollout collection |
| 11 | Docker | ~20 | CUDA image compatibility |
| 12 | Integration verification | ~0 | Regression test |
