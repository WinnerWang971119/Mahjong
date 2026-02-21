"""Wall construction and shuffling for Taiwan 16-tile Mahjong."""
from __future__ import annotations
import random


# Last 16 tiles of wall reserved as 殘牌 (鐵八墩) — never drawn in normal play
RESERVED_COUNT = 16


def shuffle_and_build_wall(deck: list[str]) -> tuple[list[str], list[str]]:
    """
    Shuffle the full 144-tile deck and split into:
      - wall: the 128 drawable tiles (drawn from front/head)
      - back: the 16 reserved 槓尾 tiles (used for kong/flower replacement draws)

    Returns (wall, back). Does not modify the input deck.
    """
    shuffled = deck.copy()
    random.shuffle(shuffled)
    back = shuffled[-RESERVED_COUNT:]
    wall = shuffled[:-RESERVED_COUNT]
    return wall, back


def draw_from_wall(wall: list[str]) -> str:
    """Draw the next tile from the head of the wall. Raises IndexError if wall is empty."""
    return wall.pop(0)


def draw_from_back(back: list[str]) -> str:
    """Draw a replacement tile from 槓尾 (back of wall). Used after kong or flower."""
    if not back:
        raise IndexError("No tiles left in back wall (槓尾)")
    return back.pop(0)
