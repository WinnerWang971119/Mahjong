"""Tests for the GameManager orchestration layer."""
from __future__ import annotations

from server.game_manager import GameManager


def test_start_game():
    gm = GameManager(human_seat=0)
    gm.start()
    state = gm.get_client_state()
    assert state is not None
    assert state["phase"] in ("play", "flower_replacement", "win", "draw")


def test_ai_auto_play_until_human_turn():
    gm = GameManager(human_seat=0)
    gm.start()
    # After start, if human is not dealer, AI turns should have run
    req = gm.get_action_request()
    # Eventually human should get a turn or game ends
    assert req is not None or gm.session.state.phase in ("win", "draw")


def test_human_discard_triggers_ai_continuation():
    gm = GameManager(human_seat=0)
    gm.start()
    req = gm.get_action_request()
    if req and "discard" in [o["type"] for o in req["options"]]:
        tile = gm.session.state.players[0].hand[0]
        gm.handle_human_action("discard", tile=tile)
        # AI should have continued


def test_full_game_completes():
    """Auto-play human with first legal action until game ends."""
    gm = GameManager(human_seat=0)
    gm.start()
    for _ in range(200):
        if gm.session.state.phase in ("win", "draw"):
            break
        req = gm.get_action_request()
        if req:
            option = req["options"][0]
            gm.handle_human_action(
                option["type"], tile=option.get("tile"), combo=option.get("combo")
            )
    assert gm.session.state.phase in ("win", "draw")


def test_get_events_returns_list():
    gm = GameManager(human_seat=0)
    gm.start()
    events = gm.get_events()
    assert isinstance(events, list)


def test_get_client_state_hides_opponents():
    gm = GameManager(human_seat=0)
    gm.start()
    state = gm.get_client_state()
    # Human player's hand should be visible
    assert state["players"][0]["hand"] is not None
    # Opponent hands should be hidden
    for i in range(1, 4):
        assert state["players"][i]["hand"] is None


def test_get_client_state_reveal_all():
    gm = GameManager(human_seat=0)
    gm.start()
    state = gm.get_client_state(reveal_all=True)
    for i in range(4):
        assert state["players"][i]["hand"] is not None


def test_full_game_non_zero_seat():
    """Human at seat 2 — dealer (seat 0) is AI and should auto-play."""
    gm = GameManager(human_seat=2)
    gm.start()
    for _ in range(200):
        if gm.session.state.phase in ("win", "draw"):
            break
        req = gm.get_action_request()
        if req:
            option = req["options"][0]
            gm.handle_human_action(
                option["type"], tile=option.get("tile"), combo=option.get("combo")
            )
    assert gm.session.state.phase in ("win", "draw")


def test_multiple_full_games():
    """Run 5 full games to check for stability."""
    for _ in range(5):
        gm = GameManager(human_seat=0)
        gm.start()
        for _ in range(200):
            if gm.session.state.phase in ("win", "draw"):
                break
            req = gm.get_action_request()
            if req:
                option = req["options"][0]
                gm.handle_human_action(
                    option["type"],
                    tile=option.get("tile"),
                    combo=option.get("combo"),
                )
        assert gm.session.state.phase in ("win", "draw")
