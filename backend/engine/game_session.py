"""Game session state machine for Taiwan 16-tile Mahjong.

Manages a full hand: deal, flower replacement, play phase (draw/discard/claim cycle),
and terminal conditions (win or draw).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal, Optional

from engine.state import GameState, Meld, PlayerState
from engine.tiles import (
    build_full_deck,
    build_flower_set,
    is_flower_tile,
    is_number_tile,
    tile_suit,
    tile_value,
)
from engine.wall import shuffle_and_build_wall, draw_from_wall, draw_from_back
from engine.deal import deal_initial_hands, flower_replacement
from engine.actions import (
    get_chi_combinations,
    validate_chi,
    validate_pong,
    validate_open_kong,
    validate_added_kong,
    validate_concealed_kong,
)
from engine.win_validator import is_winning_hand, decompose_hand

ActionType = Literal[
    "draw", "discard", "chi", "pong", "open_kong",
    "added_kong", "concealed_kong", "win", "pass",
]


@dataclass
class Action:
    """Represents a player action in the game."""

    type: ActionType
    tile: Optional[str] = None
    combo: Optional[list[str]] = None
    player_idx: Optional[int] = None  # Which player performs this action


# Internal sub-phases within "play"
_SubPhase = Literal["active_turn", "claim"]


class GameSession:
    """State machine managing a full Taiwan Mahjong hand.

    Lifecycle:
        1. ``__init__()`` creates a new game state in "deal" phase.
        2. ``start_hand()`` shuffles, deals, replaces flowers -> "play" phase.
        3. Repeatedly call ``get_legal_actions()`` and ``step()`` until
           ``state.phase`` is "win" or "draw".
    """

    def __init__(self) -> None:
        self.state: GameState = GameState.new_game()
        # Internal tracking
        self._sub_phase: _SubPhase = "active_turn"
        self._pending_discard: Optional[str] = None
        self._pending_discarder: Optional[int] = None
        self._just_drew: bool = False  # True if current player just drew a tile
        self._after_kong: bool = False  # True if current player just drew after kong
        self._passed_players: set[int] = set()  # Players who passed during claim phase

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_hand(self) -> None:
        """Shuffle deck, deal tiles, replace flowers, set phase to play."""
        deck = build_full_deck() + build_flower_set()
        wall, back = shuffle_and_build_wall(deck)
        self.state.wall = wall
        self.state.wall_back = back
        self.state.phase = "deal"

        deal_initial_hands(self.state)
        self.state.phase = "flower_replacement"
        flower_replacement(self.state)
        # After flower_replacement, phase is "play"

        # Dealer starts: they already have 17 tiles, must discard
        self.state.current_player = self.state.dealer_index
        self._sub_phase = "active_turn"
        self._just_drew = True  # Dealer's 17th tile acts like a draw

    def get_legal_actions(self, player_idx: int) -> list[Action]:
        """Return all legal actions for the given player in the current state."""
        if self.state.phase != "play":
            return []

        gs = self.state
        player = gs.players[player_idx]

        # ----- CLAIM phase: after someone discarded -----
        if self._sub_phase == "claim" and self._pending_discard is not None:
            if player_idx == self._pending_discarder:
                return []  # Discarder cannot claim their own tile
            return self._get_claim_actions(player_idx)

        # ----- ACTIVE TURN phase -----
        if player_idx != gs.current_player:
            return []

        hand_size = len(player.hand)

        # Player needs to draw (16 tiles in hand, no pending draw)
        if hand_size <= 16 and not self._just_drew:
            return [Action(type="draw")]

        # Player has drawn (or is dealer with 17 tiles) -> can discard or declare
        actions: list[Action] = []

        # Win check (self-draw / tsumo)
        if self._just_drew:
            for tile in set(player.hand):
                test_hand = list(player.hand)
                test_hand.remove(tile)
                result = is_winning_hand(test_hand, player.melds, player.flowers, tile)
                if result is not None:
                    actions.append(Action(type="win", tile=tile))
                    break  # One win action is enough

        # Concealed kong: 4 identical tiles in hand
        for tile in set(player.hand):
            if validate_concealed_kong(player.hand, tile):
                actions.append(Action(type="concealed_kong", tile=tile))

        # Added kong: extend an existing pong with a tile from hand
        for tile in set(player.hand):
            if validate_added_kong(player.melds, tile):
                actions.append(Action(type="added_kong", tile=tile))

        # Discard: can discard any tile in hand
        for tile in set(player.hand):
            actions.append(Action(type="discard", tile=tile))

        return actions

    def step(self, action: Action) -> None:
        """Execute an action and advance the game state."""
        if self.state.phase != "play":
            return

        gs = self.state

        if action.type == "draw":
            self._do_draw(gs)
        elif action.type == "discard":
            self._do_discard(gs, action)
        elif action.type == "chi":
            self._do_chi(gs, action)
        elif action.type == "pong":
            self._do_pong(gs, action)
        elif action.type == "open_kong":
            self._do_open_kong(gs, action)
        elif action.type == "added_kong":
            self._do_added_kong(gs, action)
        elif action.type == "concealed_kong":
            self._do_concealed_kong(gs, action)
        elif action.type == "win":
            self._do_win(gs, action)
        elif action.type == "pass":
            # Determine which player is passing
            passer = action.player_idx
            if passer is None:
                # Fallback: find a non-discarder who hasn't passed yet
                for i in range(4):
                    if i != self._pending_discarder and i not in self._passed_players:
                        passer = i
                        break
            if passer is not None:
                self._do_pass(gs, passer)

    # ------------------------------------------------------------------
    # Claim actions (after a discard)
    # ------------------------------------------------------------------

    def _get_claim_actions(self, player_idx: int) -> list[Action]:
        """Return legal claim actions for a player after someone discards."""
        gs = self.state
        player = gs.players[player_idx]
        discard = self._pending_discard
        assert discard is not None
        discarder = self._pending_discarder
        assert discarder is not None

        if player_idx in self._passed_players:
            return []

        actions: list[Action] = []

        # Win on discard
        result = is_winning_hand(player.hand, player.melds, player.flowers, discard)
        if result is not None:
            actions.append(Action(type="win", tile=discard))

        # Open kong (3 in hand + discarded tile)
        if validate_open_kong(player.hand, discard):
            actions.append(Action(type="open_kong", tile=discard))

        # Pong (2 in hand + discarded tile)
        if validate_pong(player.hand, discard):
            actions.append(Action(type="pong", tile=discard))

        # Chi: only the next player in turn order can chi
        next_player = (discarder + 1) % 4
        if player_idx == next_player and validate_chi(player.hand, discard):
            combos = get_chi_combinations(player.hand, discard)
            for combo in combos:
                actions.append(Action(type="chi", tile=discard, combo=combo))

        # Always can pass
        actions.append(Action(type="pass", player_idx=player_idx))

        # Tag all actions with the player index
        for a in actions:
            a.player_idx = player_idx

        return actions

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _do_draw(self, gs: GameState) -> None:
        """Draw a tile from the wall for the current player."""
        if not gs.wall:
            gs.phase = "draw"  # Exhaustive draw
            return

        player = gs.players[gs.current_player]
        tile = draw_from_wall(gs.wall)

        # Handle flower drawn during play
        if is_flower_tile(tile):
            player.flowers.append(tile)
            self._draw_replacement(gs, player)
            return

        player.hand.append(tile)
        self._just_drew = True
        self._after_kong = False
        self._sub_phase = "active_turn"
        gs.last_action = "draw"

    def _draw_replacement(self, gs: GameState, player: PlayerState) -> None:
        """Draw a replacement tile from the back wall (after flower or kong).

        Recursively handles the case where the replacement is also a flower.
        """
        if not gs.wall_back:
            # No replacement tiles left -- check main wall
            if not gs.wall:
                gs.phase = "draw"
                return
            # Fall back to main wall if back is empty
            tile = draw_from_wall(gs.wall)
        else:
            tile = draw_from_back(gs.wall_back)

        if is_flower_tile(tile):
            player.flowers.append(tile)
            self._draw_replacement(gs, player)
            return

        player.hand.append(tile)
        self._just_drew = True
        self._after_kong = True
        self._sub_phase = "active_turn"
        gs.last_action = "replacement_draw"

    def _do_discard(self, gs: GameState, action: Action) -> None:
        """Current player discards a tile."""
        assert action.tile is not None
        player = gs.players[gs.current_player]
        tile = action.tile

        player.hand.remove(tile)
        player.discards.append(tile)
        gs.discard_pool.append(tile)
        gs.last_discard = tile
        gs.last_action = "discard"

        self._pending_discard = tile
        self._pending_discarder = gs.current_player
        self._just_drew = False
        self._after_kong = False
        self._sub_phase = "claim"

    def _do_chi(self, gs: GameState, action: Action) -> None:
        """Claiming player performs chi on the pending discard."""
        assert action.tile is not None
        assert action.combo is not None
        discard = action.tile
        combo = action.combo
        discarder = self._pending_discarder
        assert discarder is not None

        # Determine claiming player: next after discarder
        claimer_idx = (discarder + 1) % 4
        claimer = gs.players[claimer_idx]

        # Remove the two non-discard tiles from hand
        for t in combo:
            if t != discard:
                claimer.hand.remove(t)

        # Remove the discard from the pool (it was added during discard step)
        # Actually the tile stays in discard_pool as record; we just consume it
        meld = Meld(type="chi", tiles=list(combo), from_player=discarder)
        claimer.melds.append(meld)

        gs.current_player = claimer_idx
        gs.last_action = "chi"
        self._pending_discard = None
        self._pending_discarder = None
        self._passed_players.clear()
        self._just_drew = True  # Player now has 17-equivalent (needs to discard)
        self._sub_phase = "active_turn"

    def _do_pong(self, gs: GameState, action: Action) -> None:
        """Claiming player performs pong on the pending discard."""
        discard = self._pending_discard
        assert discard is not None
        discarder = self._pending_discarder
        assert discarder is not None

        # Find the claiming player (any non-discarder who has 2+ copies)
        claimer_idx = self._find_claimer(gs, discard, min_count=2)
        claimer = gs.players[claimer_idx]

        # Remove 2 tiles from hand
        for _ in range(2):
            claimer.hand.remove(discard)

        meld = Meld(type="pong", tiles=[discard, discard, discard], from_player=discarder)
        claimer.melds.append(meld)

        gs.current_player = claimer_idx
        gs.last_action = "pong"
        self._pending_discard = None
        self._pending_discarder = None
        self._passed_players.clear()
        self._just_drew = True  # Has extra tile, needs to discard
        self._sub_phase = "active_turn"

    def _do_open_kong(self, gs: GameState, action: Action) -> None:
        """Claiming player performs open kong on the pending discard."""
        discard = self._pending_discard
        discarder = self._pending_discarder

        if discard is not None and discarder is not None and self._sub_phase == "claim":
            # Open kong from discard
            claimer_idx = self._find_claimer(gs, discard, min_count=3)
            claimer = gs.players[claimer_idx]

            for _ in range(3):
                claimer.hand.remove(discard)

            meld = Meld(
                type="open_kong",
                tiles=[discard, discard, discard, discard],
                from_player=discarder,
            )
            claimer.melds.append(meld)

            gs.current_player = claimer_idx
            gs.last_action = "open_kong"
            self._pending_discard = None
            self._pending_discarder = None
            self._passed_players.clear()
            self._just_drew = False
            self._sub_phase = "active_turn"

            # Draw replacement from back wall
            self._draw_replacement(gs, claimer)

    def _do_added_kong(self, gs: GameState, action: Action) -> None:
        """Current player adds a tile from hand to an existing pong meld."""
        assert action.tile is not None
        tile = action.tile
        player = gs.players[gs.current_player]

        # Find the matching pong meld and upgrade it
        for meld in player.melds:
            if meld.type == "pong" and tile in meld.tiles:
                meld.type = "added_kong"
                meld.tiles.append(tile)
                player.hand.remove(tile)
                break

        gs.last_action = "added_kong"
        self._just_drew = False
        self._sub_phase = "active_turn"

        # Draw replacement
        self._draw_replacement(gs, player)

    def _do_concealed_kong(self, gs: GameState, action: Action) -> None:
        """Current player declares a concealed kong (4 identical tiles from hand)."""
        assert action.tile is not None
        tile = action.tile
        player = gs.players[gs.current_player]

        for _ in range(4):
            player.hand.remove(tile)

        meld = Meld(
            type="concealed_kong",
            tiles=[tile, tile, tile, tile],
            from_player=None,
        )
        player.melds.append(meld)

        gs.last_action = "concealed_kong"
        self._just_drew = False
        self._sub_phase = "active_turn"

        # Draw replacement
        self._draw_replacement(gs, player)

    def _do_win(self, gs: GameState, action: Action) -> None:
        """Player declares a win."""
        gs.phase = "win"
        gs.last_action = "win"

    def _do_pass(self, gs: GameState, player_idx: int) -> None:
        """Player passes on claiming the discard.

        Only advances to next player's draw when all 3 non-discarders have passed.
        """
        assert self._pending_discarder is not None
        self._passed_players.add(player_idx)

        # Check if all non-discarders have passed
        non_discarders = {i for i in range(4) if i != self._pending_discarder}
        if self._passed_players >= non_discarders:
            next_player = (self._pending_discarder + 1) % 4
            self._pending_discard = None
            self._pending_discarder = None
            self._passed_players.clear()
            self._sub_phase = "active_turn"
            self._just_drew = False
            gs.current_player = next_player
            gs.last_action = "pass"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_claimer(self, gs: GameState, discard: str, min_count: int) -> int:
        """Find the first non-discarder with enough copies of the tile.

        Searches in priority order starting from the player after the discarder.
        """
        discarder = self._pending_discarder
        assert discarder is not None
        for offset in range(1, 4):
            idx = (discarder + offset) % 4
            if Counter(gs.players[idx].hand)[discard] >= min_count:
                return idx
        raise RuntimeError(f"No player found with {min_count}+ copies of {discard}")
