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
