# Phase 2 Frontend Testing & Bug Fix Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up vitest for the frontend, fix 3 identified bugs, and create a comprehensive test suite that verifies the Phase 2 desktop UI works correctly.

**Architecture:** Install vitest + jsdom + @testing-library/react. Write unit tests for the Zustand store, React components, and hooks. Fix bugs in HandTiles selection, ScoringScreen data flow, and ReplayViewer frame data.

**Tech Stack:** Vitest, @testing-library/react, jsdom, React 18, Zustand 5, TypeScript

---

## Bugs Identified

1. **HandTiles selection** (`src/components/game/HandTiles.tsx:20`): `selectedTile === tile` matches by tile code. Duplicate tiles (e.g. two "1m") all appear selected. Fix: use index-based selection.
2. **ScoringScreen data never populated** (`src/hooks/useGameSocket.ts:39-45`): On win/draw events, `setScoringResult()` is never called. The server sends scoring data in the `event` message but the hook ignores it. Fix: extract scoring from the event message.
3. **ReplayViewer shows nothing** (`src/components/replay/ReplayViewer.tsx:26-28`): `applyFrame` looks for `frame.state` but replay frames from `GameManager._append_event` only store `{turn, event, player, tile}`. Fix: include game state snapshots in replay frames on the backend.

---

### Task 1: Install Frontend Test Dependencies

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`

**Step 1: Install vitest and testing libraries**

Run from `frontend/`:
```bash
pnpm add -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

**Step 2: Create vitest config**

Create `frontend/vitest.config.ts`:
```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false,
  },
})
```

**Step 3: Create test setup file**

Create `frontend/src/test/setup.ts`:
```ts
import '@testing-library/jest-dom/vitest'
```

**Step 4: Add test script to package.json**

Add to `scripts` in `frontend/package.json`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

**Step 5: Verify vitest runs (no tests yet)**

Run: `cd frontend && pnpm test`
Expected: "No test files found" or similar (no errors)

**Step 6: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml frontend/vitest.config.ts frontend/src/test/setup.ts
git commit -m "feat(frontend): add vitest testing infrastructure"
```

---

### Task 2: Test & Fix gameStore (Zustand store)

**Files:**
- Create: `frontend/src/store/__tests__/gameStore.test.ts`
- (No code changes expected — store logic is straightforward)

**Step 1: Write store tests**

Create `frontend/src/store/__tests__/gameStore.test.ts`:
```ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useGameStore } from '../gameStore'

// Reset store between tests
beforeEach(() => {
  useGameStore.setState(useGameStore.getInitialState())
})

describe('gameStore', () => {
  it('starts with default state', () => {
    const state = useGameStore.getState()
    expect(state.connected).toBe(false)
    expect(state.gameState).toBeNull()
    expect(state.currentScreen).toBe('lobby')
    expect(state.selectedTile).toBeNull()
    expect(state.events).toEqual([])
    expect(state.scoringResult).toBeNull()
    expect(state.settings.animationSpeed).toBe('normal')
    expect(state.settings.language).toBe('zh-TW')
  })

  it('setConnected updates connected state', () => {
    useGameStore.getState().setConnected(true)
    expect(useGameStore.getState().connected).toBe(true)
  })

  it('setCurrentScreen changes screen', () => {
    useGameStore.getState().setCurrentScreen('game')
    expect(useGameStore.getState().currentScreen).toBe('game')
  })

  it('setSelectedTile selects and deselects', () => {
    useGameStore.getState().setSelectedTile('1m')
    expect(useGameStore.getState().selectedTile).toBe('1m')
    useGameStore.getState().setSelectedTile(null)
    expect(useGameStore.getState().selectedTile).toBeNull()
  })

  it('addEvent appends to event list', () => {
    useGameStore.getState().addEvent({ event: 'draw', player: 0, tile: '1m' })
    useGameStore.getState().addEvent({ event: 'discard', player: 0, tile: '2m' })
    expect(useGameStore.getState().events).toHaveLength(2)
    expect(useGameStore.getState().events[0].event).toBe('draw')
  })

  it('clearEvents empties the list', () => {
    useGameStore.getState().addEvent({ event: 'draw', player: 0 })
    useGameStore.getState().clearEvents()
    expect(useGameStore.getState().events).toEqual([])
  })

  it('updateSettings merges partial settings', () => {
    useGameStore.getState().updateSettings({ animationSpeed: 'fast' })
    const settings = useGameStore.getState().settings
    expect(settings.animationSpeed).toBe('fast')
    expect(settings.language).toBe('zh-TW') // unchanged
  })

  it('setGameState stores game state', () => {
    const mockState = {
      players: [],
      discard_pool: [],
      current_player: 0,
      round_wind: 'E' as const,
      round_number: 0,
      dealer_index: 0,
      wall_remaining: 56,
      last_discard: null,
      phase: 'play' as const,
    }
    useGameStore.getState().setGameState(mockState)
    expect(useGameStore.getState().gameState).toBe(mockState)
  })

  it('setScoringResult stores scoring data', () => {
    const scoring = {
      yaku: [['門清', 1]] as [string, number][],
      subtotal: 1,
      total: 1,
      payments: { 0: -3, 1: 1, 2: 1, 3: 1 },
    }
    useGameStore.getState().setScoringResult(scoring)
    expect(useGameStore.getState().scoringResult).toBe(scoring)
  })

  it('replay state setters work', () => {
    const frames = [{ game_id: 'g1', turn_number: 1, action_json: '{}', timestamp: '' }]
    useGameStore.getState().setReplayFrames(frames)
    expect(useGameStore.getState().replayFrames).toBe(frames)
    useGameStore.getState().setReplayIndex(5)
    expect(useGameStore.getState().replayIndex).toBe(5)
    useGameStore.getState().setReplayPlaying(true)
    expect(useGameStore.getState().replayPlaying).toBe(true)
    useGameStore.getState().setReplaySpeed(2)
    expect(useGameStore.getState().replaySpeed).toBe(2)
  })

  it('resetGame clears game-related state', () => {
    useGameStore.getState().setCurrentScreen('game')
    useGameStore.getState().setSelectedTile('1m')
    useGameStore.getState().addEvent({ event: 'draw', player: 0 })
    useGameStore.getState().resetGame()

    const state = useGameStore.getState()
    expect(state.gameState).toBeNull()
    expect(state.currentScreen).toBe('lobby')
    expect(state.selectedTile).toBeNull()
    expect(state.events).toEqual([])
    expect(state.scoringResult).toBeNull()
  })
})
```

**Step 2: Run tests**

Run: `cd frontend && pnpm test`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add frontend/src/store/__tests__/gameStore.test.ts
git commit -m "test(frontend): add gameStore unit tests"
```

---

### Task 3: Test & Fix HandTiles Selection Bug

**Files:**
- Create: `frontend/src/components/game/__tests__/HandTiles.test.tsx`
- Modify: `frontend/src/components/game/HandTiles.tsx`
- Modify: `frontend/src/components/game/GameView.tsx`
- Modify: `frontend/src/components/game/GameTable.tsx`
- Modify: `frontend/src/components/game/PlayerArea.tsx`

**Bug:** `selectedTile === tile` matches ALL tiles with same code. When hand has two "1m" tiles, both appear selected.

**Fix:** Change selection model from tile code to tile index. The `selectedTile` store field becomes `selectedTileIndex: number | null`.

**Step 1: Write failing test**

Create `frontend/src/components/game/__tests__/HandTiles.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HandTiles from '../HandTiles'

describe('HandTiles', () => {
  it('renders face-up tiles for self', () => {
    const { container } = render(
      <HandTiles tiles={['1m', '2m', '3m']} tileCount={3} isSelf selectedTileIndex={null} />
    )
    // Each tile renders an SVG
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(3)
  })

  it('renders face-down tiles for opponents', () => {
    const { container } = render(
      <HandTiles tiles={null} tileCount={5} isSelf={false} selectedTileIndex={null} />
    )
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(5)
  })

  it('selects only the tile at the given index, not duplicates', () => {
    const { container } = render(
      <HandTiles tiles={['1m', '1m', '2m']} tileCount={3} isSelf selectedTileIndex={0} />
    )
    const svgs = container.querySelectorAll('svg')
    // First 1m is selected (has translate class), second 1m is NOT
    expect(svgs[0].className.baseVal).toContain('-translate-y-2')
    expect(svgs[1].className.baseVal).not.toContain('-translate-y-2')
  })

  it('calls onTileClick with index when a tile is clicked', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    const { container } = render(
      <HandTiles tiles={['1m', '2m']} tileCount={2} isSelf selectedTileIndex={null} onTileClick={onClick} />
    )
    const svgs = container.querySelectorAll('svg')
    await user.click(svgs[1])
    expect(onClick).toHaveBeenCalledWith(1)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm test -- src/components/game/__tests__/HandTiles.test.tsx`
Expected: FAIL (props don't match current interface)

**Step 3: Fix HandTiles.tsx**

Change `frontend/src/components/game/HandTiles.tsx` to use index-based selection:
```tsx
import Tile from '../tiles/Tile'

interface HandTilesProps {
  tiles: string[] | null
  tileCount: number
  isSelf: boolean
  selectedTileIndex: number | null
  onTileClick?: (index: number) => void
}

export default function HandTiles({ tiles, tileCount, isSelf, selectedTileIndex, onTileClick }: HandTilesProps) {
  if (isSelf && tiles) {
    return (
      <div className="flex gap-0.5 justify-center">
        {tiles.map((tile, i) => (
          <Tile
            key={`${tile}-${i}`}
            code={tile}
            faceUp
            selected={selectedTileIndex === i}
            onClick={() => onTileClick?.(i)}
          />
        ))}
      </div>
    )
  }

  // Opponents: face-down tiles
  return (
    <div className="flex gap-0.5 justify-center">
      {Array.from({ length: tileCount }, (_, i) => (
        <Tile key={i} code="" faceUp={false} />
      ))}
    </div>
  )
}
```

**Step 4: Update PlayerArea.tsx to pass index**

Change `frontend/src/components/game/PlayerArea.tsx` — update props:
- Change `selectedTile: string | null` → `selectedTileIndex: number | null`
- Change `onTileClick?: (tile: string) => void` → `onTileClick?: (index: number) => void`
- Pass `selectedTileIndex` to `HandTiles`

```tsx
import HandTiles from './HandTiles'
import MeldArea from './MeldArea'
import FlowerArea from './FlowerArea'
import type { PlayerState } from '../../types/game'

interface PlayerAreaProps {
  player: PlayerState
  isSelf: boolean
  isActive: boolean
  selectedTileIndex: number | null
  onTileClick?: (index: number) => void
  position: 'bottom' | 'right' | 'top' | 'left'
}

const positionClasses: Record<string, string> = {
  bottom: 'flex flex-col items-center',
  top: 'flex flex-col-reverse items-center rotate-180',
  left: 'flex flex-row-reverse items-center -rotate-90',
  right: 'flex flex-row items-center rotate-90',
}

const WIND_LABELS: Record<number, string> = { 0: '東', 1: '南', 2: '西', 3: '北' }

export default function PlayerArea({ player, isSelf, isActive, selectedTileIndex, onTileClick, position }: PlayerAreaProps) {
  return (
    <div className={`${positionClasses[position]} ${isActive ? 'ring-2 ring-yellow-400 rounded-lg p-1' : 'p-1'}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-white font-bold">
          {WIND_LABELS[player.seat]}
          {player.is_dealer && ' 莊'}
        </span>
        <FlowerArea flowers={player.flowers} />
      </div>
      <MeldArea melds={player.melds} />
      <HandTiles
        tiles={player.hand}
        tileCount={player.hand_count}
        isSelf={isSelf}
        selectedTileIndex={selectedTileIndex}
        onTileClick={onTileClick}
      />
    </div>
  )
}
```

**Step 5: Update GameTable.tsx**

Change `selectedTile` → `selectedTileIndex` and `onTileClick` type:

```tsx
import PlayerArea from './PlayerArea'
import DiscardPool from './DiscardPool'
import WallIndicator from './WallIndicator'
import type { GameState } from '../../types/game'

interface GameTableProps {
  gameState: GameState
  myPlayerIndex: number
  selectedTileIndex: number | null
  onTileClick: (index: number) => void
}

function getSeatPosition(seat: number, myIndex: number): 'bottom' | 'right' | 'top' | 'left' {
  const relative = (seat - myIndex + 4) % 4
  return (['bottom', 'right', 'top', 'left'] as const)[relative]
}

export default function GameTable({ gameState, myPlayerIndex, selectedTileIndex, onTileClick }: GameTableProps) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] grid-rows-[auto_1fr_auto] w-full h-full gap-2 p-4">
      {/* Top player */}
      <div className="col-start-2 row-start-1 flex justify-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'top' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTileIndex={null} position="top" />
          ) : null,
        )}
      </div>

      {/* Left player */}
      <div className="col-start-1 row-start-2 flex items-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'left' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTileIndex={null} position="left" />
          ) : null,
        )}
      </div>

      {/* Center: discard pool + wall indicator */}
      <div className="col-start-2 row-start-2 flex flex-col items-center justify-center gap-2">
        <WallIndicator remaining={gameState.wall_remaining} />
        <DiscardPool discards={gameState.discard_pool} lastDiscard={gameState.last_discard} />
      </div>

      {/* Right player */}
      <div className="col-start-3 row-start-2 flex items-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'right' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTileIndex={null} position="right" />
          ) : null,
        )}
      </div>

      {/* Bottom player (self) */}
      <div className="col-start-2 row-start-3 flex justify-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'bottom' ? (
            <PlayerArea key={p.seat} player={p} isSelf isActive={p.seat === gameState.current_player} selectedTileIndex={selectedTileIndex} onTileClick={onTileClick} position="bottom" />
          ) : null,
        )}
      </div>
    </div>
  )
}
```

**Step 6: Update GameView.tsx**

Change the store from `selectedTile: string | null` to `selectedTileIndex: number | null`. Update GameView to resolve index → tile code for discard actions:

```tsx
import GameHeader from './GameHeader'
import GameTable from './GameTable'
import ActionPanel from './ActionPanel'
import GameLog from './GameLog'
import { useGameStore } from '../../store/gameStore'

interface GameViewProps {
  onAction: (action: string, tile?: string, combo?: string[]) => void
}

export default function GameView({ onAction }: GameViewProps) {
  const gameState = useGameStore((s) => s.gameState)
  const myPlayerIndex = useGameStore((s) => s.myPlayerIndex)
  const actionRequest = useGameStore((s) => s.actionRequest)
  const selectedTileIndex = useGameStore((s) => s.selectedTileIndex)
  const setSelectedTileIndex = useGameStore((s) => s.setSelectedTileIndex)
  const events = useGameStore((s) => s.events)

  if (!gameState) return null

  const myHand = gameState.players[myPlayerIndex]?.hand ?? []
  const selectedTileCode = selectedTileIndex !== null ? myHand[selectedTileIndex] ?? null : null

  const handleTileClick = (index: number) => {
    if (selectedTileIndex === index) {
      // Double-click effect: discard immediately
      const tile = myHand[index]
      if (tile) onAction('discard', tile)
      setSelectedTileIndex(null)
    } else {
      setSelectedTileIndex(index)
    }
  }

  return (
    <div className="min-h-screen bg-table-green flex flex-col">
      <GameHeader gameState={gameState} />
      <div className="flex-1 flex">
        <div className="flex-1">
          <GameTable
            gameState={gameState}
            myPlayerIndex={myPlayerIndex}
            selectedTileIndex={selectedTileIndex}
            onTileClick={handleTileClick}
          />
        </div>
        <GameLog events={events} />
      </div>
      {actionRequest && (
        <ActionPanel options={actionRequest.options} onAction={onAction} />
      )}
      {/* Discard button when tile is selected and it's our active turn */}
      {selectedTileCode && !actionRequest && gameState.current_player === myPlayerIndex && (
        <div className="flex justify-center p-2 bg-black/40">
          <button
            onClick={() => {
              onAction('discard', selectedTileCode)
              setSelectedTileIndex(null)
            }}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold"
          >
            打出 {selectedTileCode} (Discard)
          </button>
        </div>
      )}
    </div>
  )
}
```

**Step 7: Update gameStore.ts**

Replace `selectedTile` with `selectedTileIndex` in the store:
- `selectedTile: string | null` → `selectedTileIndex: number | null`
- `setSelectedTile: (tile: string | null) => void` → `setSelectedTileIndex: (idx: number | null) => void`
- Update `resetGame` to clear `selectedTileIndex`

**Step 8: Update useGameSocket.ts**

In `sendAction`, change `setSelectedTile(null)` → `setSelectedTileIndex(null)`.

**Step 9: Update ReplayViewer.tsx**

In `ReplayViewer`, change `selectedTile={null}` to `selectedTileIndex={null}` and `onTileClick={() => {}}` to `onTileClick={() => {}}` (index param, no-op is fine).

**Step 10: Run all tests**

Run: `cd frontend && pnpm test && pnpm run build`
Expected: All tests PASS, build succeeds

**Step 11: Commit**

```bash
git add frontend/src/components/game/ frontend/src/store/ frontend/src/hooks/ frontend/src/components/replay/
git commit -m "fix(frontend): use index-based tile selection to fix duplicate selection bug"
```

---

### Task 4: Test & Fix ScoringScreen Data Flow

**Files:**
- Create: `frontend/src/hooks/__tests__/useGameSocket.test.ts`
- Modify: `frontend/src/hooks/useGameSocket.ts` (add setScoringResult call)
- Modify: `frontend/src/types/game.ts` (add scoring field to event message)
- Modify: `backend/server/ws_server.py` (include scoring in game-end event)
- Modify: `backend/server/game_manager.py` (compute scoring on win)

**Bug:** When a game ends with a win, the server doesn't send scoring data, and the frontend never calls `setScoringResult()`.

**Step 1: Write backend test for scoring in game-end event**

Add to `backend/tests/test_ws_server.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_ws_server.py::test_websocket_win_event_includes_scoring -v`
Expected: FAIL (scoring key not in event)

**Step 3: Add scoring computation to GameManager**

Modify `backend/server/game_manager.py` — add a `get_scoring()` method:
```python
def get_scoring(self) -> dict | None:
    """Compute scoring breakdown if the game ended with a win."""
    if self.session.state.phase != "win":
        return None
    try:
        from engine.scorer import ScoreCalculator
        state = self.session.state
        winner_idx = self.session._winner_idx
        if winner_idx is None:
            return None
        calc = ScoreCalculator(state, winner_idx)
        result = calc.calculate()
        return {
            "winner": winner_idx,
            "yaku": result.yaku,
            "subtotal": result.subtotal,
            "total": result.total,
            "payments": result.payments,
        }
    except Exception:
        return None
```

Note: This depends on the ScoreCalculator API. The agent implementing this MUST read `backend/engine/scorer.py` to understand the actual API and adapt accordingly. The scorer may use different method names or return different structures.

**Step 4: Include scoring in game-end event**

Modify `backend/server/ws_server.py` `_send_game_end()`:
```python
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
```

**Step 5: Update frontend types**

Modify `frontend/src/types/game.ts` — update the event ServerMessage variant:
```ts
| { type: 'event'; event: string; player?: number; tile?: string; state?: GameState; scoring?: ScoringBreakdown }
```

**Step 6: Update useGameSocket to populate scoring**

Modify `frontend/src/hooks/useGameSocket.ts` in the `'event'` case:
```ts
case 'event':
  addEvent({ event: msg.event, player: msg.player, tile: msg.tile })
  if (msg.event === 'win' || msg.event === 'draw') {
    if (msg.state) {
      setGameState(msg.state)
    }
    if (msg.scoring) {
      useGameStore.getState().setScoringResult(msg.scoring)
    }
    setActionRequest(null)
    setCurrentScreen('scoring')
  }
  break
```

**Step 7: Run backend tests**

Run: `cd backend && uv run pytest tests/test_ws_server.py -v`
Expected: All PASS

**Step 8: Run frontend tests and build**

Run: `cd frontend && pnpm test && pnpm run build`
Expected: All PASS

**Step 9: Commit**

```bash
git add backend/server/game_manager.py backend/server/ws_server.py frontend/src/types/game.ts frontend/src/hooks/useGameSocket.ts backend/tests/test_ws_server.py
git commit -m "fix: include scoring data in win events and display on ScoringScreen"
```

---

### Task 5: Test & Fix ReplayViewer

**Files:**
- Modify: `backend/server/game_manager.py` (include state snapshots in replay frames)
- Modify: `backend/tests/test_ws_server.py` (verify replay frame has state)
- Create: `frontend/src/components/replay/__tests__/ReplayViewer.test.tsx`

**Bug:** Replay frames only contain `{turn, event, player, tile}` — no game state. The ReplayViewer's `applyFrame` looks for `frame.state` and finds nothing.

**Step 1: Write failing backend test**

Add to `backend/tests/test_ws_server.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_ws_server.py::test_replay_frames_contain_state -v`
Expected: FAIL ("state" not in frame)

**Step 3: Include state snapshot in replay frames**

Modify `backend/server/game_manager.py` `_append_event()` to include a state snapshot:
```python
def _append_event(
    self, event: str, player: int, tile: str | None = None
) -> None:
    event_dict = {"event": event, "player": player, "tile": tile}
    self.events.append(event_dict)
    # Record for replay with state snapshot
    self._turn_counter += 1
    state_snapshot = serialize_game_state(
        self.session.state, viewer_idx=0, reveal_all=True
    )
    self.replay_frames.append({
        "turn": self._turn_counter,
        "event": event,
        "player": player,
        "tile": tile,
        "state": state_snapshot,
    })
```

Note: `serialize_game_state` is already imported via `from server.serializer import serialize_game_state` at the top of the file.

**Step 4: Run backend tests**

Run: `cd backend && uv run pytest tests/test_ws_server.py -v`
Expected: All PASS

**Step 5: Write frontend ReplayViewer test**

Create `frontend/src/components/replay/__tests__/ReplayViewer.test.tsx`:
```tsx
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReplayViewer from '../ReplayViewer'
import { useGameStore } from '../../../store/gameStore'

const mockGameState = {
  players: [
    { seat: 0, hand: ['1m', '2m'], hand_count: 2, melds: [], flowers: [], discards: [], is_dealer: true },
    { seat: 1, hand: ['3m', '4m'], hand_count: 2, melds: [], flowers: [], discards: [], is_dealer: false },
    { seat: 2, hand: ['5m', '6m'], hand_count: 2, melds: [], flowers: [], discards: [], is_dealer: false },
    { seat: 3, hand: ['7m', '8m'], hand_count: 2, melds: [], flowers: [], discards: [], is_dealer: false },
  ],
  discard_pool: [],
  current_player: 0,
  round_wind: 'E' as const,
  round_number: 0,
  dealer_index: 0,
  wall_remaining: 50,
  last_discard: null,
  phase: 'play' as const,
}

const mockFrames = [
  {
    game_id: 'g1',
    turn_number: 1,
    action_json: JSON.stringify({ turn: 1, event: 'draw', player: 0, tile: '1m', state: mockGameState }),
    timestamp: '2026-01-01',
  },
  {
    game_id: 'g1',
    turn_number: 2,
    action_json: JSON.stringify({ turn: 2, event: 'discard', player: 0, tile: '2m', state: { ...mockGameState, current_player: 1 } }),
    timestamp: '2026-01-01',
  },
]

beforeEach(() => {
  useGameStore.setState(useGameStore.getInitialState())
})

describe('ReplayViewer', () => {
  it('renders replay controls', () => {
    useGameStore.getState().setReplayFrames(mockFrames)
    useGameStore.getState().setGameState(mockGameState)
    render(<ReplayViewer onBack={() => {}} />)
    expect(screen.getByText(/播放/)).toBeTruthy()
    expect(screen.getByText('1 / 2')).toBeTruthy()
  })

  it('stepping forward applies frame state', async () => {
    const user = userEvent.setup()
    useGameStore.getState().setReplayFrames(mockFrames)
    useGameStore.getState().setGameState(mockGameState)
    render(<ReplayViewer onBack={() => {}} />)

    const nextBtn = screen.getByText(/下一步/)
    await user.click(nextBtn)

    // After stepping forward, game state should update
    const state = useGameStore.getState().gameState
    expect(state?.current_player).toBe(1)
  })

  it('calls onBack when back button clicked', async () => {
    const user = userEvent.setup()
    const onBack = vi.fn()
    useGameStore.getState().setReplayFrames(mockFrames)
    useGameStore.getState().setGameState(mockGameState)
    render(<ReplayViewer onBack={onBack} />)

    await user.click(screen.getByText('返回'))
    expect(onBack).toHaveBeenCalled()
  })
})
```

**Step 6: Run all tests**

Run: `cd frontend && pnpm test && pnpm run build`
Expected: All PASS

**Step 7: Commit**

```bash
git add backend/server/game_manager.py backend/tests/test_ws_server.py frontend/src/components/replay/__tests__/ReplayViewer.test.tsx
git commit -m "fix: include game state in replay frames for working replay playback"
```

---

### Task 6: Test Core UI Components

**Files:**
- Create: `frontend/src/components/tiles/__tests__/Tile.test.tsx`
- Create: `frontend/src/components/game/__tests__/GameTable.test.tsx`
- Create: `frontend/src/components/game/__tests__/ActionPanel.test.tsx`
- Create: `frontend/src/components/game/__tests__/GameView.test.tsx`
- Create: `frontend/src/components/lobby/__tests__/GameLobby.test.tsx`
- Create: `frontend/src/components/scoring/__tests__/ScoringScreen.test.tsx`

**Step 1: Write Tile component tests**

Create `frontend/src/components/tiles/__tests__/Tile.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Tile from '../Tile'

describe('Tile', () => {
  it('renders character tile face-up', () => {
    const { container } = render(<Tile code="1m" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
    // Should have the tile face rect (cream color)
    const rects = container.querySelectorAll('rect')
    expect(rects.length).toBeGreaterThan(0)
  })

  it('renders face-down tile', () => {
    const { container } = render(<Tile code="1m" faceUp={false} />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
  })

  it('renders honor tiles', () => {
    for (const code of ['E', 'S', 'W', 'N', 'C', 'F', 'B']) {
      const { container } = render(<Tile code={code} />)
      expect(container.querySelector('svg')).toBeTruthy()
    }
  })

  it('renders flower tiles', () => {
    for (let i = 1; i <= 8; i++) {
      const { container } = render(<Tile code={`f${i}`} />)
      expect(container.querySelector('svg')).toBeTruthy()
    }
  })

  it('renders all suit tiles', () => {
    for (const suit of ['m', 'p', 's']) {
      for (let v = 1; v <= 9; v++) {
        const { container } = render(<Tile code={`${v}${suit}`} />)
        expect(container.querySelector('svg')).toBeTruthy()
      }
    }
  })

  it('applies selected style', () => {
    const { container } = render(<Tile code="1m" selected />)
    const svg = container.querySelector('svg')
    expect(svg?.className.baseVal).toContain('-translate-y-2')
  })

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    const { container } = render(<Tile code="1m" onClick={onClick} />)
    await user.click(container.querySelector('svg')!)
    expect(onClick).toHaveBeenCalled()
  })

  it('does not call onClick when disabled', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    const { container } = render(<Tile code="1m" disabled onClick={onClick} />)
    await user.click(container.querySelector('svg')!)
    expect(onClick).not.toHaveBeenCalled()
  })
})
```

**Step 2: Write GameLobby test**

Create `frontend/src/components/lobby/__tests__/GameLobby.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import GameLobby from '../GameLobby'

describe('GameLobby', () => {
  it('renders title', () => {
    render(<GameLobby onStartGame={() => {}} connected={true} />)
    expect(screen.getByText('台灣16張麻將')).toBeTruthy()
  })

  it('disables start buttons when not connected', () => {
    render(<GameLobby onStartGame={() => {}} connected={false} />)
    const easyBtn = screen.getByText(/簡單模式/)
    expect(easyBtn).toBeDisabled()
  })

  it('enables start buttons when connected', () => {
    render(<GameLobby onStartGame={() => {}} connected={true} />)
    const easyBtn = screen.getByText(/簡單模式/)
    expect(easyBtn).not.toBeDisabled()
  })

  it('calls onStartGame with mode when button clicked', async () => {
    const user = userEvent.setup()
    const onStart = vi.fn()
    render(<GameLobby onStartGame={onStart} connected={true} />)
    await user.click(screen.getByText(/簡單模式/))
    expect(onStart).toHaveBeenCalledWith('easy')
  })

  it('shows connecting message when not connected', () => {
    render(<GameLobby onStartGame={() => {}} connected={false} />)
    expect(screen.getByText(/Connecting/)).toBeTruthy()
  })

  it('navigates to settings', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<GameLobby onStartGame={() => {}} connected={true} onNavigate={onNavigate} />)
    await user.click(screen.getByText(/設定/))
    expect(onNavigate).toHaveBeenCalledWith('settings')
  })
})
```

**Step 3: Write ActionPanel test**

Create `frontend/src/components/game/__tests__/ActionPanel.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ActionPanel from '../ActionPanel'

describe('ActionPanel', () => {
  it('renders action buttons', () => {
    const options = [
      { type: 'pong' as const, tile: '1m', combo: null },
      { type: 'pass' as const, tile: null, combo: null },
    ]
    render(<ActionPanel options={options} onAction={() => {}} />)
    expect(screen.getByText(/碰/)).toBeTruthy()
    expect(screen.getByText(/過/)).toBeTruthy()
  })

  it('calls onAction with correct type on click', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    const options = [
      { type: 'pong' as const, tile: '1m', combo: null },
      { type: 'pass' as const, tile: null, combo: null },
    ]
    render(<ActionPanel options={options} onAction={onAction} />)
    await user.click(screen.getByText(/碰/))
    expect(onAction).toHaveBeenCalledWith('pong', '1m', undefined)
  })

  it('shows chi combo selector when multiple chi options', async () => {
    const user = userEvent.setup()
    const options = [
      { type: 'chi' as const, tile: '2m', combo: ['1m', '2m', '3m'] },
      { type: 'chi' as const, tile: '5m', combo: ['4m', '5m', '6m'] },
      { type: 'pass' as const, tile: null, combo: null },
    ]
    render(<ActionPanel options={options} onAction={() => {}} />)
    await user.click(screen.getByText(/吃/))
    // Should show combo selection
    expect(screen.getByText(/選擇吃牌組合/)).toBeTruthy()
  })
})
```

**Step 4: Write ScoringScreen test**

Create `frontend/src/components/scoring/__tests__/ScoringScreen.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ScoringScreen from '../ScoringScreen'

describe('ScoringScreen', () => {
  it('shows draw message when no scoring', () => {
    render(<ScoringScreen scoring={null} onContinue={() => {}} />)
    expect(screen.getByText(/流局/)).toBeTruthy()
  })

  it('shows yaku list when scoring provided', () => {
    const scoring = {
      yaku: [['門清自摸', 3], ['平胡', 2]] as [string, number][],
      subtotal: 5,
      total: 5,
      payments: { 0: 15, 1: -5, 2: -5, 3: -5 },
    }
    render(<ScoringScreen scoring={scoring} onContinue={() => {}} />)
    expect(screen.getByText('門清自摸')).toBeTruthy()
    expect(screen.getByText('平胡')).toBeTruthy()
  })

  it('calls onContinue when button clicked', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    render(<ScoringScreen scoring={null} onContinue={onContinue} />)
    await user.click(screen.getByText(/繼續/))
    expect(onContinue).toHaveBeenCalled()
  })
})
```

**Step 5: Run all tests**

Run: `cd frontend && pnpm test`
Expected: All PASS

**Step 6: Commit**

```bash
git add frontend/src/components/
git commit -m "test(frontend): add component tests for Tile, GameLobby, ActionPanel, ScoringScreen, ReplayViewer"
```

---

### Task 7: Run Full Test Suite and Verify Build

**Step 1: Run all backend tests**

Run: `cd backend && uv run pytest -v`
Expected: All PASS

**Step 2: Run all frontend tests**

Run: `cd frontend && pnpm test`
Expected: All PASS

**Step 3: Verify build**

Run: `cd frontend && pnpm run build`
Expected: Build succeeds with no errors

**Step 4: Verify TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 5: Final commit if needed**

Any remaining fixes get committed.
