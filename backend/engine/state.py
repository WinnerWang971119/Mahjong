"""Core data structures for Taiwan 16-tile Mahjong game state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


MeldType = Literal["chi", "pong", "open_kong", "added_kong", "concealed_kong"]
Phase = Literal["deal", "flower_replacement", "play", "win", "draw"]


@dataclass
class Meld:
    type: MeldType
    tiles: list[str]            # 3 or 4 tiles forming the meld
    from_player: Optional[int]  # index of player whose discard was used (None = concealed)


@dataclass
class PlayerState:
    seat: int                   # 0=East, 1=South, 2=West, 3=North
    hand: list[str] = field(default_factory=list)
    melds: list[Meld] = field(default_factory=list)
    flowers: list[str] = field(default_factory=list)
    discards: list[str] = field(default_factory=list)
    is_dealer: bool = False
    streak: int = 0             # consecutive dealer rounds


@dataclass
class GameState:
    players: list[PlayerState]
    wall: list[str]             # drawable wall (head = next draw)
    wall_back: list[str]        # 槓尾 replacement tiles (back wall)
    discard_pool: list[str]     # all discarded tiles (牌海)
    current_player: int
    round_wind: str             # "E" / "S" / "W" / "N"
    round_number: int           # rounds completed in current wind circle
    dealer_index: int
    last_discard: Optional[str]
    last_action: Optional[str]
    phase: Phase
    tenpai_flags: dict[int, bool]  # player_idx → tenpai after deal (for 天聽 detection)

    @classmethod
    def new_game(cls) -> "GameState":
        """Create a fresh game state ready for dealing."""
        players = [PlayerState(seat=i) for i in range(4)]
        players[0].is_dealer = True
        return cls(
            players=players,
            wall=[],
            wall_back=[],
            discard_pool=[],
            current_player=0,
            round_wind="E",
            round_number=0,
            dealer_index=0,
            last_discard=None,
            last_action=None,
            phase="deal",
            tenpai_flags={},
        )
