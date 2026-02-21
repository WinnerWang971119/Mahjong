"""Shanten number calculator for Taiwan 16-tile Mahjong.

Taiwan Mahjong uses 16 tiles in hand. A winning hand consists of
5 sets (sequences or triplets) plus 1 pair, totaling 17 tiles
(16 in hand + 1 drawn/claimed tile). With exposed melds, the hand
tiles are reduced accordingly.

This implementation uses an array-based representation for performance:
tiles are mapped to indices 0-33 (9 man + 9 pin + 9 sou + 7 honor),
and counts are tracked in a flat list to avoid repeated Counter() calls
and list copies.
"""
from __future__ import annotations

from engine.tiles import (
    FLOWERS,
    build_full_deck,
    is_number_tile,
    tile_suit,
    tile_value,
)
from engine.state import Meld
from engine.win_validator import is_standard_win

# --- Tile-to-index mapping ---
# 0-8: 1m-9m, 9-17: 1p-9p, 18-26: 1s-9s, 27-33: E,S,W,N,C,F,B
_SUIT_OFFSET = {"m": 0, "p": 9, "s": 18}
_HONOR_INDEX = {"E": 27, "S": 28, "W": 29, "N": 30, "C": 31, "F": 32, "B": 33}
_INDEX_TO_TILE: list[str] = []
for _s in ("m", "p", "s"):
    for _v in range(1, 10):
        _INDEX_TO_TILE.append(f"{_v}{_s}")
for _h in ("E", "S", "W", "N", "C", "F", "B"):
    _INDEX_TO_TILE.append(_h)

_NUM_TILE_TYPES = 34


def _tile_to_idx(tile: str) -> int:
    if len(tile) == 2 and tile[1] in _SUIT_OFFSET:
        return int(tile[0]) - 1 + _SUIT_OFFSET[tile[1]]
    return _HONOR_INDEX[tile]


def _hand_to_counts(hand: list[str]) -> list[int]:
    counts = [0] * _NUM_TILE_TYPES
    for t in hand:
        counts[_tile_to_idx(t)] += 1
    return counts


def shanten_number(hand: list[str], melds: list[Meld]) -> int:
    """Calculate shanten number for Taiwan 16-tile Mahjong.

    Returns:
      -1 = winning hand (tsumo / already complete)
       0 = tenpai (one tile away from win)
       n = n tiles needed to reach tenpai
    """
    sets_needed = 5 - len(melds)
    counts = _hand_to_counts(hand)
    best = [2 * sets_needed]
    _search(counts, 0, sets_needed, 0, 0, False, best)
    return best[0]


def _search(
    counts: list[int],
    idx: int,
    sets_needed: int,
    mentsu: int,
    taatsu: int,
    jantai: bool,
    best: list[int],
) -> None:
    """Recursive backtracking search over tile count array."""
    # Evaluate current state
    effective_taatsu = min(taatsu, sets_needed - mentsu)
    s = 2 * (sets_needed - mentsu) - effective_taatsu - (1 if jantai else 0)
    if s < best[0]:
        best[0] = s
    if best[0] <= -1:
        return

    # Skip to next non-zero tile
    while idx < _NUM_TILE_TYPES and counts[idx] == 0:
        idx += 1
    if idx >= _NUM_TILE_TYPES:
        return

    # Upper-bound pruning: even if all remaining tiles form perfect sets/partials,
    # can we beat the current best?
    remaining = sum(counts[idx:])
    max_new_mentsu = remaining // 3
    max_new_taatsu = (remaining - max_new_mentsu * 3) // 2
    theoretical_best = (
        2 * (sets_needed - mentsu - max_new_mentsu)
        - min(taatsu + max_new_taatsu, sets_needed - mentsu - max_new_mentsu)
        - 1  # assume we find jantai
    )
    if theoretical_best >= best[0]:
        return

    # --- Try complete sets ---

    # Triplet
    if counts[idx] >= 3:
        counts[idx] -= 3
        _search(counts, idx, sets_needed, mentsu + 1, taatsu, jantai, best)
        counts[idx] += 3

    # Sequence (only for number tiles: idx 0-26, and value <= 7 within suit)
    if idx < 27 and (idx % 9) <= 6:
        if counts[idx] >= 1 and counts[idx + 1] >= 1 and counts[idx + 2] >= 1:
            counts[idx] -= 1
            counts[idx + 1] -= 1
            counts[idx + 2] -= 1
            _search(counts, idx, sets_needed, mentsu + 1, taatsu, jantai, best)
            counts[idx] += 1
            counts[idx + 1] += 1
            counts[idx + 2] += 1

    # --- Try pair as jantou ---
    if not jantai and counts[idx] >= 2:
        counts[idx] -= 2
        _search(counts, idx, sets_needed, mentsu, taatsu, True, best)
        counts[idx] += 2

    # --- Try partial sets (taatsu) ---
    if taatsu < (sets_needed - mentsu):
        # Pair as taatsu (when jantou already found)
        if jantai and counts[idx] >= 2:
            counts[idx] -= 2
            _search(counts, idx, sets_needed, mentsu, taatsu + 1, jantai, best)
            counts[idx] += 2

        # Adjacent sequence partial (number tiles only)
        if idx < 27 and (idx % 9) <= 7:
            if counts[idx] >= 1 and counts[idx + 1] >= 1:
                counts[idx] -= 1
                counts[idx + 1] -= 1
                _search(counts, idx, sets_needed, mentsu, taatsu + 1, jantai, best)
                counts[idx] += 1
                counts[idx + 1] += 1

        # Skip-one sequence partial (number tiles only)
        if idx < 27 and (idx % 9) <= 6:
            if counts[idx] >= 1 and counts[idx + 2] >= 1:
                counts[idx] -= 1
                counts[idx + 2] -= 1
                _search(counts, idx, sets_needed, mentsu, taatsu + 1, jantai, best)
                counts[idx] += 1
                counts[idx + 2] += 1

    # Skip this tile entirely (move to next tile type)
    saved = counts[idx]
    counts[idx] = 0
    _search(counts, idx + 1, sets_needed, mentsu, taatsu, jantai, best)
    counts[idx] = saved


def tenpai_tiles(hand: list[str], melds: list[Meld]) -> list[str]:
    """Return list of tiles that would complete this hand (shanten goes to -1).

    Only meaningful when the hand is already tenpai (shanten == 0).
    Returns an empty list if the hand is not tenpai.
    """
    if shanten_number(hand, melds) != 0:
        return []

    # Build candidate set: all non-flower tile types
    all_tile_types = sorted(set(build_full_deck()) - set(FLOWERS))

    winners: list[str] = []
    for t in all_tile_types:
        candidate = sorted(hand + [t])
        if is_standard_win(candidate, melds):
            winners.append(t)
    return winners
