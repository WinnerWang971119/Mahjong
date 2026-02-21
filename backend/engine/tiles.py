"""Tile definitions and helpers for Taiwan 16-tile Mahjong."""
from __future__ import annotations

# Suit codes
SUITS = ("m", "p", "s")  # 萬, 筒, 索

# Honor tile codes
WINDS = ("E", "S", "W", "N")       # 東南西北
DRAGONS = ("C", "F", "B")          # 中發白
HONORS = WINDS + DRAGONS

# Flower tile codes: f1-f4 = 春夏秋冬 (seasons), f5-f8 = 梅蘭菊竹 (plants)
FLOWERS = tuple(f"f{i}" for i in range(1, 9))

# Season flowers (f1-f4) correspond to seats E/S/W/N
SEASON_FLOWERS = ("f1", "f2", "f3", "f4")
# Plant flowers (f5-f8) correspond to seats E/S/W/N
PLANT_FLOWERS = ("f5", "f6", "f7", "f8")

# Player seat winds in order
SEAT_WINDS = WINDS  # index 0=E, 1=S, 2=W, 3=N


def build_full_deck() -> list[str]:
    """Return 136-tile deck (4 copies each of 34 unique tiles, no flowers)."""
    tiles: list[str] = []
    for suit in SUITS:
        for value in range(1, 10):
            tiles.extend([f"{value}{suit}"] * 4)
    for honor in HONORS:
        tiles.extend([honor] * 4)
    return tiles


def build_flower_set() -> list[str]:
    """Return the 8 unique flower tiles (1 copy each)."""
    return list(FLOWERS)


def is_number_tile(tile: str) -> bool:
    """True if tile is a number tile (萬/筒/索)."""
    return len(tile) == 2 and tile[1] in SUITS and tile[0].isdigit()


def is_honor_tile(tile: str) -> bool:
    """True if tile is a wind or dragon honor tile."""
    return tile in HONORS


def is_flower_tile(tile: str) -> bool:
    """True if tile is a flower tile (f1-f8)."""
    return tile in FLOWERS


def is_wind_tile(tile: str) -> bool:
    """True if tile is a wind tile (E/S/W/N)."""
    return tile in WINDS


def is_dragon_tile(tile: str) -> bool:
    """True if tile is a dragon tile (C/F/B)."""
    return tile in DRAGONS


def tile_suit(tile: str) -> str:
    """Return suit character ('m', 'p', 's'). Raises ValueError for non-number tiles."""
    if not is_number_tile(tile):
        raise ValueError(f"Tile '{tile}' has no suit (not a number tile)")
    return tile[1]


def tile_value(tile: str) -> int:
    """Return numeric value 1-9. Raises ValueError for non-number tiles."""
    if not is_number_tile(tile):
        raise ValueError(f"Tile '{tile}' has no value (not a number tile)")
    return int(tile[0])


def tile_wind_index(tile: str) -> int:
    """Return 0=E, 1=S, 2=W, 3=N. Raises ValueError if not a wind tile."""
    if tile not in WINDS:
        raise ValueError(f"Tile '{tile}' is not a wind tile")
    return WINDS.index(tile)


def own_seat_flowers(seat: int) -> tuple[str, str]:
    """Return the two flower tiles belonging to this seat (season + plant)."""
    return (SEASON_FLOWERS[seat], PLANT_FLOWERS[seat])
