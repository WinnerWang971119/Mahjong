"""Shanten number calculator for Taiwan 16-tile Mahjong (from scratch).

Taiwan Mahjong uses 16 tiles in hand. A winning hand consists of
5 sets (sequences or triplets) plus 1 pair, totaling 17 tiles
(16 in hand + 1 drawn/claimed tile). With exposed melds, the hand
tiles are reduced accordingly.
"""
from __future__ import annotations

from collections import Counter

from engine.tiles import (
    FLOWERS,
    build_full_deck,
    is_number_tile,
    tile_suit,
    tile_value,
)
from engine.state import Meld
from engine.win_validator import is_standard_win


def shanten_number(hand: list[str], melds: list[Meld]) -> int:
    """Calculate shanten number for Taiwan 16-tile Mahjong.

    Returns:
      -1 = winning hand (tsumo / already complete)
       0 = tenpai (one tile away from win)
       n = n tiles needed to reach tenpai

    The hand should contain only the concealed tiles (not tiles locked
    in melds). For a player with no melds, the hand has 16 tiles when
    it is their turn (before discard) or 17 tiles if checking after draw.
    """
    sets_needed = 5 - len(melds)
    sorted_hand = sorted(hand)
    return _shanten(sorted_hand, sets_needed)


def _shanten(tiles: list[str], sets_needed: int) -> int:
    """Minimum shanten via exhaustive grouping.

    Uses the standard shanten formula from mahjong theory:

      shanten = 2 * (sets_needed - mentsu) - taatsu - jantai

    Where:
      - mentsu  = number of complete sets (triplets or sequences) found
      - taatsu  = number of partial sets (adjacent/skip pairs, NOT the jantou)
      - jantai  = 1 if a pair candidate (jantou / 將眼) has been found, else 0

    Constraints:
      - taatsu <= sets_needed - mentsu (partials can't exceed remaining sets)

    Result: -1 = complete, 0 = tenpai, n = n away from tenpai.
    """
    best = [2 * sets_needed]  # worst case

    def search(
        tiles: list[str],
        mentsu: int,
        taatsu: int,
        jantai: bool,
    ) -> None:
        # Cap taatsu at the number of remaining incomplete sets
        effective_taatsu = min(taatsu, sets_needed - mentsu)
        s = 2 * (sets_needed - mentsu) - effective_taatsu - (1 if jantai else 0)
        if s < best[0]:
            best[0] = s

        # Pruning: can't improve beyond -1
        if best[0] <= -1:
            return

        if not tiles:
            return

        t = tiles[0]
        counts = Counter(tiles)

        # --- Try complete sets from the first tile ---

        # Triplet
        if counts[t] >= 3:
            rem = tiles.copy()
            for _ in range(3):
                rem.remove(t)
            search(rem, mentsu + 1, taatsu, jantai)

        # Sequence (number tiles only, value <= 7)
        if is_number_tile(t):
            suit = tile_suit(t)
            val = tile_value(t)
            t2 = f"{val + 1}{suit}"
            t3 = f"{val + 2}{suit}"
            if val <= 7 and counts.get(t2, 0) >= 1 and counts.get(t3, 0) >= 1:
                rem = tiles.copy()
                rem.remove(t)
                rem.remove(t2)
                rem.remove(t3)
                search(rem, mentsu + 1, taatsu, jantai)

        # --- Try pair as jantou (only once) ---
        if not jantai and counts[t] >= 2:
            rem = tiles.copy()
            rem.remove(t)
            rem.remove(t)
            search(rem, mentsu, taatsu, True)

        # --- Try partial sets (taatsu) ---
        if taatsu < (sets_needed - mentsu):
            # Pair as taatsu (only if jantai already found)
            if jantai and counts[t] >= 2:
                rem = tiles.copy()
                rem.remove(t)
                rem.remove(t)
                search(rem, mentsu, taatsu + 1, jantai)

            # Adjacent or skip-one sequence partials (number tiles only)
            if is_number_tile(t):
                suit = tile_suit(t)
                val = tile_value(t)
                for dv in (1, 2):
                    nv = val + dv
                    if nv <= 9:
                        t2 = f"{nv}{suit}"
                        if counts.get(t2, 0) >= 1:
                            rem = tiles.copy()
                            rem.remove(t)
                            rem.remove(t2)
                            search(rem, mentsu, taatsu + 1, jantai)

        # Skip this tile entirely
        rem = tiles.copy()
        rem.remove(t)
        search(rem, mentsu, taatsu, jantai)

    search(tiles, 0, 0, False)
    return best[0]


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
