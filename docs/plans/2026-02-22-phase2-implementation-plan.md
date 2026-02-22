# Phase 2 Implementation Plan — Desktop UI (Electron + React + TypeScript)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete, playable desktop Mahjong game where a human plays against 3 AI opponents, with replay viewer, inspect mode, and settings.

**Architecture:** Electron spawns a Python FastAPI WebSocket server as a child process. React renderer connects via `ws://localhost:{PORT}` and acts as a thin client — all game logic stays in Python. SQLite stores replays and ELO history.

**Tech Stack:** Electron, React 18, TypeScript, Zustand, Tailwind CSS v4, Framer Motion, Vite, electron-builder, pnpm (frontend); FastAPI, uvicorn, aiosqlite, uv (backend)

**Design doc:** `docs/plans/2026-02-22-phase2-desktop-ui-design.md`

---

## Build Order (6 Groups, ~45 Tasks)

```
Group 1: Python WebSocket Server     → backend/server/
Group 2: Frontend Scaffold           → frontend/ (Electron + Vite + React)
Group 3: Core UI Components          → Tile SVGs + table layout
Group 4: Game Flow                   → WebSocket integration + human controls
Group 5: Polish                      → Timer, animations, scoring screen
Group 6: Advanced Features           → Settings, replay, inspect mode
```

---

## Group 1: Python WebSocket Server

**Goal:** Wrap existing `GameSession` engine behind a FastAPI WebSocket server.

**Critical files to reference:**
- `backend/engine/state.py` — `PlayerState`, `GameState`, `Meld` dataclasses
- `backend/engine/game_session.py` — `GameSession` state machine
- `backend/engine/scorer.py` — `score_hand()`, scoring result
- `backend/ai/rule_based.py` — `RuleBasedAI.choose_action()`
- `backend/engine/tiles.py` — tile code format (`"5m"`, `"E"`, `"f3"`)

---

### Task 1.1: Add server dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1:** Add server optional dependencies to pyproject.toml:
```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "websockets>=13.0",
    "aiosqlite>=0.20",
]
```

**Step 2:** Install:
```bash
cd backend && uv pip install -e ".[server]" --system
```

**Step 3:** Verify:
```bash
python -c "import fastapi; import uvicorn; import aiosqlite; print('OK')"
```

**Step 4:** Commit:
```bash
git commit -m "build: add FastAPI, uvicorn, websockets, aiosqlite server deps"
```

---

### Task 1.2: Create state serializer

**Files:**
- Create: `backend/server/__init__.py`
- Create: `backend/server/serializer.py`
- Test: `backend/tests/test_serializer.py`

**Step 1: Write failing tests**

```python
# test_serializer.py
from engine.state import GameState, PlayerState, Meld
from server.serializer import serialize_game_state, serialize_player, serialize_meld

def test_own_hand_visible():
    """Player can see their own hand."""
    player = PlayerState(seat=0, hand=["1m","2m","3m"], ...)
    result = serialize_player(player, is_self=True)
    assert result["hand"] == ["1m","2m","3m"]

def test_opponent_hand_hidden():
    """Opponent hand is hidden, only count shown."""
    player = PlayerState(seat=1, hand=["1m","2m","3m"], ...)
    result = serialize_player(player, is_self=False)
    assert result["hand"] is None
    assert result["hand_count"] == 3

def test_melds_always_visible():
    """Melds are always visible for all players."""
    meld = Meld(type="pong", tiles=["5m","5m","5m"], from_player=2)
    result = serialize_meld(meld)
    assert result["tiles"] == ["5m","5m","5m"]

def test_reveal_all_shows_opponent_hands():
    """In inspect/replay mode, all hands visible."""
    # ... test with reveal_all=True
```

**Step 2:** Run tests, verify they fail.
```bash
pytest backend/tests/test_serializer.py -v
```

**Step 3:** Implement `serializer.py`:
```python
def serialize_game_state(gs: GameState, viewer_idx: int, reveal_all: bool = False) -> dict:
    """Serialize GameState to JSON-safe dict. Hide opponents' hands unless reveal_all."""

def serialize_player(player: PlayerState, is_self: bool, reveal: bool = False) -> dict:
    """Serialize a single player. Hidden hand -> hand_count only."""

def serialize_meld(meld: Meld) -> dict:
    """Meld is always public."""
```

**Step 4:** Run tests, verify pass.

**Step 5:** Commit:
```bash
git commit -m "feat(server): add game state JSON serializer with visibility filtering"
```

---

### Task 1.3: Create game manager

**Files:**
- Create: `backend/server/game_manager.py`
- Test: `backend/tests/test_game_manager.py`

**Step 1: Write failing tests**

```python
# test_game_manager.py
from server.game_manager import GameManager

def test_start_game():
    gm = GameManager(human_seat=0)
    gm.start()
    state = gm.get_client_state()
    assert state is not None
    assert state["phase"] in ("play", "flower_replacement")

def test_ai_auto_play_until_human_turn():
    gm = GameManager(human_seat=0)
    gm.start()
    # After start, if human is not dealer, AI turns should have run
    req = gm.get_action_request()
    # Eventually human should get a turn or game ends
    assert req is not None or gm.session.phase in ("win", "draw")

def test_human_discard_triggers_ai_continuation():
    gm = GameManager(human_seat=0)
    gm.start()
    req = gm.get_action_request()
    if req and "discard" in [o["type"] for o in req["options"]]:
        tile = gm.session.players[0].hand[0]
        gm.handle_human_action("discard", tile=tile)
        # AI should have continued

def test_full_game_completes():
    gm = GameManager(human_seat=0)
    gm.start()
    # Auto-play human with random legal actions until game ends
    for _ in range(200):
        if gm.session.phase in ("win", "draw"):
            break
        req = gm.get_action_request()
        if req:
            option = req["options"][0]
            gm.handle_human_action(option["type"], tile=option.get("tile"))
    assert gm.session.phase in ("win", "draw")
```

**Step 2:** Run tests, verify fail.

**Step 3:** Implement `GameManager`:
```python
class GameManager:
    def __init__(self, human_seat: int = 0, mode: str = "easy"):
        self.session = GameSession()
        self.human_seat = human_seat
        self.ai = RuleBasedAI()
        self.mode = mode
        self.events: list[dict] = []

    def start(self) -> None:
    def handle_human_action(self, action_type, tile=None, combo=None) -> None:
    def _run_ai_turns(self) -> None:
    def get_client_state(self) -> dict:
    def get_action_request(self) -> dict | None:
```

**Step 4:** Run tests, verify pass.

**Step 5:** Commit:
```bash
git commit -m "feat(server): add GameManager orchestrating human + AI turns"
```

---

### Task 1.4: Create SQLite database layer

**Files:**
- Create: `backend/server/database.py`
- Test: `backend/tests/test_database.py`

**Step 1: Write failing tests** using in-memory SQLite (`:memory:`):
```python
import pytest
import asyncio
from server.database import Database

@pytest.fixture
async def db():
    d = Database(":memory:")
    await d.initialize()
    return d

@pytest.mark.asyncio
async def test_save_and_get_game(db):
    await db.save_game("g1", "easy", 0)
    await db.finish_game("g1", "win")
    history = await db.get_game_history()
    assert len(history) == 1
    assert history[0]["result"] == "win"

@pytest.mark.asyncio
async def test_save_and_get_replay_frames(db):
    await db.save_game("g1", "easy", 0)
    await db.save_replay_frame("g1", 1, '{"action":"discard"}')
    frames = await db.get_replay_frames("g1")
    assert len(frames) == 1

@pytest.mark.asyncio
async def test_save_and_get_elo(db):
    await db.save_game("g1", "easy", 0)
    await db.save_elo("g1", 1200, 1215)
    history = await db.get_elo_history()
    assert history[0]["elo_after"] == 1215
```

**Step 2:** Run tests, verify fail.

**Step 3:** Implement `Database` class with `aiosqlite`.

**Step 4:** Run tests, verify pass. Add `pytest-asyncio` to dev deps.

**Step 5:** Commit:
```bash
git commit -m "feat(server): add async SQLite database layer for games, replays, ELO"
```

---

### Task 1.5: Create WebSocket server

**Files:**
- Create: `backend/server/ws_server.py`
- Test: `backend/tests/test_ws_server.py`

**Step 1: Write failing tests**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from server.ws_server import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
```

WebSocket integration test (uses `websockets` test client or `httpx-ws`).

**Step 2:** Run tests, verify fail.

**Step 3:** Implement FastAPI app:
```python
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager = GameManager()
    # Message loop
```

Handle messages: `new_game`, `action`, `replay_load`.

**Step 4:** Run tests, verify pass.

**Step 5:** Commit:
```bash
git commit -m "feat(server): add FastAPI WebSocket server with game protocol"
```

---

### Task 1.6: Add server entry point

**Files:**
- Create: `backend/server/__main__.py`

```python
"""Entry point: python -m server [--port PORT]"""
import os, uvicorn
from server.ws_server import app

def main():
    port = int(os.environ.get("MAHJONG_PORT", "9000"))
    uvicorn.run(app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()
```

**Test:** `cd backend && python -m server` starts, `curl http://localhost:9000/health` returns OK.

**Commit:**
```bash
git commit -m "feat(server): add __main__.py entry point for server startup"
```

---

### Task 1.7: Update CI for server tests

**Files:**
- Modify: `.github/workflows/ci.yml` — add server deps install + server test step
- Modify: `backend/pyproject.toml` — add `pytest-asyncio`, `httpx` to dev deps

**Commit:**
```bash
git commit -m "ci: add server test coverage to GitHub Actions workflow"
```

---

### Group 1 Dependency Graph

```
1.1 (deps)
  ├─> 1.2 (serializer)  ─┐
  └─> 1.4 (database)     ├─> 1.3 (game_manager)
                          │        └─> 1.5 (ws_server)
                          │             └─> 1.6 (entry point)
                          │                  └─> 1.7 (CI)
```

**Parallelizable:** 1.2 and 1.4 after 1.1.

---

## Group 2: Frontend Scaffold

**Goal:** Working Electron app that spawns Python server and connects via WebSocket.

---

### Task 2.1: Initialize Vite + React + TypeScript project

**Files to create:**
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`
- `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`
- `frontend/.gitignore`

**Steps:**
```bash
cd frontend
pnpm create vite . --template react-ts
pnpm add zustand framer-motion
pnpm add -D tailwindcss @tailwindcss/vite electron electron-builder @types/node
```

**Test:** `pnpm dev` serves React placeholder at localhost:5173.

**Commit:** `feat(frontend): scaffold Vite + React + TypeScript project`

---

### Task 2.2: Configure Tailwind CSS v4

**Files:**
- Create: `frontend/src/index.css`
- Modify: `frontend/vite.config.ts` — add `@tailwindcss/vite` plugin
- Modify: `frontend/src/main.tsx` — import `index.css`

**CSS theme:**
```css
@import "tailwindcss";

@theme {
  --color-table-green: #1a5c2a;
  --color-table-blue: #1a3c5c;
  --color-tile-cream: #f5f0e1;
  --color-wan-red: #c41e3a;
  --color-tong-blue: #2563eb;
  --color-suo-green: #16a34a;
  --color-honor-dark: #1e293b;
  --color-flower-gold: #ca8a04;
}
```

Import Noto Sans TC via `@import url(...)` from Google Fonts.

**Test:** Tailwind utility classes render correctly.

**Commit:** `feat(frontend): configure Tailwind CSS v4 with mahjong color theme`

---

### Task 2.3: Add Electron main process

**Files:**
- Create: `frontend/electron/main.ts` — BrowserWindow + Python server spawn
- Create: `frontend/electron/preload.ts` — minimal preload
- Modify: `frontend/package.json` — add `"main"`, Electron scripts

**Key logic:**
```typescript
function spawnPythonServer(): ChildProcess {
  const port = 9000
  return spawn('python', ['-m', 'server'], {
    cwd: path.join(__dirname, '../../backend'),
    env: { ...process.env, MAHJONG_PORT: String(port) }
  })
}
// Wait for /health, then create BrowserWindow (min 1280x720, resizable)
```

**Test:** `pnpm electron:dev` opens Electron with React app + Python server running.

**Commit:** `feat(frontend): add Electron main process with Python server spawn`

---

### Task 2.4: Configure electron-builder

**Files:**
- Modify: `frontend/package.json` — add `"build"` config

**Commit:** `build(frontend): configure electron-builder for Windows packaging`

---

### Task 2.5: Create TypeScript types

**Files:**
- Create: `frontend/src/types/game.ts`

Mirror Python models exactly:
```typescript
export interface GameState {
  players: PlayerState[]
  discard_pool: string[]
  current_player: number
  round_wind: Wind
  round_number: number
  dealer_index: number
  wall_remaining: number
  last_discard: string | null
  phase: Phase
}

export interface PlayerState {
  seat: number
  hand: string[] | null  // null for opponents
  hand_count: number
  melds: Meld[]
  flowers: string[]
  discards: string[]
  is_dealer: boolean
}

export interface ActionRequest {
  player: number
  options: ActionOption[]
  timeout: number
}

// ... ServerMessage, ClientMessage, ScoringBreakdown, etc.
```

**Test:** `pnpm tsc --noEmit` succeeds.

**Commit:** `feat(frontend): add TypeScript game type definitions mirroring server protocol`

---

### Task 2.6: Create Zustand store

**Files:**
- Create: `frontend/src/store/gameStore.ts`

Store shape per design doc: connection, game state, UI state, settings, replay slices + actions.

**Test:** Compilation check.

**Commit:** `feat(frontend): add Zustand game store with all state slices`

---

### Task 2.7: Create WebSocket connection hook

**Files:**
- Create: `frontend/src/hooks/useGameSocket.ts`

Connect to `ws://localhost:{PORT}/ws`, reconnect with backoff, dispatch to Zustand store, expose `sendAction()`, `sendNewGame()`, `sendReplayLoad()`.

**Test:** Manual — connect to running Python server, verify state updates in React DevTools.

**Commit:** `feat(frontend): add useGameSocket hook with reconnection and message dispatch`

---

### Group 2 Dependency Graph

```
2.1 (Vite init)
  ├─> 2.2 (Tailwind)     ─┐
  ├─> 2.3 (Electron)      │  parallel
  └─> 2.5 (TS types)     ─┘
       └─> 2.6 (Zustand store)
            └─> 2.7 (WebSocket hook)
2.3 ──> 2.4 (electron-builder)
```

---

## Group 3: Core UI Components

**Goal:** Custom SVG tiles + game table layout.

---

### Task 3.1: TileBase SVG component

**File:** `frontend/src/components/tiles/TileBase.tsx`

Base tile: rounded rect 48×64px, cream fill, shadow. Props: `faceUp`, `selected`, `highlighted`, `disabled`, `onClick`, `children`.

**Commit:** `feat(frontend): add TileBase SVG component with face-up/down/selected states`

### Task 3.2: Character tile artwork (萬)

**File:** `frontend/src/components/tiles/suits/CharacterTile.tsx`

SVG for 1m–9m. Chinese numerals (一~九) in red/gold + 萬.

**Commit:** `feat(frontend): add Character (萬) tile SVG artwork`

### Task 3.3: Circle tile artwork (筒)

**File:** `frontend/src/components/tiles/suits/CircleTile.tsx`

SVG circle patterns for 1p–9p in blue.

**Commit:** `feat(frontend): add Circle (筒) tile SVG artwork`

### Task 3.4: Bamboo tile artwork (索)

**File:** `frontend/src/components/tiles/suits/BambooTile.tsx`

SVG bamboo sticks for 1s–9s in green.

**Commit:** `feat(frontend): add Bamboo (索) tile SVG artwork`

### Task 3.5: Honor tile artwork

**File:** `frontend/src/components/tiles/suits/HonorTile.tsx`

SVG for E/S/W/N/C/F/B. White on dark background.

**Commit:** `feat(frontend): add Honor tile SVG artwork`

### Task 3.6: Flower tile artwork

**File:** `frontend/src/components/tiles/suits/FlowerTile.tsx`

SVG for f1–f8. Gold on soft green.

**Commit:** `feat(frontend): add Flower tile SVG artwork`

### Task 3.7: Tile dispatcher component

**File:** `frontend/src/components/tiles/Tile.tsx`

Maps tile code (`"5m"`, `"E"`, `"f3"`) → correct artwork component inside `TileBase`.

**Commit:** `feat(frontend): add Tile dispatcher mapping codes to SVG artwork`

### Task 3.8–3.15: Game layout components

| Task | File | Component | Purpose |
|------|------|-----------|---------|
| 3.8 | `components/game/HandTiles.tsx` | HandTiles | Row of tiles (face-up or face-down) |
| 3.9 | `components/game/MeldArea.tsx` | MeldArea | Exposed chi/pong/kong sets |
| 3.10 | `components/game/FlowerArea.tsx` | FlowerArea | Collected flowers |
| 3.11 | `components/game/PlayerArea.tsx` | PlayerArea | Composes hand+melds+flowers, CSS rotation per seat |
| 3.12 | `components/game/DiscardPool.tsx` | DiscardPool | Central 6-column discard grid |
| 3.13 | `components/game/WallIndicator.tsx` | WallIndicator | Remaining tile count badge |
| 3.14 | `components/game/GameTable.tsx` | GameTable | CSS Grid: 4 PlayerAreas + center DiscardPool |
| 3.15 | `components/game/GameHeader.tsx` | GameHeader | Round wind, dealer, turn indicator |

Each gets its own commit: `feat(frontend): add {ComponentName} component`

### Task 3.16: Dev tile gallery

**File:** `frontend/src/pages/DevTileGallery.tsx`

All 42 unique tiles in a grid + all states. Route: `/dev/tiles`.

**Commit:** `feat(frontend): add dev tile gallery for visual QA`

---

### Group 3 Dependency Graph

```
3.1 (TileBase)
  ├─> 3.2, 3.3, 3.4, 3.5, 3.6 (parallel artwork)
  │    └─> 3.7 (dispatcher)
  │         ├─> 3.8, 3.9, 3.10, 3.12, 3.13 (parallel)
  │         │    └─> 3.11 (PlayerArea, needs 3.8+3.9+3.10)
  │         │         └─> 3.14 (GameTable, needs 3.11+3.12+3.13)
  │         │              └─> 3.15 (GameHeader)
  └─> 3.16 (DevGallery, parallel)
```

---

## Group 4: Game Flow

**Goal:** Connect UI to live server, enable human play through a full game.

---

### Task 4.1: GameLobby component

**File:** `frontend/src/components/lobby/GameLobby.tsx`

Mode buttons: Easy (active), Hard (greyed, "Coming in Phase 4"), Inspect. Calls `sendNewGame(mode)`.

**Commit:** `feat(frontend): add GameLobby mode selection screen`

### Task 4.2: ActionPanel component

**File:** `frontend/src/components/game/ActionPanel.tsx`

Slides up when `actionRequest` is non-null. Shows 吃/碰/槓/胡/過 buttons. Chi has sub-panel for combo choices.

**Commit:** `feat(frontend): add ActionPanel with chi/pong/kong/win/pass buttons`

### Task 4.3: GameView component

**File:** `frontend/src/components/game/GameView.tsx`

Composes GameHeader + GameTable + ActionPanel + GameLog. Reads from Zustand store.

**Commit:** `feat(frontend): add GameView composing header, table, action panel`

### Task 4.4: GameLog component

**File:** `frontend/src/components/game/GameLog.tsx`

Scrollable action history: "[西家] 打出 5萬", "[南家] 碰 7筒", etc.

**Commit:** `feat(frontend): add GameLog scrollable action history panel`

### Task 4.5: Wire tile selection + discard flow

**Modify:** `HandTiles.tsx`, `gameStore.ts`

Click → select (raise), click again → discard. Double-click → instant discard.

**Commit:** `feat(frontend): wire up tile selection and discard interaction flow`

### Task 4.6: Wire claim flow

**Modify:** `ActionPanel.tsx`, `useGameSocket.ts`

Claim buttons send actions. Chi sub-panel for multiple combos. Auto-pass on 5-sec timeout.

**Commit:** `feat(frontend): wire up claim action flow with chi combo selection`

### Task 4.7: App router

**Modify:** `App.tsx`

State-based routing: lobby → game → scoring → replay → settings → history.

**Commit:** `feat(frontend): add App view routing between all screens`

---

### Group 4 Dependency Graph

```
4.1, 4.2, 4.4 (parallel)
  └─> 4.3 (GameView)
       └─> 4.7 (router)
       └─> 4.5 (discard flow)
            └─> 4.6 (claim flow)
```

---

## Group 5: Polish Features

**Goal:** Turn timer, animations, scoring screen.

---

### Task 5.1: TurnTimer component

**File:** `frontend/src/components/game/TurnTimer.tsx`

Circular SVG countdown, 10 seconds. Red at 3s. Auto-discard/auto-pass on timeout.

**Commit:** `feat(frontend): add 10-second TurnTimer with auto-action on timeout`

### Task 5.2–5.5: Animation components

| Task | File | Animation | Duration |
|------|------|-----------|----------|
| 5.2 | `components/animations/DrawAnimation.tsx` | Tile slides wall → hand | 300ms |
| 5.3 | `components/animations/DiscardAnimation.tsx` | Tile flips hand → pool | 400ms |
| 5.4 | `components/animations/MeldAnimation.tsx` | Chi/pong/kong reveal | 500ms |
| 5.5 | `components/animations/WinAnimation.tsx` | Fan-out + golden glow | 800ms |

All use Framer Motion. Each gets own commit.

### Task 5.6: Animation queue manager

**File:** `frontend/src/hooks/useAnimationQueue.ts`

Queues game events, plays sequentially. Respects `animationSpeed` setting (slow=2×, normal=1×, fast=0.5×, instant=0ms).

**Commit:** `feat(frontend): add animation queue manager with speed control`

### Task 5.7: ScoringScreen modal

**File:** `frontend/src/components/scoring/ScoringScreen.tsx`

Post-hand modal: winning hand layout, itemized yaku + tai, total (capped 81), payment breakdown, continue button.

**Commit:** `feat(frontend): add ScoringScreen modal with yaku breakdown and payments`

---

### Group 5 Dependency Graph

```
5.1, 5.2, 5.3, 5.4, 5.5, 5.7 (all parallel)
  └─> 5.6 (animation queue, needs 5.2-5.5)
```

---

## Group 6: Advanced Features

**Goal:** Settings, replay viewer, ELO history, inspect mode.

---

### Task 6.1: SettingsPanel component

**File:** `frontend/src/components/settings/SettingsPanel.tsx`

Animation speed, language, table background, sound toggle.

**Commit:** `feat(frontend): add SettingsPanel with speed, language, theme settings`

### Task 6.2: electron-store persistence

**Modify:** `electron/main.ts`, `electron/preload.ts`
**Create:** `frontend/src/hooks/useSettings.ts`

IPC bridge for settings. Falls back to localStorage in dev mode.

**Commit:** `feat(frontend): add electron-store settings persistence with IPC bridge`

### Task 6.3: Replay frame recording (server)

**Modify:** `backend/server/game_manager.py`, `backend/server/ws_server.py`

Save replay frames during gameplay. Handle `replay_load` message.

**Test (TDD):** Verify frames saved during game, `replay_load` returns them.

**Commit:** `feat(server): record replay frames during gameplay and serve on request`

### Task 6.4: ReplayViewer component

**Create:** `frontend/src/components/replay/ReplayViewer.tsx`, `ReplayControls.tsx`

Reuses GameView in read-only mode. Play/Pause, Step ←/→, Speed slider (0.5×–4×), Jump to turn. All 4 hands revealed.

**Commit:** `feat(frontend): add ReplayViewer with playback controls`

### Task 6.5: EloHistory component

**File:** `frontend/src/components/history/EloHistory.tsx`

Match history table + ELO trend line chart (SVG).

**Commit:** `feat(frontend): add EloHistory match history and ELO chart`

### Task 6.6: Server history endpoints

**Modify:** `backend/server/ws_server.py` — add `GET /api/history`, `GET /api/elo`

**Test (TDD):** Verify endpoints return correct data.

**Commit:** `feat(server): add REST endpoints for game history and ELO data`

### Task 6.7: InspectOverlay component

**File:** `frontend/src/components/game/InspectOverlay.tsx`

AI thinking overlay: shanten, top-3 discards, waiting tiles. Semi-transparent panels per AI player.

**Commit:** `feat(frontend): add InspectOverlay showing AI thinking data`

### Task 6.8: Server inspect mode

**Modify:** `backend/server/game_manager.py`, `backend/server/ws_server.py`

All 4 players AI. `reveal_all=True`. Emit `ai_thinking` events with shanten + considered actions.

**Test (TDD):** Verify inspect mode runs 4 AI, emits thinking events.

**Commit:** `feat(server): add inspect mode with full state reveal and AI thinking events`

### Task 6.9: Final integration pass

**Modify:** Various files — fix layout issues, wire all views, version bump.

**Test:** Full end-to-end: launch Electron, play game, view scoring, check replay, toggle settings, run inspect mode.

**Commit:** `feat: Phase 2 complete — desktop UI with full game, replay, and inspect mode`

---

### Group 6 Dependency Graph

```
6.1 → 6.2 (settings)
6.3 → 6.4 (replay)       all start points parallel
6.5 → 6.6 (ELO history)
6.7 → 6.8 (inspect)
  └─> 6.9 (final integration, needs all)
```

---

## Milestone ↔ Task Mapping

| Milestone | Tasks | Key Deliverable |
|-----------|-------|----------------|
| 2.1 | 1.1–1.7, 2.1–2.7 | Electron app connects to Python server |
| 2.2 | 3.8–3.15 | Game table layout renders |
| 2.3 | 3.1–3.7, 3.16 | All 42 tile SVGs render |
| 2.4 | 4.1–4.7 | Human can play a complete game |
| 2.5 | 5.1 | 10-second turn timer |
| 2.6 | 5.2–5.6 | All tile animations |
| 2.7 | 5.7 | Scoring breakdown modal |
| 2.8 | 6.1–6.2 | Settings panel |
| 2.9 | 6.3–6.6 | Replay viewer + ELO history |
| 2.10 | 6.7–6.9 | Inspect mode |

---

## Verification

After completing all tasks, verify end-to-end:

1. `cd backend && python -m server` — server starts on port 9000
2. `curl http://localhost:9000/health` — returns `{"status":"ok"}`
3. `cd frontend && pnpm electron:dev` — Electron opens, Python spawns automatically
4. Click "Easy" → game starts, tiles render, human can play
5. Complete a game → scoring screen shows with yaku breakdown
6. Open Settings → change animation speed, reload, verify persistence
7. Open Replay → load last game, step through, play/pause works
8. Start Inspect mode → 4 AI play, all hands visible, thinking data shown
9. `cd backend && pytest --cov` — all tests pass, coverage ≥85%
10. `cd frontend && pnpm tsc --noEmit` — no TypeScript errors
