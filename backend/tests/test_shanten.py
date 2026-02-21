"""Tests for the shanten number calculator (Taiwan 16-tile Mahjong).

Taiwan Mahjong hands:
  - 16 tiles in hand (before draw) with 0 melds
  - 17 tiles = winning hand (5 sets + 1 pair) with 0 melds
  - With N melds: hand has (17 - 3*N) tiles for a winning hand
"""
import pytest
from ai.shanten import shanten_number, tenpai_tiles
from engine.state import Meld


# ---------------------------------------------------------------------------
# Winning hands (shanten == -1)
# ---------------------------------------------------------------------------

def test_complete_hand_is_minus_one():
    """17 tiles forming 5 sets + 1 pair => shanten -1."""
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p6p + 1s1s
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "6p", "1s", "1s",
    ]
    assert shanten_number(hand, []) == -1


def test_complete_hand_all_triplets():
    """17 tiles: 5 triplets + 1 pair => shanten -1."""
    hand = [
        "1m", "1m", "1m", "2p", "2p", "2p", "3s", "3s", "3s",
        "E", "E", "E", "N", "N", "N", "C", "C",
    ]
    assert shanten_number(hand, []) == -1


def test_shanten_with_melds_complete():
    """1 exposed meld + 14 hand tiles forming 4 sets + pair => shanten -1."""
    melds = [Meld(type="pong", tiles=["E", "E", "E"], from_player=1)]
    # 4 sets + 1 pair = 14 hand tiles
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "1s", "1s",
    ]
    assert shanten_number(hand, melds) == -1


# ---------------------------------------------------------------------------
# Tenpai (shanten == 0)
# ---------------------------------------------------------------------------

def test_tenpai_is_zero():
    """16 tiles, one tile away from winning => shanten 0."""
    # Missing one tile to complete the 5th set or pair
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p + 1s1s  (need 6p)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "1s", "1s",
    ]
    assert shanten_number(hand, []) == 0


def test_tenpai_pair_wait():
    """16 tiles, waiting on a pair tile => shanten 0."""
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p6p + 1s  (need 1s for pair)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "6p", "1s",
    ]
    assert shanten_number(hand, []) == 0


def test_tenpai_with_meld():
    """1 meld + 13 hand tiles, tenpai => shanten 0."""
    melds = [Meld(type="pong", tiles=["E", "E", "E"], from_player=1)]
    # 4m5m6m 7m8m9m 1p2p3p 4p5p + 1s1s  (need 3p/6p)
    hand = [
        "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "1s", "1s",
    ]
    assert shanten_number(hand, melds) == 0


# ---------------------------------------------------------------------------
# One away from tenpai (shanten == 1)
# ---------------------------------------------------------------------------

def test_one_from_tenpai():
    """15 tiles, two tiles away from winning => shanten 1."""
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p + 1s1s  (need to form 5th set)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "1s", "1s",
    ]
    assert shanten_number(hand, []) == 1


# ---------------------------------------------------------------------------
# Higher shanten values
# ---------------------------------------------------------------------------

def test_high_shanten_disconnected_hand():
    """Badly disconnected hand should have high shanten."""
    # All isolated tiles, no sets possible
    hand = [
        "1m", "3m", "5m", "7m", "9m",
        "1p", "3p", "5p", "7p", "9p",
        "E", "S", "W", "N", "C", "F",
    ]
    s = shanten_number(hand, [])
    # No complete sets, but skip-one partial waits exist (1m+3m, 5m+7m, etc.)
    # shanten = 2*5 - 0 mentsu - 4 taatsu = 6
    assert s == 6


# ---------------------------------------------------------------------------
# tenpai_tiles
# ---------------------------------------------------------------------------

def test_tenpai_tiles_sequence_wait():
    """Verify tenpai_tiles returns correct waiting tiles for a sequence wait."""
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p + 1s1s  (waiting on 3p or 6p)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "1s", "1s",
    ]
    waits = tenpai_tiles(hand, [])
    assert "3p" in waits or "6p" in waits
    assert len(waits) > 0


def test_tenpai_tiles_pair_wait():
    """Verify tenpai_tiles returns the pair tile for a single wait."""
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p6p + 1s  (waiting on 1s)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "5p", "6p", "1s",
    ]
    waits = tenpai_tiles(hand, [])
    assert "1s" in waits


def test_tenpai_tiles_empty_when_not_tenpai():
    """Non-tenpai hand should return empty list."""
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "4p", "1s", "1s",
    ]
    waits = tenpai_tiles(hand, [])
    assert waits == []


def test_tenpai_tiles_with_meld():
    """Tenpai with an exposed meld should return correct waits."""
    melds = [Meld(type="pong", tiles=["E", "E", "E"], from_player=1)]
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p + 1s  (need 1s for pair)
    hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "3p", "1s",
    ]
    waits = tenpai_tiles(hand, melds)
    assert "1s" in waits
