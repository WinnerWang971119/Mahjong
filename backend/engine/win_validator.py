"""Win detection for Taiwan 16-tile Mahjong."""
from __future__ import annotations

from typing import Optional

from engine.state import Meld
from engine.tiles import is_number_tile, tile_suit, tile_value, FLOWERS


# ---------------------------------------------------------------------------
# Tile sort key — groups number tiles by suit/value, then honors alphabetically
# ---------------------------------------------------------------------------

_SUIT_ORDER = {"m": 0, "p": 1, "s": 2}
_HONOR_ORDER = {"E": 30, "S": 31, "W": 32, "N": 33, "C": 34, "F": 35, "B": 36}


def _tile_sort_key(tile: str) -> int:
    """Return an integer sort key so tiles group by suit then value."""
    if is_number_tile(tile):
        return _SUIT_ORDER[tile[1]] * 10 + int(tile[0])
    return _HONOR_ORDER.get(tile, 99)


# ---------------------------------------------------------------------------
# Standard hand decomposition (backtracking)
# ---------------------------------------------------------------------------

def decompose_hand(
    hand: list[str],
    melds: list[Meld],
) -> Optional[tuple[list[list[str]], list[str]]]:
    """Try to decompose *hand* into (sets, pair).

    Total sets needed = 5 - len(melds).
    Each set is a sequence [a, b, c] or a triplet [a, a, a].
    The pair is [a, a].

    Returns ``(sets, pair)`` on success, ``None`` if no valid decomposition.
    """
    sets_needed = 5 - len(melds)
    sorted_hand = sorted(hand, key=_tile_sort_key)
    return _find_decomposition(sorted_hand, sets_needed, [])


def _find_decomposition(
    tiles: list[str],
    sets_needed: int,
    found_sets: list[list[str]],
) -> Optional[tuple[list[list[str]], list[str]]]:
    """Recursive backtracking: try pair extraction at every candidate tile."""
    if sets_needed == 0:
        # Only the pair should remain
        if len(tiles) == 2 and tiles[0] == tiles[1]:
            return (found_sets, list(tiles))
        return None

    # Quick length check
    expected = sets_needed * 3 + 2
    if len(tiles) != expected:
        return None

    # Try extracting each possible pair first, then decompose the rest
    seen_pairs: set[str] = set()
    for i, tile in enumerate(tiles):
        if tile in seen_pairs:
            continue
        if i + 1 < len(tiles) and tiles[i + 1] == tile:
            seen_pairs.add(tile)
            remaining = tiles[:i] + tiles[i + 2:]
            result = _decompose_sets(remaining, sets_needed, [])
            if result is not None:
                return (result, [tile, tile])

    return None


def _decompose_sets(
    tiles: list[str],
    sets_needed: int,
    found_sets: list[list[str]],
) -> Optional[list[list[str]]]:
    """Decompose *tiles* into exactly *sets_needed* sets (triplet or sequence).

    Tiles must be sorted by ``_tile_sort_key``. Always consumes the first tile
    to avoid redundant branches.
    """
    if sets_needed == 0:
        return found_sets if len(tiles) == 0 else None

    if not tiles:
        return None

    first = tiles[0]

    # Try triplet with the first tile
    if tiles.count(first) >= 3:
        remaining = list(tiles)
        for _ in range(3):
            remaining.remove(first)
        result = _decompose_sets(remaining, sets_needed - 1, found_sets + [[first] * 3])
        if result is not None:
            return result

    # Try sequence with the first tile (number tiles only)
    if is_number_tile(first):
        suit = tile_suit(first)
        val = tile_value(first)
        if val <= 7:
            t2 = f"{val + 1}{suit}"
            t3 = f"{val + 2}{suit}"
            if t2 in tiles and t3 in tiles:
                remaining = list(tiles)
                remaining.remove(first)
                remaining.remove(t2)
                remaining.remove(t3)
                result = _decompose_sets(
                    remaining, sets_needed - 1, found_sets + [[first, t2, t3]],
                )
                if result is not None:
                    return result

    return None


def is_standard_win(hand: list[str], melds: list[Meld]) -> bool:
    """Return ``True`` if *hand* + *melds* form a valid standard winning hand.

    A standard win consists of 5 sets (sequences or triplets) plus 1 pair.
    """
    return decompose_hand(hand, melds) is not None


# ---------------------------------------------------------------------------
# Flower-based win conditions
# ---------------------------------------------------------------------------

_ALL_FLOWERS = frozenset(FLOWERS)


def is_bajian_guohai(flowers: list[str]) -> bool:
    """八仙過海: player holds all 8 flower tiles."""
    return len(flowers) == 8 and set(flowers) == _ALL_FLOWERS


def is_qiqiang_yi(flowers: list[str], incoming_tile: str) -> bool:
    """七搶一: player holds 7 flowers and claims the 8th flower tile."""
    if incoming_tile not in _ALL_FLOWERS:
        return False
    if len(flowers) != 7:
        return False
    return set(flowers) | {incoming_tile} == _ALL_FLOWERS


# ---------------------------------------------------------------------------
# Combined win check
# ---------------------------------------------------------------------------

def is_winning_hand(
    hand: list[str],
    melds: list[Meld],
    flowers: list[str],
    win_tile: str,
    is_flower_steal: bool = False,
) -> Optional[str]:
    """Check all win conditions.

    Returns a win-type string (``"standard"``, ``"bajian_guohai"``,
    ``"qiqiang_yi"``) or ``None`` if the hand is not a winner.
    """
    if is_flower_steal:
        if is_qiqiang_yi(flowers, win_tile):
            return "qiqiang_yi"
        return None

    # Check 八仙過海 — if the win tile is itself a flower, include it
    flower_set = list(flowers)
    if win_tile in _ALL_FLOWERS:
        flower_set.append(win_tile)
    if is_bajian_guohai(flower_set):
        return "bajian_guohai"

    # Standard win: add win_tile to hand and decompose
    full_hand = sorted(hand + [win_tile], key=_tile_sort_key)
    if is_standard_win(full_hand, melds):
        return "standard"

    return None
