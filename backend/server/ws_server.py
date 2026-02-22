"""FastAPI WebSocket server for Mahjong game."""
from __future__ import annotations

import asyncio
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


@app.get("/api/history")
async def get_history() -> dict:
    """Return game history from the database."""
    db: Database = app.state.db
    history = await db.get_game_history()
    return {"games": history}


@app.get("/api/elo")
async def get_elo() -> dict:
    """Return ELO history from the database."""
    db: Database = app.state.db
    elo = await db.get_elo_history()
    return {"history": elo}


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
                mode = msg.get("mode", "easy")
                if mode == "inspect":
                    manager, game_id = await _handle_inspect_game(
                        websocket, db, msg
                    )
                else:
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

    # 3. Save replay frames from the initial AI turns.
    await _save_replay_frames(db, game_id, manager)

    # 4. Check if the game already ended during start.
    if manager.session.state.phase in ("win", "draw"):
        await _send_game_end(websocket, manager, db, game_id)
    else:
        # 5. If the human needs to act, send an action request.
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

    # 2. Save replay frames to database.
    if game_id:
        await _save_replay_frames(db, game_id, manager)

    # 3. Send updated state.
    await websocket.send_json({
        "type": "game_state",
        "state": manager.get_client_state(),
    })

    # 4. Check game end.
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


async def _handle_inspect_game(
    websocket: WebSocket,
    db: Database,
    msg: dict,
) -> tuple[GameManager, str]:
    """Create an inspect-mode game where all 4 players are AI.

    The full game runs automatically and state updates are streamed to the
    client after each AI action batch.
    """
    manager = GameManager(human_seat=0, mode="inspect")
    game_id = str(uuid.uuid4())
    await db.save_game(game_id, "inspect", -1)

    # start() will run the entire game since all seats are AI
    manager.start()

    # Save replay frames before sending to client (ensures persistence
    # even if the client disconnects mid-stream).
    await _save_replay_frames(db, game_id, manager)

    # Send all accumulated events
    for event in manager.get_events():
        await websocket.send_json({"type": "event", **event})

    # Send final state (always revealed in inspect mode)
    await websocket.send_json({
        "type": "game_state",
        "state": manager.get_client_state(),
    })

    # Send game end
    await _send_game_end(websocket, manager, db, game_id)

    return manager, game_id


async def _save_replay_frames(
    db: Database,
    game_id: str,
    manager: GameManager,
) -> None:
    """Persist all replay frames accumulated in the manager to the database."""
    for frame in manager.get_replay_frames():
        await db.save_replay_frame(
            game_id,
            frame["turn"],
            json.dumps(frame),
        )
    # Clear the frames after saving to avoid re-saving on next call
    manager.replay_frames.clear()


async def _send_game_end(
    websocket: WebSocket,
    manager: GameManager,
    db: Database,
    game_id: str | None,
) -> None:
    """Send a game-end event and persist the result."""
    phase = manager.session.state.phase
    event_data: dict = {
        "type": "event",
        "event": phase,
        "state": manager.get_client_state(reveal_all=True),
    }
    if phase == "win":
        scoring = manager.get_scoring()
        if scoring is not None:
            event_data["scoring"] = scoring
    await websocket.send_json(event_data)
    if game_id:
        await db.finish_game(game_id, phase)
