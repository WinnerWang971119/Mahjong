"""JSON serializer for game state with visibility filtering."""
from __future__ import annotations

from engine.state import GameState, Meld, PlayerState


def serialize_game_state(
    gs: GameState, viewer_idx: int, reveal_all: bool = False
) -> dict:
    """Serialize GameState to a JSON-safe dict.

    Hides opponents' hands unless *reveal_all* is True (inspect/replay mode).
    """
    return {
        "players": [
            serialize_player(
                p, is_self=(p.seat == viewer_idx), reveal=reveal_all
            )
            for p in gs.players
        ],
        "discard_pool": gs.discard_pool,
        "current_player": gs.current_player,
        "round_wind": gs.round_wind,
        "round_number": gs.round_number,
        "dealer_index": gs.dealer_index,
        "wall_remaining": len(gs.wall) + len(gs.wall_back),
        "last_discard": gs.last_discard,
        "phase": gs.phase,
    }


def serialize_player(
    player: PlayerState, is_self: bool = False, reveal: bool = False
) -> dict:
    """Serialize a single player's state.

    When *is_self* and *reveal* are both False the hand tiles are hidden and
    only the tile count is exposed.
    """
    show_hand = is_self or reveal
    return {
        "seat": player.seat,
        "hand": list(player.hand) if show_hand else None,
        "hand_count": len(player.hand),
        "melds": [serialize_meld(m) for m in player.melds],
        "flowers": list(player.flowers),
        "discards": list(player.discards),
        "is_dealer": player.is_dealer,
    }


def serialize_meld(meld: Meld) -> dict:
    """Serialize a meld. Melds are always public information."""
    return {
        "type": meld.type,
        "tiles": list(meld.tiles),
        "from_player": meld.from_player,
    }
