"""Greedy rule-based AI baseline for Taiwan 16-tile Mahjong."""
from __future__ import annotations

import copy

from engine.state import GameState, Meld
from engine.game_session import Action
from engine.tiles import is_honor_tile, is_number_tile, tile_value
from ai.shanten import shanten_number


class RuleBasedAI:
    """
    Greedy AI: minimize shanten number at every decision.
    Always wins when legal. No bluffing or danger assessment.
    """

    def choose_action(
        self,
        gs: GameState,
        player_idx: int,
        legal_actions: list[Action],
    ) -> Action:
        if not legal_actions:
            raise ValueError("No legal actions available")

        # Priority 1: Win always
        for a in legal_actions:
            if a.type == "win":
                return a

        # Priority 2: On discard -- pick tile that minimizes shanten
        discard_actions = [a for a in legal_actions if a.type == "discard"]
        if discard_actions:
            return self._best_discard(gs, player_idx, discard_actions)

        # Priority 3: Kong (concealed or added) -- usually beneficial
        for a in legal_actions:
            if a.type in ("concealed_kong", "added_kong", "open_kong"):
                return a

        # Priority 4: Accept pong/chi if it reduces shanten
        player = gs.players[player_idx]
        current_shanten = shanten_number(player.hand, player.melds)
        for a in legal_actions:
            if a.type in ("pong", "chi"):
                # Simulate: would this reduce shanten?
                simulated_hand = player.hand.copy()
                valid_simulation = True
                if a.type == "pong" and a.tile:
                    # Must have at least 2 copies to pong
                    if simulated_hand.count(a.tile) >= 2:
                        simulated_hand.remove(a.tile)
                        simulated_hand.remove(a.tile)
                    else:
                        valid_simulation = False
                elif a.type == "chi" and a.combo:
                    for t in a.combo:
                        if t != a.tile:
                            if t in simulated_hand:
                                simulated_hand.remove(t)
                            else:
                                valid_simulation = False
                                break
                if not valid_simulation:
                    continue
                new_melds = copy.deepcopy(player.melds)
                if a.type == "pong" and a.tile:
                    new_melds.append(
                        Meld(type="pong", tiles=[a.tile] * 3, from_player=None)
                    )
                elif a.type == "chi" and a.combo:
                    new_melds.append(
                        Meld(type="chi", tiles=list(a.combo), from_player=None)
                    )
                new_shanten = shanten_number(simulated_hand, new_melds)
                if new_shanten < current_shanten:
                    return a

        # Priority 5: Draw (mandatory if available)
        for a in legal_actions:
            if a.type == "draw":
                return a

        # Priority 6: Pass (decline optional action)
        for a in legal_actions:
            if a.type == "pass":
                return a

        # Fallback
        return legal_actions[0]

    def _best_discard(
        self,
        gs: GameState,
        player_idx: int,
        discard_actions: list[Action],
    ) -> Action:
        """Return the discard action that minimizes shanten number."""
        player = gs.players[player_idx]
        best_shanten = float("inf")
        best_action = discard_actions[0]
        best_priority = 0

        for a in discard_actions:
            if a.tile is None:
                continue
            simulated = player.hand.copy()
            if a.tile in simulated:
                simulated.remove(a.tile)
            s = shanten_number(simulated, player.melds)

            # Tiebreaker: prefer discarding isolated honors > terminals > others
            priority = 0
            if is_honor_tile(a.tile):
                priority = 2
            elif is_number_tile(a.tile) and tile_value(a.tile) in (1, 9):
                priority = 1

            if s < best_shanten or (s == best_shanten and priority > best_priority):
                best_shanten = s
                best_action = a
                best_priority = priority

        return best_action
