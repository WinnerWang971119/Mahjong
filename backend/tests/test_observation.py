"""Tests for observation encoder."""
from __future__ import annotations

import numpy as np

from engine.game_session import GameSession, Action
from training.observation import (
    ActionEncoder,
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


# ---------------------------------------------------------------
# ActionEncoder tests
# ---------------------------------------------------------------


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
