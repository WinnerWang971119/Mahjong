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
    """Encodes game state into flat float32 vector.

    Feature layout:
        [0:34]     own hand tile counts / 4
        [34:42]    own flowers (binary)
        [42:76]    opponent 1 discards / 4
        [76:110]   opponent 2 discards / 4
        [110:144]  opponent 3 discards / 4
        [144:178]  opponent 1 visible melds / 4
        [178:212]  opponent 2 visible melds / 4
        [212:246]  opponent 3 visible melds / 4
        [246:280]  own melds / 4
        [280:284]  seat wind one-hot
        [284:288]  prevailing wind one-hot
        [288]      tiles remaining in wall (normalized)
        [289]      tiles remaining in back wall (normalized)
    """

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

        # Opponents relative to player (3 x discards + 3 x melds)
        opp_indices = [(player_idx + i) % 4 for i in range(1, 4)]

        # Opponent discards (3 x 34)
        for opp_idx in opp_indices:
            opp = gs.players[opp_idx]
            obs[offset : offset + 34] = _count_tiles(opp.discards)
            offset += 34

        # Opponent visible melds (3 x 34)
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

        # Tiles remaining in wall (1) -- normalized by initial wall size
        initial_wall = 144 - 8 - 16 * 4  # 144 total - 8 flowers - 64 dealt
        wall_count = len(gs.wall)
        obs[offset] = wall_count / max(initial_wall, 1)
        offset += 1

        # Tiles remaining in back wall (1)
        obs[offset] = len(gs.wall_back) / max(16, 1)
        offset += 1

        assert offset == self.obs_size
        return obs
