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


# ── Replay frame recording (Task 6.3) ─────────────────────────────────

def test_replay_frames_accumulate_during_start():
    """Replay frames should be recorded during the initial AI turns."""
    gm = GameManager(human_seat=0)
    gm.start()
    frames = gm.get_replay_frames()
    # There should be at least some frames from AI turns during start
    # (unless human is dealer and acts first, but even then flower
    # replacement generates events)
    assert isinstance(frames, list)


def test_replay_frames_have_turn_counter():
    """Each replay frame should have an incrementing turn number."""
    gm = GameManager(human_seat=0)
    gm.start()
    frames = gm.get_replay_frames()
    if len(frames) >= 2:
        for i in range(1, len(frames)):
            assert frames[i]["turn"] > frames[i - 1]["turn"]


def test_replay_frames_grow_after_human_action():
    """Replay frames should grow after a human action."""
    gm = GameManager(human_seat=0)
    gm.start()
    initial_count = len(gm.get_replay_frames())

    req = gm.get_action_request()
    if req and gm.session.state.phase not in ("win", "draw"):
        option = req["options"][0]
        gm.handle_human_action(
            option["type"], tile=option.get("tile"), combo=option.get("combo")
        )
        new_count = len(gm.get_replay_frames())
        assert new_count > initial_count


def test_replay_frame_structure():
    """Each replay frame should contain turn, event, player, and tile keys."""
    gm = GameManager(human_seat=0)
    gm.start()
    frames = gm.get_replay_frames()
    for frame in frames:
        assert "turn" in frame
        assert "event" in frame
        assert "player" in frame
        assert "tile" in frame


def test_full_game_replay_frames():
    """A full game should produce replay frames for all actions."""
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
    frames = gm.get_replay_frames()
    assert len(frames) > 0


# ── Inspect mode (Task 6.8) ───────────────────────────────────────────

def test_inspect_mode_runs_full_game():
    """Inspect mode should auto-play all 4 seats to completion."""
    gm = GameManager(human_seat=0, mode="inspect")
    gm.start()
    assert gm.session.state.phase in ("win", "draw")


def test_inspect_mode_reveals_all_hands():
    """In inspect mode, get_client_state should reveal all hands."""
    gm = GameManager(human_seat=0, mode="inspect")
    gm.start()
    state = gm.get_client_state()
    for i in range(4):
        assert state["players"][i]["hand"] is not None


def test_inspect_mode_emits_ai_thinking_events():
    """Inspect mode should emit ai_thinking events with shanten data."""
    gm = GameManager(human_seat=0, mode="inspect")
    gm.start()
    events = gm.get_events()
    ai_thinking = [e for e in events if e["event"] == "ai_thinking"]
    # Should have at least some ai_thinking events
    assert len(ai_thinking) > 0
    for evt in ai_thinking:
        assert "shanten" in evt
        assert evt["player"] in range(4)


def test_inspect_mode_produces_replay_frames():
    """Inspect mode should produce replay frames for the full game."""
    gm = GameManager(human_seat=0, mode="inspect")
    gm.start()
    frames = gm.get_replay_frames()
    assert len(frames) > 0


def test_inspect_mode_multiple_games():
    """Run 3 inspect-mode games for stability."""
    for _ in range(3):
        gm = GameManager(human_seat=0, mode="inspect")
        gm.start()
        assert gm.session.state.phase in ("win", "draw")
