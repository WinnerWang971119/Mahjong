"""Deal logic: initial hand distribution and flower replacement."""
from __future__ import annotations

from engine.state import GameState
from engine.tiles import FLOWERS
from engine.wall import draw_from_wall, draw_from_back


def deal_initial_hands(gs: GameState) -> None:
    """
    Deal tiles to all 4 players in-place.
    4 rounds of 4 tiles each (counter-clockwise from dealer).
    Dealer receives one extra tile at the end -> 17 tiles.
    Non-dealers get 16 tiles.
    Modifies gs.wall and gs.players[*].hand.
    """
    dealer = gs.dealer_index
    players_in_order = [(dealer + i) % 4 for i in range(4)]

    # 4 rounds, each round deals 4 tiles to each player
    for _ in range(4):
        for p_idx in players_in_order:
            for _ in range(4):
                tile = draw_from_wall(gs.wall)
                gs.players[p_idx].hand.append(tile)

    # Dealer's extra tile
    gs.players[dealer].hand.append(draw_from_wall(gs.wall))


def flower_replacement(gs: GameState) -> None:
    """
    Process flower replacement in dealer-first, counter-clockwise order.
    Any flower in hand goes to player's flower area; replacement drawn from back wall.
    Recurse if replacement tile is also a flower.
    Sets gs.phase = "play" when done.
    """
    dealer = gs.dealer_index
    order = [(dealer + i) % 4 for i in range(4)]
    for p_idx in order:
        _replace_flowers_for_player(gs, p_idx)
    gs.phase = "play"


def _replace_flowers_for_player(gs: GameState, p_idx: int) -> None:
    """Replace all flowers in this player's hand, repeating if replacements are also flowers."""
    player = gs.players[p_idx]
    while True:
        flower_indices = [i for i, t in enumerate(player.hand) if t in FLOWERS]
        if not flower_indices:
            break
        # Move all current flowers to flower area (pop in reverse to preserve indices)
        for i in sorted(flower_indices, reverse=True):
            flower = player.hand.pop(i)
            player.flowers.append(flower)
        # Draw replacements from back wall
        for _ in flower_indices:
            replacement = draw_from_back(gs.wall_back)
            player.hand.append(replacement)
        # Loop continues to check if any replacements are also flowers


def check_peipai_flower_hu(gs: GameState, p_idx: int) -> bool:
    """Return True if player was dealt all 8 flower tiles (special win)."""
    return len(gs.players[p_idx].flowers) == 8
