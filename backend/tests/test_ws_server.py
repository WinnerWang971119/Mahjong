"""Tests for the FastAPI WebSocket server."""
from __future__ import annotations

import json

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient

from server.ws_server import app, _init_db


@pytest.fixture(autouse=True)
def _setup_db():
    """Ensure in-memory DB is used for all tests."""
    _init_db(":memory:")


# ── HTTP health check ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


# ── WebSocket new_game ─────────────────────────────────────────────────

def test_websocket_new_game():
    """Creating a new game returns a game_state message."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})
            data = ws.receive_json()
            assert data["type"] == "game_state"
            assert data["state"]["phase"] in (
                "play", "flower_replacement", "win", "draw"
            )


def test_websocket_new_game_default_mode():
    """Mode defaults to 'easy' when omitted."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game"})
            data = ws.receive_json()
            assert data["type"] == "game_state"


# ── WebSocket action flow ─────────────────────────────────────────────

def test_websocket_action_flow():
    """Send an action after starting a game and verify response."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})
            # Drain all initial messages until we find an action_request
            state_msg = ws.receive_json()
            assert state_msg["type"] == "game_state"

            # Collect remaining initial messages (events + action_request)
            action_req = None
            try:
                for _ in range(50):
                    msg = ws.receive_json()
                    if msg["type"] == "action_request":
                        action_req = msg
                        break
                    if msg["type"] == "event" and msg.get("event") in (
                        "win", "draw"
                    ):
                        break
            except Exception:
                pass

            if action_req is not None:
                option = action_req["options"][0]
                ws.send_json({
                    "type": "action",
                    "action": option["type"],
                    "tile": option.get("tile"),
                    "combo": option.get("combo"),
                })
                resp = ws.receive_json()
                assert resp["type"] in ("game_state", "event")


def test_websocket_full_game():
    """Play a full game through the WebSocket interface."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})

            game_ended = False
            for _ in range(500):
                msg = ws.receive_json()

                if msg["type"] == "event" and msg.get("event") in (
                    "win", "draw"
                ):
                    game_ended = True
                    break

                if msg["type"] == "action_request":
                    option = msg["options"][0]
                    ws.send_json({
                        "type": "action",
                        "action": option["type"],
                        "tile": option.get("tile"),
                        "combo": option.get("combo"),
                    })

            assert game_ended, "Game did not end within 500 message exchanges"


# ── WebSocket replay_load ──────────────────────────────────────────────

def test_websocket_replay_load_unknown_game():
    """Loading replay for a non-existent game returns empty frames."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "replay_load", "game_id": "nonexistent"})
            data = ws.receive_json()
            assert data["type"] == "replay_data"
            assert data["game_id"] == "nonexistent"
            assert data["frames"] == []


# ── WebSocket unknown message type ────────────────────────────────────

def test_websocket_unknown_message_type():
    """Unknown message types return an error response."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "bogus"})
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "unknown" in data["message"].lower()


# ── HTTP history endpoint (Task 6.6) ─────────────────────────────────

def test_history_endpoint_empty():
    """History endpoint returns empty list when no games played."""
    with TestClient(app) as client:
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "games" in data
        assert isinstance(data["games"], list)


def test_elo_endpoint_empty():
    """ELO endpoint returns empty list when no records exist."""
    with TestClient(app) as client:
        resp = client.get("/api/elo")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data
        assert isinstance(data["history"], list)


def test_history_endpoint_after_game():
    """History endpoint returns games after a game is played."""
    with TestClient(app) as client:
        # Play a game via WebSocket first
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})
            for _ in range(500):
                msg = ws.receive_json()
                if msg["type"] == "event" and msg.get("event") in (
                    "win", "draw"
                ):
                    break
                if msg["type"] == "action_request":
                    option = msg["options"][0]
                    ws.send_json({
                        "type": "action",
                        "action": option["type"],
                        "tile": option.get("tile"),
                        "combo": option.get("combo"),
                    })

        # Now check history
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["games"]) >= 1
        game = data["games"][0]
        assert "game_id" in game
        assert "mode" in game
        # Result may or may not be set yet depending on async timing,
        # but the game record should exist.
        assert game["result"] in ("win", "draw", None)


# ── Replay frame recording via WebSocket (Task 6.3) ──────────────────

def test_websocket_replay_frames_after_full_game():
    """After playing a full game, replay_load should return frames."""
    with TestClient(app) as client:
        # Play a full game
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})

            game_ended = False
            for _ in range(500):
                msg = ws.receive_json()

                if msg["type"] == "event" and msg.get("event") in (
                    "win", "draw"
                ):
                    game_ended = True
                    break

                if msg["type"] == "action_request":
                    option = msg["options"][0]
                    ws.send_json({
                        "type": "action",
                        "action": option["type"],
                        "tile": option.get("tile"),
                        "combo": option.get("combo"),
                    })

            assert game_ended, "Game did not end within 500 message exchanges"

        # Get the game_id from history
        resp = client.get("/api/history")
        games = resp.json()["games"]
        assert len(games) > 0
        game_id = games[0]["game_id"]

        # Load replay via websocket
        with client.websocket_connect("/ws") as ws:
            ws.send_json({
                "type": "replay_load",
                "game_id": game_id,
            })
            data = ws.receive_json()
            assert data["type"] == "replay_data"
            assert data["game_id"] == game_id
            assert len(data["frames"]) > 0
            # Verify frame structure
            frame = json.loads(data["frames"][0]["action_json"])
            assert "turn" in frame
            assert "event" in frame


# ── Inspect mode via WebSocket (Task 6.8) ─────────────────────────────

def test_websocket_win_event_includes_scoring():
    """When a game ends in a win, the end event should include scoring data."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})

            game_ended_with_win = False
            win_event = None
            for _ in range(500):
                msg = ws.receive_json()
                if msg["type"] == "event" and msg.get("event") == "win" and "state" in msg:
                    game_ended_with_win = True
                    win_event = msg
                    break
                if msg["type"] == "event" and msg.get("event") == "draw":
                    break
                if msg["type"] == "action_request":
                    option = msg["options"][0]
                    ws.send_json({
                        "type": "action",
                        "action": option["type"],
                        "tile": option.get("tile"),
                        "combo": option.get("combo"),
                    })

            if game_ended_with_win:
                assert "scoring" in win_event, "Win event should include scoring data"
                scoring = win_event["scoring"]
                assert "yaku" in scoring
                assert "total" in scoring
                assert "payments" in scoring


def test_replay_frames_contain_state():
    """Replay frames should include game state snapshots for replay playback."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "easy"})
            for _ in range(500):
                msg = ws.receive_json()
                if msg["type"] == "event" and msg.get("event") in ("win", "draw"):
                    break
                if msg["type"] == "action_request":
                    option = msg["options"][0]
                    ws.send_json({
                        "type": "action",
                        "action": option["type"],
                        "tile": option.get("tile"),
                        "combo": option.get("combo"),
                    })

        resp = client.get("/api/history")
        games = resp.json()["games"]
        assert len(games) > 0
        game_id = games[0]["game_id"]

        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "replay_load", "game_id": game_id})
            data = ws.receive_json()
            assert data["type"] == "replay_data"
            assert len(data["frames"]) > 0
            frame = json.loads(data["frames"][0]["action_json"])
            assert "state" in frame, "Replay frame should include game state"
            assert "players" in frame["state"]


@pytest.mark.slow
def test_websocket_inspect_mode():
    """Inspect mode should auto-play a full game and send events + state."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "inspect"})

            # In inspect mode the server sends all events, then
            # game_state, then the final end event from _send_game_end.
            # The events stream may include a "win" action from AI before
            # the final game-end event. We count end events: the last one
            # (from _send_game_end) has a "state" key.
            got_game_state = False
            got_ai_thinking = False
            got_final_end = False
            messages = []
            for _ in range(2000):
                msg = ws.receive_json()
                messages.append(msg)

                if msg["type"] == "game_state":
                    got_game_state = True
                    state = msg.get("state", {})
                    for p in state.get("players", []):
                        assert p["hand"] is not None

                if msg["type"] == "event":
                    if msg.get("event") == "ai_thinking":
                        got_ai_thinking = True
                    # The final end event from _send_game_end includes
                    # a "state" key; normal action events do not.
                    if (
                        msg.get("event") in ("win", "draw")
                        and "state" in msg
                    ):
                        got_final_end = True
                        break

            assert got_final_end, (
                f"Inspect game did not end. Got {len(messages)} messages. "
                f"Last few types: {[m['type'] for m in messages[-5:]]}"
            )
            assert got_game_state, "No game_state received in inspect mode"
            assert got_ai_thinking, "No ai_thinking events in inspect mode"


@pytest.mark.slow
def test_websocket_inspect_mode_saves_replay():
    """Inspect mode should save replay frames to the database."""
    with TestClient(app) as client:
        # Run inspect game
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "new_game", "mode": "inspect"})
            for _ in range(2000):
                msg = ws.receive_json()
                if msg["type"] == "event" and msg.get("event") in (
                    "win", "draw"
                ):
                    break

        # Verify replay was saved
        resp = client.get("/api/history")
        games = resp.json()["games"]
        assert len(games) > 0
        game_id = games[0]["game_id"]

        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "replay_load", "game_id": game_id})
            data = ws.receive_json()
            assert data["type"] == "replay_data"
            assert len(data["frames"]) > 0
