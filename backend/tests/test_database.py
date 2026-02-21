"""Tests for the async SQLite database layer."""
from __future__ import annotations

import pytest
import pytest_asyncio

from server.database import Database


@pytest_asyncio.fixture
async def db():
    d = Database(":memory:")
    await d.initialize()
    yield d
    await d.close()


@pytest.mark.asyncio
async def test_save_and_get_game(db):
    await db.save_game("g1", "easy", 0)
    await db.finish_game("g1", "win")
    history = await db.get_game_history()
    assert len(history) == 1
    assert history[0]["game_id"] == "g1"
    assert history[0]["result"] == "win"


@pytest.mark.asyncio
async def test_save_and_get_replay_frames(db):
    await db.save_game("g1", "easy", 0)
    await db.save_replay_frame("g1", 1, '{"action":"discard","tile":"5m"}')
    await db.save_replay_frame("g1", 2, '{"action":"draw"}')
    frames = await db.get_replay_frames("g1")
    assert len(frames) == 2
    assert frames[0]["turn_number"] == 1


@pytest.mark.asyncio
async def test_save_and_get_elo(db):
    await db.save_game("g1", "easy", 0)
    await db.save_elo("g1", 1200, 1215)
    history = await db.get_elo_history()
    assert len(history) == 1
    assert history[0]["elo_before"] == 1200
    assert history[0]["elo_after"] == 1215


@pytest.mark.asyncio
async def test_empty_history(db):
    history = await db.get_game_history()
    assert history == []


@pytest.mark.asyncio
async def test_multiple_games(db):
    await db.save_game("g1", "easy", 0)
    await db.finish_game("g1", "win")
    await db.save_game("g2", "easy", 1)
    await db.finish_game("g2", "draw")
    history = await db.get_game_history()
    assert len(history) == 2
