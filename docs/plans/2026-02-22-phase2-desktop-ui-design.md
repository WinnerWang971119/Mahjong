# Phase 2 Design — Desktop UI (Electron + React + TypeScript)

**Date:** 2026-02-22
**Status:** Approved
**Prerequisite:** Phase 1 game engine complete (all milestones 1.1–1.8)

---

## Context

Phase 1 delivered a complete, headless Taiwan 16-tile Mahjong engine in Python with:
- Full rule implementation (tiles, wall, deal, chi/pong/kong, win detection, scoring)
- Greedy rule-based AI baseline
- 85%+ test coverage, 1000-game integration tests, CI via GitHub Actions

Phase 2 builds a desktop UI so a human can play a full 4-player game against 3 AI opponents.

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| Window size | Resizable, minimum 1280×720 |
| Replay viewer style | Both auto-play + manual stepping |
| Storage | SQLite (ELO + replays) |
| Frontend ↔ Backend | WebSocket (FastAPI) |
| Tile rendering | Custom SVG components (no external image assets) |

---

## 1. System Architecture

### Process Model

```
Electron Main Process
  → Spawns Python FastAPI server as child process
  → Monitors health, restarts on crash
  → Manages window lifecycle

Electron Renderer (React)
  → Pure UI, no game logic
  → Connects to ws://localhost:{PORT}
  → Renders game state received from server

Python Game Server (FastAPI + WebSocket)
  → Wraps existing GameSession engine
  → Drives AI turns automatically
  → Sends full visible state after every action
  → SQLite for ELO + replay storage
```

### WebSocket Protocol

**Client → Server:**
```json
{ "type": "action", "action": "discard", "tile": "5m" }
{ "type": "action", "action": "pong" }
{ "type": "action", "action": "pass" }
{ "type": "new_game", "mode": "easy" }
{ "type": "replay_load", "game_id": "abc123" }
```

**Server → Client:**
```json
{ "type": "game_state", "state": { ... } }
{ "type": "action_request", "player": 0, "options": ["discard","pong","pass"], "timeout": 10 }
{ "type": "event", "event": "win", "player": 2, "hand": [...], "scoring": {...} }
{ "type": "event", "event": "draw_tile", "player": 0, "tile": "3s" }
{ "type": "event", "event": "ai_thinking", "player": 1, "data": {...} }
```

**Design principle:** Server sends full visible game state after every action. Client is a thin renderer. Single source of truth stays in Python.

---

## 2. Frontend Component Tree

```
App
├── GameLobby              — Mode selection, new game
├── GameView               — Main game screen
│   ├── GameHeader         — Round info, wind, dealer, timer
│   ├── GameTable          — Central layout (CSS Grid)
│   │   ├── PlayerArea ×4  — One per seat (rotated via CSS)
│   │   │   ├── HandTiles  — Concealed (self) or face-down (opponents)
│   │   │   ├── MeldArea   — Exposed chi/pong/kong
│   │   │   └── FlowerArea — Collected flowers
│   │   ├── DiscardPool    — Central discard area
│   │   └── WallIndicator  — Remaining tile count
│   ├── ActionPanel        — Chi/Pong/Kong/Win/Pass buttons
│   ├── TurnTimer          — 10-sec countdown
│   ├── GameLog            — Scrollable action history
│   └── InspectOverlay     — AI thinking data (inspect mode)
├── ScoringScreen          — Post-hand breakdown (modal)
├── ReplayViewer           — Playback controls + game view
├── SettingsPanel          — Animation speed, language, theme
└── EloHistory             — Match history & ELO chart
```

### State Management: Zustand

```typescript
interface GameStore {
  // Connection
  socket: WebSocket | null
  connected: boolean

  // Game state (mirrors server)
  gameState: GameState | null
  myPlayerIndex: number

  // UI state
  actionRequest: ActionRequest | null
  selectedTile: string | null
  timerSeconds: number

  // Settings
  animationSpeed: 'slow' | 'normal' | 'fast' | 'instant'
  language: 'zh-TW' | 'en'

  // Replay
  replayData: ReplayFrame[] | null
  replayIndex: number
  replayPlaying: boolean
  replaySpeed: number
}
```

### Key Hook: `useGameSocket`

Connects to Python server, dispatches state updates to store, sends player actions, handles reconnection, manages turn timer countdown.

---

## 3. Tile Rendering — Custom SVG

Each of the 42 unique tile faces (9×3 suits + 7 honors + 8 flowers) is a React SVG component.

**Tile anatomy:** Rounded rect body (cream fill, shadow) containing suit-specific SVG paths — Chinese numerals, circle/bamboo/character artwork, honor characters, flower motifs.

**Tile back:** Dark green with SVG `<pattern>` fill.

**Base size:** 48×64px, scaled via CSS `transform: scale()`.

**Tile states:**
- Face-up: White background + artwork
- Face-down: Dark green pattern
- Selected: Raised 8px + glow border
- Highlighted: Pulsing border
- Disabled: Dimmed opacity

**Color scheme:**
- 萬 (Characters): Red/gold
- 筒 (Circles): Blue
- 索 (Bamboo): Green
- 字牌 (Honors): White on dark
- 花牌 (Flowers): Gold on soft green

**Font:** Noto Sans TC for all Chinese text.

---

## 4. Animations — Framer Motion

| Event | Animation | Duration |
|-------|-----------|----------|
| Tile draw | Slide from wall → hand | 300ms |
| Discard | Flip from hand → discard pool | 400ms |
| Chi/Pong | Tiles slide to meld area, flip face-up | 500ms |
| Kong | 4 tiles arrange into kong display | 500ms |
| Win reveal | Hand fans out in arc, golden glow | 800ms |
| Flower draw | Float to flower area + replacement draw | 600ms |
| Turn transition | Highlight moves to active player | 200ms |

**Speed multipliers:** Slow (2×), Normal (1×), Fast (0.5×), Instant (0ms).

---

## 5. Human Player Interactions

**Discard:** Click tile → raises + glows → click again to confirm. Double-click for instant discard.

**Claim (chi/pong/kong/win):** ActionPanel slides up with valid options. Chi shows sub-panel if multiple combos. 5-second decision window, auto-pass on timeout.

**Turn timer:** Circular countdown, turns red at 3 seconds, auto-discards most recently drawn tile on timeout.

---

## 6. Scoring Screen

Modal showing:
- Winning hand tiles laid out
- Itemized 計台明細 (each yaku + tai value)
- Total tai (capped at 81)
- Payment breakdown per player
- Continue button

---

## 7. Game Modes

| Mode | Description |
|------|-------------|
| Easy | 1 human + 3 rule-based AI. 10-sec timer. |
| Hard | 1 human + 3 RL-trained AI. 10-sec timer. (Phase 4) |
| Inspect | 4 AI, all hands visible, thinking overlay, playback controls. |

---

## 8. Replay Viewer

- Loads completed games from SQLite
- Reuses GameView component with replay frames instead of live WebSocket
- All 4 hands revealed
- Controls: Play/Pause, Step ←/→, Speed slider (0.5×–4×), Jump to turn #
- Export replay as JSON

---

## 9. Settings

| Setting | Options | Default |
|---------|---------|---------|
| Animation speed | Slow / Normal / Fast / Instant | Normal |
| Language | 繁體中文 / English | 繁體中文 |
| Table background | Green / Blue / Wood | Green |
| Sound effects | On / Off | On |

Persisted via `electron-store`.

---

## 10. Python Server & Data Layer

### FastAPI WebSocket Server (`backend/server/ws_server.py`)

- One GameSession per connected game
- AI turns execute automatically after human action
- Filters state to only visible info per player (opponents' hands hidden)
- Inspect/replay mode sends full state

### SQLite Schema

```sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    mode TEXT,
    started_at DATETIME,
    ended_at DATETIME,
    human_seat INTEGER,
    result TEXT
);

CREATE TABLE replay_frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT REFERENCES games(id),
    turn_number INTEGER,
    action_json TEXT,
    timestamp DATETIME
);

CREATE TABLE elo_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT REFERENCES games(id),
    elo_before INTEGER,
    elo_after INTEGER,
    recorded_at DATETIME
);
```

---

## 11. Technology Stack

| Component | Technology |
|-----------|-----------|
| Desktop shell | Electron |
| UI framework | React 18 + TypeScript |
| State management | Zustand |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| Build tool | Vite + electron-builder |
| WebSocket client | Native WebSocket API |
| Python server | FastAPI + `websockets` |
| Database | SQLite (via `aiosqlite`) |
| Settings persistence | electron-store |
| Font | Noto Sans TC (Google Fonts) |
| Package manager | pnpm (frontend), uv (backend) |

---

## 12. Milestone Mapping

| Milestone | Deliverable | Design Section |
|-----------|-------------|----------------|
| 2.1 | Electron scaffold + WebSocket connection | §1 |
| 2.2 | Game table layout (4 players, wall, discard pool) | §2 |
| 2.3 | Custom SVG tile rendering | §3 |
| 2.4 | Human player controls (draw, discard, chi/pong/kong) | §5 |
| 2.5 | 10-second turn timer | §5 |
| 2.6 | Animations (draw, discard, meld, win) | §4 |
| 2.7 | Scoring breakdown screen | §6 |
| 2.8 | Settings panel | §9 |
| 2.9 | Replay viewer | §8 |
| 2.10 | Inspect mode (AI thinking overlay) | §7 |
