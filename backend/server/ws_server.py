"""FastAPI WebSocket server for Mahjong game."""
from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from server.database import Database
from server.game_manager import GameManager

# ---------------------------------------------------------------------------
# Module-level database configuration
# ---------------------------------------------------------------------------
# By default the database uses a file; tests call ``_init_db(":memory:")``
# before the app starts to swap in an in-memory store.

_db_path: str = "mahjong.db"


def _init_db(path: str = "mahjong.db") -> None:
    """Set the database path before the application starts.

    This is intended for tests that need an in-memory database.
    """
    global _db_path
    _db_path = path


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and clean up the database on startup / shutdown."""
    app.state.db = Database(_db_path)
    await app.state.db.initialize()
    yield
    await app.state.db.close()


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    manager: GameManager | None = None
    game_id: str | None = None
    db: Database = websocket.app.state.db

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "new_game":
                manager, game_id = await _handle_new_game(
                    websocket, db, msg
                )

            elif msg_type == "action" and manager is not None:
                await _handle_action(websocket, manager, db, game_id, msg)

            elif msg_type == "replay_load":
                await _handle_replay_load(websocket, db, msg)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------

async def _handle_new_game(
    websocket: WebSocket,
    db: Database,
    msg: dict,
) -> tuple[GameManager, str]:
    """Create a new game, send initial state + events + action request."""
    mode = msg.get("mode", "easy")
    human_seat = msg.get("human_seat", 0)

    manager = GameManager(human_seat=human_seat, mode=mode)
    game_id = str(uuid.uuid4())
    await db.save_game(game_id, mode, human_seat)
    manager.start()

    # 1. Send game state.
    await websocket.send_json({
        "type": "game_state",
        "state": manager.get_client_state(),
    })

    # 2. Send accumulated events (flower draws, AI actions, etc.).
    for event in manager.get_events():
        await websocket.send_json({"type": "event", **event})

    # 3. Check if the game already ended during start.
    if manager.session.state.phase in ("win", "draw"):
        await _send_game_end(websocket, manager, db, game_id)
    else:
        # 4. If the human needs to act, send an action request.
        action_req = manager.get_action_request()
        if action_req:
            await websocket.send_json({"type": "action_request", **action_req})

    return manager, game_id


async def _handle_action(
    websocket: WebSocket,
    manager: GameManager,
    db: Database,
    game_id: str | None,
    msg: dict,
) -> None:
    """Process a human action, send events + new state."""
    action = msg.get("action")
    tile = msg.get("tile")
    combo = msg.get("combo")
    manager.handle_human_action(action, tile=tile, combo=combo)

    # 1. Send accumulated events.
    for event in manager.get_events():
        await websocket.send_json({"type": "event", **event})

    # 2. Send updated state.
    await websocket.send_json({
        "type": "game_state",
        "state": manager.get_client_state(),
    })

    # 3. Check game end.
    if manager.session.state.phase in ("win", "draw"):
        await _send_game_end(websocket, manager, db, game_id)
    else:
        action_req = manager.get_action_request()
        if action_req:
            await websocket.send_json({"type": "action_request", **action_req})


async def _handle_replay_load(
    websocket: WebSocket,
    db: Database,
    msg: dict,
) -> None:
    """Load replay frames for a given game and send them back."""
    req_game_id = msg.get("game_id", "")
    frames = await db.get_replay_frames(req_game_id)
    await websocket.send_json({
        "type": "replay_data",
        "game_id": req_game_id,
        "frames": frames,
    })


async def _send_game_end(
    websocket: WebSocket,
    manager: GameManager,
    db: Database,
    game_id: str | None,
) -> None:
    """Send a game-end event and persist the result."""
    phase = manager.session.state.phase
    await websocket.send_json({
        "type": "event",
        "event": phase,
        "state": manager.get_client_state(reveal_all=True),
    })
    if game_id:
        await db.finish_game(game_id, phase)
