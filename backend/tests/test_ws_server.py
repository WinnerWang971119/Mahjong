"""Tests for the FastAPI WebSocket server."""
from __future__ import annotations

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
