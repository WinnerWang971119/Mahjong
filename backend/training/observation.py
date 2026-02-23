"""Encode GameState into flat observation vector from one player's perspective."""
from __future__ import annotations

import numpy as np

from engine.game_session import Action
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

        # Opponent visible melds (3 x 34) — exclude concealed kongs (hidden info)
        for opp_idx in opp_indices:
            opp = gs.players[opp_idx]
            visible = [m for m in opp.melds if m.from_player is not None]
            obs[offset : offset + 34] = _count_tiles(_meld_tiles(visible))
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
        # 128 drawable (144 total - 16 back wall) - 65 dealt (64 to players + 1 dealer extra)
        initial_wall = 63
        wall_count = len(gs.wall)
        obs[offset] = wall_count / max(initial_wall, 1)
        offset += 1

        # Tiles remaining in back wall (1)
        obs[offset] = len(gs.wall_back) / max(16, 1)
        offset += 1

        assert offset == self.obs_size
        return obs


# ---------------------------------------------------------------
# Action Encoder
# ---------------------------------------------------------------


def _build_chi_combos() -> list[tuple[str, str, str]]:
    """Build all 21 unique chi combinations (7 starting values x 3 suits)."""
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
    """Encode discrete actions as integers and provide legal-action masking.

    Action space layout (128 total):
        [0:34]     discard tile_i
        [34:55]    chi combo_j  (21 unique sorted triples: 7 start x 3 suits)
        [55]       pong
        [56]       open_kong
        [57:91]    added_kong tile_i  (which pong to extend)
        [91:125]   concealed_kong tile_i  (which tile to kong)
        [125]      win
        [126]      pass
        [127]      draw
    """

    DISCARD_OFFSET: int = 0          # 34 actions
    CHI_OFFSET: int = 34             # 21 actions
    PONG_OFFSET: int = 55            #  1 action
    OPEN_KONG_OFFSET: int = 56       #  1 action
    ADDED_KONG_OFFSET: int = 57      # 34 actions
    CONCEALED_KONG_OFFSET: int = 91  # 34 actions
    WIN_OFFSET: int = 125            #  1 action
    PASS_OFFSET: int = 126           #  1 action
    DRAW_OFFSET: int = 127           #  1 action

    action_size: int = 128

    def action_to_int(self, action: Action) -> int:
        """Convert an Action dataclass to an integer index."""
        if action.type == "discard":
            assert action.tile is not None
            return self.DISCARD_OFFSET + tile_to_index(action.tile)
        elif action.type == "chi":
            assert action.combo is not None
            key = tuple(sorted(action.combo))
            return self.CHI_OFFSET + _CHI_COMBO_TO_IDX[key]
        elif action.type == "pong":
            return self.PONG_OFFSET
        elif action.type == "open_kong":
            return self.OPEN_KONG_OFFSET
        elif action.type == "added_kong":
            assert action.tile is not None
            return self.ADDED_KONG_OFFSET + tile_to_index(action.tile)
        elif action.type == "concealed_kong":
            assert action.tile is not None
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
        """Convert an integer index back to an Action dataclass."""
        if idx < 0 or idx >= self.action_size:
            raise ValueError(f"Action index {idx} out of range [0, {self.action_size})")

        if idx < self.CHI_OFFSET:
            # Discard: [0, 34)
            tile = TILE_TYPES[idx - self.DISCARD_OFFSET]
            return Action(type="discard", tile=tile, player_idx=player_idx)
        elif idx < self.PONG_OFFSET:
            # Chi: [34, 55)
            combo = _CHI_COMBOS[idx - self.CHI_OFFSET]
            return Action(type="chi", combo=list(combo), player_idx=player_idx)
        elif idx == self.PONG_OFFSET:
            return Action(type="pong", player_idx=player_idx)
        elif idx == self.OPEN_KONG_OFFSET:
            return Action(type="open_kong", player_idx=player_idx)
        elif idx < self.CONCEALED_KONG_OFFSET:
            # Added kong: [57, 91)
            tile = TILE_TYPES[idx - self.ADDED_KONG_OFFSET]
            return Action(type="added_kong", tile=tile, player_idx=player_idx)
        elif idx < self.WIN_OFFSET:
            # Concealed kong: [91, 125)
            tile = TILE_TYPES[idx - self.CONCEALED_KONG_OFFSET]
            return Action(type="concealed_kong", tile=tile, player_idx=player_idx)
        elif idx == self.WIN_OFFSET:
            return Action(type="win", player_idx=player_idx)
        elif idx == self.PASS_OFFSET:
            return Action(type="pass", player_idx=player_idx)
        elif idx == self.DRAW_OFFSET:
            return Action(type="draw", player_idx=player_idx)
        else:
            raise ValueError(f"Action index {idx} out of range [0, {self.action_size})")

    def legal_actions_to_mask(self, legal_actions: list[Action]) -> np.ndarray:
        """Create a binary float32 mask from a list of legal actions.

        Returns an array of shape (action_size,) where mask[i] = 1.0
        if the action corresponding to index i is legal, 0.0 otherwise.
        """
        mask = np.zeros(self.action_size, dtype=np.float32)
        for action in legal_actions:
            mask[self.action_to_int(action)] = 1.0
        return mask
