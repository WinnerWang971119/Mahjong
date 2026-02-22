"""Tests for server.serializer – game state JSON serialization with visibility filtering."""
from engine.state import GameState, PlayerState, Meld
from server.serializer import serialize_game_state, serialize_player, serialize_meld


def test_own_hand_visible():
    """Player can see their own hand."""
    player = PlayerState(seat=0, hand=["1m", "2m", "3m"])
    result = serialize_player(player, is_self=True)
    assert result["hand"] == ["1m", "2m", "3m"]


def test_opponent_hand_hidden():
    """Opponent hand is hidden, only count shown."""
    player = PlayerState(seat=1, hand=["1m", "2m", "3m"])
    result = serialize_player(player, is_self=False)
    assert result["hand"] is None
    assert result["hand_count"] == 3


def test_melds_always_visible():
    """Melds are always visible for all players."""
    meld = Meld(type="pong", tiles=["5m", "5m", "5m"], from_player=2)
    result = serialize_meld(meld)
    assert result["tiles"] == ["5m", "5m", "5m"]
    assert result["type"] == "pong"
    assert result["from_player"] == 2


def test_reveal_all_shows_opponent_hands():
    """In inspect/replay mode, all hands visible."""
    player = PlayerState(seat=1, hand=["1m", "2m", "3m"])
    result = serialize_player(player, is_self=False, reveal=True)
    assert result["hand"] == ["1m", "2m", "3m"]


def test_serialize_game_state_structure():
    """Full game state serialization has correct structure."""
    gs = GameState.new_game()
    gs.players[0].hand = ["1m", "2m", "3m"]
    gs.players[1].hand = ["4p", "5p"]
    gs.phase = "play"
    gs.current_player = 0
    result = serialize_game_state(gs, viewer_idx=0)
    assert result["players"][0]["hand"] == ["1m", "2m", "3m"]
    assert result["players"][1]["hand"] is None
    assert result["players"][1]["hand_count"] == 2
    assert result["current_player"] == 0
    assert result["phase"] == "play"
    assert "wall_remaining" in result


def test_serialize_game_state_reveal_all():
    """With reveal_all, all players' hands are visible."""
    gs = GameState.new_game()
    gs.players[0].hand = ["1m"]
    gs.players[1].hand = ["2m", "3m"]
    result = serialize_game_state(gs, viewer_idx=0, reveal_all=True)
    assert result["players"][1]["hand"] == ["2m", "3m"]
