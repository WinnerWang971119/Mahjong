"""Async SQLite database layer for game history, replays, and ELO tracking."""
from __future__ import annotations

import aiosqlite


class Database:
    """Manages an async SQLite connection for persisting game data."""

    def __init__(self, db_path: str = "mahjong.db") -> None:
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Open the database connection and create tables if they don't exist."""
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                mode TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                human_seat INTEGER,
                result TEXT
            );
            CREATE TABLE IF NOT EXISTS replay_frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT REFERENCES games(id),
                turn_number INTEGER,
                action_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS elo_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT REFERENCES games(id),
                elo_before INTEGER,
                elo_after INTEGER,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    # ── Game CRUD ──────────────────────────────────────────────────────

    async def save_game(
        self, game_id: str, mode: str, human_seat: int
    ) -> None:
        """Insert a new game record."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO games (id, mode, human_seat) VALUES (?, ?, ?)",
            (game_id, mode, human_seat),
        )
        await self._conn.commit()

    async def finish_game(self, game_id: str, result: str) -> None:
        """Mark a game as finished with the given result."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE games SET result = ?, ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result, game_id),
        )
        await self._conn.commit()

    async def get_game_history(self) -> list[dict]:
        """Return all games ordered by most recent first."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT id AS game_id, mode, started_at, ended_at, human_seat, result "
            "FROM games ORDER BY started_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ── Replay Frames ─────────────────────────────────────────────────

    async def save_replay_frame(
        self, game_id: str, turn_number: int, action_json: str
    ) -> None:
        """Append a replay frame for the given game."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO replay_frames (game_id, turn_number, action_json) "
            "VALUES (?, ?, ?)",
            (game_id, turn_number, action_json),
        )
        await self._conn.commit()

    async def get_replay_frames(self, game_id: str) -> list[dict]:
        """Return all replay frames for a game ordered by turn number."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT game_id, turn_number, action_json, timestamp "
            "FROM replay_frames WHERE game_id = ? ORDER BY turn_number",
            (game_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ── ELO History ───────────────────────────────────────────────────

    async def save_elo(
        self, game_id: str, elo_before: int, elo_after: int
    ) -> None:
        """Record an ELO change after a game."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO elo_history (game_id, elo_before, elo_after) "
            "VALUES (?, ?, ?)",
            (game_id, elo_before, elo_after),
        )
        await self._conn.commit()

    async def get_elo_history(self) -> list[dict]:
        """Return all ELO records ordered by most recent first."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT game_id, elo_before, elo_after, recorded_at "
            "FROM elo_history ORDER BY recorded_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
