# Project X — Taiwan Mahjong AI / RL System

**Version:** 0.1 (Draft)
**Date:** 2026-02-21
**Author:** Solo project
**Status:** Pre-development specification

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Goals & Success Criteria](#2-goals--success-criteria)
3. [Phases & Milestones](#3-phases--milestones)
4. [Technology Stack](#4-technology-stack)
5. [System Architecture](#5-system-architecture)
6. [Game Rules Specification — Taiwan 16-Tile Mahjong](#6-game-rules-specification--taiwan-16-tile-mahjong)
7. [Scoring System — 計台名堂 (Full Table)](#7-scoring-system--計台名堂-full-table)
8. [Game Engine Specification](#8-game-engine-specification)
9. [UI / UX Specification](#9-ui--ux-specification)
10. [AI Agent Specification](#10-ai-agent-specification)
11. [RL Training Specification](#11-rl-training-specification)
12. [Human vs AI Mode](#12-human-vs-ai-mode)
13. [Testing Strategy](#13-testing-strategy)
14. [Repository & DevOps](#14-repository--devops)
15. [Open Questions & Pending Decisions](#15-open-questions--pending-decisions)

---

## 1. Project Vision

Build a complete, faithful implementation of **Taiwan 16-Tile Mahjong (台灣16張麻將)** with a reinforcement learning AI agent that:
1. Learns Mahjong **from scratch** via self-play RL
2. Eventually reaches a level where it can **defeat a human player**
3. Is playable with a proper **desktop UI** that looks clean and professional
4. Serves as a platform for AI/ML research and experimentation

**Reference rule source:** Taiwan Mahjong Association official rules
- http://atawmj.org.tw/memu015.htm
- http://atawmj.org.tw/mjking.htm

---

## 2. Goals & Success Criteria

### Phase Goals

| Phase | Goal | Success Criteria |
|-------|------|-----------------|
| 1 | Game Engine | All Taiwan 16-tile rules implemented and unit-tested; rule-based AI can complete a full game |
| 2 | UI | Human can play a full 4-player game against 3 rule-based AI opponents in the desktop app |
| 3 | RL Training | AI trains via self-play, beats rule-based AI in >80% of games |
| 4 | Strong AI | RL AI reaches a level that consistently challenges human players |

### Definition of "Powerful AI"
- Wins against rule-based AI in ≥ 80% of sessions (measured over 1000 games)
- Human player has <40% win rate against the trained AI in a full session
- AI correctly identifies optimal discard in ≥ 75% of known benchmark positions

---

## 3. Phases & Milestones

### Phase 1 — Game Engine (Python Backend)
**Goal:** A complete, headless, fully rules-compliant Taiwan 16-tile Mahjong engine.

| Milestone | Deliverable |
|-----------|-------------|
| 1.1 | Tile set, deck, shuffle, wall (牌牆) builder |
| 1.2 | Deal (配牌), flower replacement (補花) logic |
| 1.3 | Turn engine: draw, discard, chi (吃), pong (碰), kong (槓) |
| 1.4 | Win detection (胡牌 validator): all hand shapes |
| 1.5 | Full scoring engine: all 計台名堂, 連莊/拉莊 accumulation |
| 1.6 | Game session manager: wind rotation, round tracking |
| 1.7 | Rule-based AI (greedy baseline) |
| 1.8 | Unit tests: ≥ 90% coverage on all rule logic |

### Phase 2 — Desktop UI (Electron + React + TypeScript)
**Goal:** A complete, playable 2D desktop game for Windows.

| Milestone | Deliverable |
|-----------|-------------|
| 2.1 | Electron app scaffold, WebSocket connection to Python server |
| 2.2 | Game table layout: 4 players, wall, discard pool (牌海) |
| 2.3 | Tile rendering with official Chinese characters |
| 2.4 | Human player controls (draw, discard, chi/pong/kong decisions) |
| 2.5 | 10-second turn timer for human players |
| 2.6 | Animation: tile draw, discard, chi/pong/kong reveals, win reveal |
| 2.7 | Scoring breakdown screen after each hand |
| 2.8 | Settings panel (animation speed, language toggles) |
| 2.9 | Game replay viewer |
| 2.10 | Inspect mode (4 AI playing with thinking overlay) |

### Phase 3 — RL Training Infrastructure
**Goal:** A training pipeline where AI improves through self-play.

| Milestone | Deliverable |
|-----------|-------------|
| 3.1 | RL environment wrapper (OpenAI Gym / PettingZoo interface) |
| 3.2 | PPO agent implementation in PyTorch |
| 3.3 | Action masking layer (only legal moves) |
| 3.4 | Neural network architecture for policy + value heads |
| 3.5 | Self-play loop with league-based opponent pool |
| 3.6 | Training metrics: TensorBoard reward curves, win rates, ELO ratings |
| 3.7 | Checkpoint saving & versioning |
| 3.8 | Training run on GPU (remote or local) |

### Phase 4 — Human vs AI & Polish
**Goal:** Play against a strong trained AI in a polished experience.

| Milestone | Deliverable |
|-----------|-------------|
| 4.1 | Load trained model into game server |
| 4.2 | Human vs AI mode (1 human + 3 trained AIs) |
| 4.3 | AI "thinking" display in human vs AI mode (optional overlay) |
| 4.4 | ELO tracking: human vs AI match history |
| 4.5 | Final UI polish pass |
| 4.6 | Packaged Windows installer (.exe) |

---

## 4. Technology Stack

### Backend (Game Engine + AI)
| Component | Technology | Reason |
|-----------|-----------|--------|
| Language | Python 3.11 | Best RL/ML library ecosystem |
| RL Framework | PyTorch 2.x | User preference, mature ecosystem |
| RL Algorithm | PPO (Proximal Policy Optimization) | Handles imperfect-information games, stable, battle-tested in self-play systems |
| Multi-agent | PettingZoo (AEC environment) | Standard interface for turn-based multi-agent RL |
| Training vis | TensorBoard | Standard training dashboards |
| WebSocket server | Python `websockets` or `FastAPI` + `websockets` | Real-time bidirectional game state updates |
| Serialization | JSON (game state messages) | Simple, debuggable |
| Testing | `pytest` | Unit and integration tests |

### Frontend (Desktop UI)
| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | Electron + React | Native Windows app, rich UI, TypeScript support |
| Language | TypeScript | Type safety, large ecosystem |
| Styling | Tailwind CSS or CSS Modules | Clean 2D UI styling |
| Animation | Framer Motion or CSS transitions | Smooth tile animations |
| WebSocket client | Native `WebSocket` API | Connects to Python backend |
| Build | Vite + Electron Builder | Fast build, easy Windows packaging |

### DevOps
| Component | Technology |
|-----------|-----------|
| Version control | Git + GitHub |
| CI/CD | GitHub Actions (run pytest on push) |
| Package manager (Python) | `uv` or `pip` + `requirements.txt` |
| Package manager (Node) | `npm` or `pnpm` |
| Docker | Yes — for training environment isolation |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────┐
│           Electron Desktop App               │
│  ┌──────────────────────────────────────┐   │
│  │         React UI (TypeScript)         │   │
│  │  - Game Table View                    │   │
│  │  - Player Hand View                   │   │
│  │  - Scoring Screen                     │   │
│  │  - Inspect / Replay Mode              │   │
│  │  - Settings Panel                     │   │
│  └──────────────┬───────────────────────┘   │
│                 │ WebSocket (JSON)            │
└─────────────────┼───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│           Python Game Server                 │
│  ┌──────────────────────────────────────┐   │
│  │         Game Session Manager          │   │
│  │  - Round / wind rotation              │   │
│  │  - Turn sequencer                     │   │
│  │  - Event bus (draw/discard/win etc)   │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │          Game Engine (Rules)          │   │
│  │  - Tile set, deck, wall               │   │
│  │  - Chi / Pong / Kong validator        │   │
│  │  - Win validator (all hand shapes)    │   │
│  │  - Scoring engine (台數 calculator)   │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │          AI Player Module             │   │
│  │  - Rule-based AI (baseline)           │   │
│  │  - PPO Agent (trained model)          │   │
│  │  - Action masking layer               │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │        RL Training Pipeline           │   │
│  │  - PettingZoo env wrapper             │   │
│  │  - Self-play loop                     │   │
│  │  - League / opponent pool             │   │
│  │  - TensorBoard logging                │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### WebSocket Message Protocol (simplified)
```
Client → Server:
  { "type": "action", "player": 0, "action": "discard", "tile": "9m" }
  { "type": "action", "player": 0, "action": "pong" }

Server → Client:
  { "type": "state",  "game_state": { ... full game state ... } }
  { "type": "event",  "event": "win", "player": 2, "hand": [...], "score": [...] }
  { "type": "request","player": 0, "options": ["discard", "pong", "pass"] }
```

---

## 6. Game Rules Specification — Taiwan 16-Tile Mahjong

### 6.1 Basic Setup

| Parameter | Value |
|-----------|-------|
| Players | 4 |
| Tiles per hand | 16 (dealer starts with 17) |
| Total tile sets | 4 sets of 34 unique tiles = 136 tiles + 8 flower tiles = **144 tiles** |
| Wind rotation | Full 4-wind game (East → South → West → North) |
| Rounds per wind | Each player deals once per wind circle = 4 rounds per wind |
| Max consecutive dealer streaks | Each 連莊 adds 1 拉莊 台; no hard cap on streaks |
| Draw (荒局) | Dealer continues (連莊); draw counts as 連莊 for 連/拉莊 accumulation |
| Remaining wall tiles | Last 8 stacks (16 tiles) reserved as 殘牌 (鐵八墩), not drawn in normal play |

### 6.2 Tile Set

**Number tiles (數牌):** 144 tiles total
- 萬子 (Characters): 1–9, × 4 copies each = 36 tiles
- 筒子 (Circles): 1–9, × 4 copies each = 36 tiles
- 索子 (Bamboo): 1–9, × 4 copies each = 36 tiles

**Honor tiles (字牌):** 28 tiles total
- Wind tiles (風牌): East東, South南, West西, North北 × 4 copies each = 16 tiles
- Dragon tiles (箭牌): Red中, Green發, White白 × 4 copies each = 12 tiles

**Flower tiles (花牌):** 8 tiles total (1 copy each)
- Season set (季節): 春(1), 夏(2), 秋(3), 冬(4)
- Plant set (花草): 梅(1), 蘭(2), 竹(3), 菊(4)

**Total: 144 + 8 = 152 tiles**

### 6.3 Game Flow

```
1. 搬風 (Wind Assignment) — dice roll assigns seats
2. 定莊 (Determine Dealer) — dice roll within the wind
3. 洗牌 (Shuffle)
4. 砌牌 (Build Wall) — 18 stacks per player, 2 tiles high
5. 配牌 (Deal) — 4 rounds × 4 tiles each; dealer takes extra tile → 17 tiles
6. 補花 (Flower Replacement) — in order starting from dealer
7. 行牌 (Play) — counter-clockwise turns
   - Draw (摸牌) / Chi (吃) / Pong (碰) / Kong (槓)
   - Discard (捨牌)
   - Win declaration check (胡牌?)
8. End of hand — score, rotate dealer or continue streak
9. After all winds — game ends, final scoring
```

### 6.4 Turn Actions

| Action | Trigger | Condition |
|--------|---------|-----------|
| 摸牌 Draw | Own turn | Draw from wall head (牆頭) |
| 吃牌 Chi | Left player discards | Form a sequence with 2 tiles in hand |
| 碰牌 Pong | Any player discards | Have a pair of the same tile |
| 明槓 Open Kong | Any player discards (碰槓) or after existing pong (加槓) | Have 4 of the same tile available |
| 暗槓 Concealed Kong | After drawing | Have all 4 matching tiles in hand |
| 補花 Draw replacement | After drawing a flower | Mandatory; draw from 槓尾 (back of wall) |
| 捨牌 Discard | End of own draw turn or after chi/pong | Choose 1 tile from hand |
| 胡牌 Win | On any valid incoming tile | Hand meets win condition |

### 6.5 Win Conditions

A valid winning hand must be one of:
- **Standard**: 5 complete sets (sequences or triplets/quads) + 1 pair (將眼)
- ~~**Special: 嚦咕嚦咕**~~ — **excluded from this game**
- **Flower Win: 八仙過海**: All 8 flower tiles collected
- **Flower Win: 七搶一**: Hold 7 flowers, steal the 8th from another player

### 6.6 Priority Rules (行牌優先權)
1. Win (胡牌) > Pong/Kong (碰/槓) > Chi (吃) > Draw (摸牌)
2. If multiple players declare win (攔胡): player closest counter-clockwise from discarder wins first
3. Special cases: see official rule source for edge cases involving early grabs

### 6.7 Dealer Continuation (連莊/拉莊)
- Dealer wins → 連莊 (dealer continues, streak count +1)
- Draw (荒局) → 連莊 (dealer continues, streak count +1)
- Dealer loses → 下莊 (dealer passes counter-clockwise)

**Streak scoring for n consecutive dealer rounds (連N):**
- 作莊: 1台 (dealer bonus, every hand)
- 連莊: n × 1台 (accumulates each streak)
- 拉莊: n × 1台 (閒家 ALL pay; accumulates each streak)

**Example — 3連莊:**
- 作莊 = 1台
- 連莊 = 3台
- 拉莊 = 3台
- **Extra台 on top of hand score = 7台**

Note: 連莊 marker displayed by dice in front of dealer. If marker shows lower than actual streak, use marker amount when dealer wins; use actual streak when dealer loses. Vice versa if marker shows higher.

---

## 7. Scoring System — 計台名堂 (Full Table)

### 7.1 Base Rules
- All applicable 台數 are **additive** (累計)
- Exception: if two scoring hands **necessarily co-exist** (必然並存), only the **higher-value one** counts
- A **底 (base bet)** is the unit of exchange. 1台 = 1 point value per bottom (exact point/NTD value TBD)
- Cap: **81台 maximum** per winning hand
- 自摸: winner collects from all 3 players
- 放槍 (胡銃): discarder pays the full amount; other 2 players pay nothing (standard rule)

### 7.2 Complete 計台名堂 Table

#### 1台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 作莊 | 1 | Dealer bonus — applies whenever dealer wins OR is the discarder |
| 連莊 | n | n consecutive dealer rounds (n台, accumulated) |
| 拉莊 | n | All players pay n台 extra when dealer is on streak |
| 門清 | 1 | No chi, pong, or open kong before winning (concealed kong allowed) |
| 自摸 | 1 | Win by self-draw |
| 風牌 (開門風) | 1 | Triplet of own seat wind tile |
| 風圈 (圈風) | 1 | Triplet of current round wind tile (stacks with 開門風 if same) |
| 箭字坎 (中/發/白) | 1 | Triplet of any dragon tile (中, 發, 白) |
| 花牌 (自家花) | 1 per tile | Each flower tile matching own seat direction |
| 搶槓 | 1 | Own winning tile is a tile another player adds to an existing pong (加槓) |
| 獨聽 | 1 | Waiting on exactly 1 unique tile (edge wait 站壁, center wait 中洞, single pair 單釣) |
| 半求 | 1 | Only 1 concealed tile left (all others chi/ponged), win by self-draw (includes 獨聽 — total 3台 with 自摸) |
| 槓上開花 | 1 | Win on the supplement tile drawn after a kong or flower (+ 自摸 1台) |
| 海底撈月 | 1 | Win by self-drawing the last available wall tile (+ 自摸 1台) |
| 河底撈魚 | 1 | Win off the last discarded tile |

#### 2台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 不求 (+ 自摸) | 2 | No chi/pong/open kong AND win by self-draw (門清一摸三 = 門清1 + 不求自摸2 = 3台 total) |
| 平胡 | 2 | 5 sequences + 1 pair; all number tiles; no 獨聽; no 自摸; two-sided wait |
| 全求 | 2 | All tiles chi/ponged, one tile left, win by discard (+ 獨聽 1台 = 3台 total) |
| 花槓 | 2 | Own flower group fully collected (春夏秋冬 or 梅蘭菊竹 complete set of 4) |
| 三暗坎 | 2 | 3 concealed triplets (including concealed kongs) |

#### 4台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 地聽 | 4 | Tenpai declared after first discard (門清 required, not counted separately); can add 自摸 |
| 對對胡 (碰碰胡) | 4 | All triplets + 1 pair |
| 小三元 | 4 | 2 dragon triplets + 1 dragon pair (箭字坎 not added separately; 圈風 adds if applicable) |
| 湊一色 (混一色) | 4 | All tiles one suit + honor tiles mixed |

#### 5台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 四暗坎 | 5 | 4 concealed triplets (including concealed kongs) |

#### 6台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 四暗坎 (alt) | 6 | Per mjking.htm source — check exact value during implementation; TBD |

#### 8台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 天聽 | 8 | Tenpai immediately after deal + flower draw; can add 不求自摸; cannot add 門清 |
| 五暗坎 | 8 | 5 concealed triplets (門清 and 對對胡 not counted; 不求自摸 can add) |
| 大三元 | 8 | All 3 dragon triplets (箭字坎 not counted separately; 圈風 adds if applicable) |
| 小四喜 | 8 | 3 wind triplets + 1 wind pair (圈風/開門風 adds if applicable) |
| 清一色 | 8 | All tiles same number suit (no honors) — per memu015 source |
| ~~嚦咕嚦咕~~ | ~~8~~ | **Excluded from this game** |
| 七搶一 | 8 | Hold 7 flowers, steal 8th from another player (花胡 variant) |
| 八仙過海 | 8 | Collect all 8 flower tiles (花胡 variant; payer: all 3 players) |

#### 12台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 清一色 | 12 | All tiles same number suit — per mjking.htm source |
| 配牌花胡 | 12 | Dealt all 8 flowers at start (天胡 variant for flowers) |

#### 16台 Hands

| Name | 台 | Description |
|------|-----|-------------|
| 天胡 | 16 | Dealer wins immediately after deal + flower draw (門清一摸三 not counted) |
| 地胡 | 16 | Non-dealer draws first tile after 天聽, wins by self-draw (不求自摸 can add) |
| 人胡 | 16 | Non-dealer on 天聽, wins off first discard of any player (= 天聽一發) |
| 大四喜 | 16 | All 4 wind triplets (圈風/開門風 not counted; other hands can add) |
| 清一色 (per mjking) | 12 | See note above — source discrepancy, TBD final value |
| 字一色 | 16 | All honor tiles (對對胡 not counted; dragon/wind hands add as applicable) |
| 五暗坎 | 16 | Per mjking.htm — source discrepancy; TBD final value |

> **Authoritative source: memu015.htm** is the canonical scoring reference for this project.
> - 清一色 = **8台**
> - 五暗坎 = **8台**
> - 四暗坎 = **5台**
> - 嚦咕嚦咕 is **excluded** from this game.

### 7.3 Authoritative 台數 Values (Locked)

| Hand | 台數 (Final) | Source |
|------|------------|--------|
| 清一色 | 8台 | memu015 |
| 五暗坎 | 8台 | memu015 |
| 四暗坎 | 5台 | memu015 |
| 嚦咕嚦咕 | **Excluded** | — |
| All others | Per memu015 table | memu015 |

### 7.4 花牌 Scoring Summary

| Situation | 台數 |
|-----------|------|
| 1 flower tile matching own seat | 1台 |
| Complete group of 4 (花槓: 春夏秋冬 or 梅蘭菊竹) | 2台 |
| All 8 flower tiles (八仙過海) | 8台 |
| Dealt all 8 flowers at start (配牌花胡) | 12台 |

### 7.5 Payment Model

| Win type | Who pays |
|----------|---------|
| 自摸 (self-draw) | All 3 other players each pay full 台數 |
| 胡銃 (win off discard) | Only the discarder pays full 台數 |
| 八仙過海 / 七搶一 | All 3 players each pay full 台數 |

**底注 system:** 1底 = 1 abstract point. No real-money NTD value. Scoring display shows points only.

Other special payment rules (包賠, 代位賠付) follow memu015 official rule source exactly.

**插花 (side bets): Out of scope. Not implemented.**

---

## 8. Game Engine Specification

### 8.1 Core Data Structures (Python)

```python
# Tile representation
Tile = str  # e.g. "1m"=1萬, "9p"=9筒, "5s"=5索,
            #      "E"=東, "S"=南, "W"=西, "N"=北
            #      "C"=中, "F"=發, "B"=白(白板)
            #      "f1"-"f4"=春夏秋冬, "f5"-"f8"=梅蘭菊竹

# Player state
@dataclass
class PlayerState:
    seat: int              # 0=East, 1=South, 2=West, 3=North (relative to round)
    hand: List[Tile]       # Concealed tiles (16 or 17)
    melds: List[Meld]      # Exposed sets (chi/pong/open kong)
    flowers: List[Tile]    # Collected flower tiles
    discards: List[Tile]   # This player's discard history
    kongs: List[Meld]      # Concealed kongs
    is_dealer: bool
    streak: int            # Current consecutive dealer streak

# Game state
@dataclass
class GameState:
    players: List[PlayerState]
    wall: List[Tile]               # Remaining wall tiles
    discard_pool: List[Tile]       # All discarded tiles (海/牌池)
    current_player: int
    round_wind: str                # E/S/W/N — current wind circle
    round_number: int              # Which round within the wind
    last_discard: Optional[Tile]
    last_action: Optional[Action]
    phase: str                     # "deal", "play", "win", "draw"
```

### 8.2 Win Validator

The win validator must handle:
- Standard 5-set + 1-pair decomposition (all possible interpretations)
- 嚦咕嚦咕 (7 pairs + 1 triplet)
- 花胡 (flower win: 八仙過海, 七搶一)
- 天胡 / 地胡 / 人胡 edge cases
- Handling of 相公 (invalid hand due to violations)

### 8.3 Scoring Engine

```
score = sum of all applicable 計台名堂
      + 作莊 (if dealer)
      + 連莊 × streak_count
      + 拉莊 × streak_count (added to all payers)
capped at 81台
```

### 8.4 Action Space (per turn)

```
General:
  DRAW          — draw from wall
  DISCARD(tile) — discard a tile (16 possible tiles × positions)
  CHI(tile, combo) — chi with specific sequence
  PONG          — pong
  OPEN_KONG     — open kong (from discard or add kong)
  CONCEALED_KONG(tile) — concealed kong
  WIN           — declare win
  PASS          — decline optional action (chi/pong/kong opportunity)
```

### 8.5 Rule-Based AI (Baseline)

The greedy rule-based AI will:
1. **Discard strategy**: Discard tile that minimizes "向聽數" (shanten number — tiles away from tenpai)
2. **Meld strategy**: Accept chi/pong/kong if it reduces shanten number
3. **No bluffing or strategic deception** (pure greedy)
4. Used in **Phase 1 testing** and as **initial training opponent** in RL Phase 3

---

## 9. UI / UX Specification

### 9.1 Layout

```
┌────────────────────────────────────────────────┐
│  [Round Info]   [Wind]   [Dealer]   [Timer]     │
│                                                  │
│          ┌──── North Player ────┐               │
│          │  [Face-down tiles]   │               │
│          │  [Melds]  [Flowers]  │               │
│          └──────────────────────┘               │
│  West    │                      │  East         │
│  Player  │    Discard Pool      │  Player       │
│  [tiles] │    (牌海/牌池)        │  [tiles]      │
│          │                      │               │
│          └──────────────────────┘               │
│          ┌──── South Player ────┐               │
│          │  [YOUR hand tiles]   │               │
│          │  [Action buttons]    │               │
│          └──────────────────────┘               │
│  [Game Log]              [Settings]  [Replay]   │
└────────────────────────────────────────────────┘
```

### 9.2 Tile Style
- **2D tiles drawn in CSS/SVG** — no external tile image assets
- Official Traditional Chinese characters rendered with web fonts
- Color coding: 萬=red/gold characters, 筒=blue circles, 索=green bamboo, 字牌=dark background
- Flower tiles: soft green/yellow background with Chinese character
- Tile face: white/cream background, rounded corners, subtle drop shadow
- Tile back (opponent hand): uniform dark pattern (e.g., dark green with subtle grid)

### 9.3 Game Modes

| Mode | Description |
|------|-------------|
| **Human vs AI (Easy)** | 1 human (random seat) + 3 rule-based greedy AI opponents. 10-sec turn timer. |
| **Human vs AI (Hard)** | 1 human (random seat) + 3 trained RL AI opponents. 10-sec turn timer. |
| **Inspect Mode** | 4 AI players. All 4 hands visible face-up. AI thinking overlay on each player. Auto-plays at set speed with pause/step-forward/step-back controls. Human observes only. |
| **Training Mode** | Headless (no UI). Python backend only. Used for RL self-play training. |

### 9.4 Inspect Mode — Controls & AI Thinking Overlay

**Playback controls:**
- ▶ Play / ⏸ Pause button
- ⏭ Step Forward (advance one action)
- ⏮ Step Backward (undo one action in view)
- Speed slider: 0.5× / 1× / 2× / 4×
- Jump to specific turn number

**AI thinking overlay per player:**
- **Win probability** (estimated % based on current hand)
- **Shanten number** (how many tiles away from tenpai)
- **Top-3 discard candidates** (highlighted tiles with scores)
- **Waiting tiles** (if in tenpai: which tiles complete the hand)
- **Tile tracker** (which tiles are dead / still live in wall)

### 9.5 Turn Timer
- Human player turn: **10-second countdown** displayed visually
- On timeout: **auto-discard** the most recently drawn tile
- Timer pauses during win/chi/pong/kong decision windows

### 9.6 Animations
| Event | Animation |
|-------|-----------|
| Tile draw | Tile slides from wall to hand |
| Discard | Tile flips/slides to discard pool |
| Chi / Pong | Tiles flip face-up, move to meld area |
| Kong | 4 tiles arrange into kong display |
| Win | Hand tiles fan out dramatically; scoring table rises |
| Flower draw | Flower tile floats to flower area; replacement tile draws |

### 9.7 Post-Hand Scoring Screen
- Shows full winning hand layout
- Lists every applicable 計台名堂 entry with 台數
- Shows total 台數 (capped at 81)
- Shows 底注 calculation
- Shows payment breakdown per player

### 9.8 Replay Viewer
- Step forward / backward through any completed game
- Shows all 4 hands (hidden during live play, revealed in replay)
- Shows AI thinking data if available at each decision point
- Export replay to JSON file

### 9.9 Settings Panel
- Animation speed: Slow / Normal / Fast / Instant
- Language toggle: 繁體中文 (default) / English
- Wind indicator style preference
- Table background color/texture

### 9.10 Game Log Panel
- Shows last N actions in the current hand (scrollable)
- Format: `[西家] 打出 5萬`, `[南家] 碰 7筒`, `[東家] 自摸 8索 (7台)`

---

## 10. AI Agent Specification

### 10.1 Architecture

**Algorithm:** Proximal Policy Optimization (PPO) with self-play

**Neural network (Policy + Value):**
```
Input:
  - Own hand (tile encoding vector)
  - Own melds (publicly known)
  - Own flowers
  - Discard pool (all visible tiles, 全牌追蹤)
  - Each opponent's melds and flowers (public info)
  - Each opponent's discard history (public info)
  - Round wind, seat wind, dealer status, streak count
  - Current legal actions (action mask)
  - Turn count, tiles remaining in wall

Network:
  - Feature encoder (MLP or Transformer for tile sequences)
  - Policy head → probability distribution over legal actions
  - Value head → estimated game value (expected reward)

Output:
  - Action distribution (masked to legal moves only)
  - State value estimate
```

### 10.2 Action Masking

At every decision point, a binary mask is applied over the full action space. Actions not currently legal are set to -inf before softmax. This guarantees:
- AI never makes an illegal move
- Exploration focuses only on valid plays
- Training efficiency dramatically improved

### 10.3 Observation Space

The AI observes only **information visible to that player** (imperfect information):
- Own concealed hand (full)
- All exposed melds of all players (public)
- All discard histories (public)
- Flowers of all players (public)
- Wall size (public)
- Which tiles are "dead" (discarded / in melds) → infer opponent hand possibilities

### 10.4 League-Based Self-Play

To prevent cycling and overfitting to one strategy:
1. Maintain a **pool of historical model checkpoints**
2. New model trains against a **random mix** of:
   - Current model (self-play)
   - Recent checkpoints (e.g., last 10 saved versions)
   - Rule-based AI (early training)
3. Periodically evaluate all models in the pool via tournament → update **ELO ratings**
4. Remove weakest models from pool to keep pool size bounded

### 10.5 Reward Function

| Event | Reward |
|-------|--------|
| Win hand | + (total 台數 won) |
| Lose hand (放槍) | − (total 台數 paid) |
| Lose hand (自摸 by others) | − (total 台數 paid) |
| Draw (荒局) | 0 (no payment in draw) |
| Intermediate | 0 (no intermediate shaping initially) |

Reward is based on **actual 計台名堂 score** to incentivize the agent to pursue high-value hands, not just any win.

### 10.6 Model Checkpointing
- Save checkpoint every N training episodes (N = TBD based on training speed)
- Checkpoint metadata: episode count, ELO rating, win rate vs. rule-based AI, win rate vs. pool
- Keep last 20 checkpoints; always keep "best ELO" checkpoint
- Training log exported to TensorBoard

### 10.7 Tile Tracking / Opponent Modeling
The AI input includes the full history of visible tiles, enabling it to learn:
- Which tiles are "dead" (cannot be drawn)
- Which tiles opponents are likely holding based on their pong/chi/discard behavior
- Danger assessment: whether a discard may let an opponent win

---

## 11. RL Training Specification

### 11.1 Environment Interface

Using **PettingZoo AEC (Agent-Environment Cycle)** format:
- Turn-based: agents act one at a time
- `observation_space`: encoded game state visible to current agent
- `action_space`: Discrete(N) — full action space (masked at runtime)
- `reward`: delta score from the completed hand

### 11.2 Training Loop

```
Phase A — Warm-up (Rule-based opponents):
  - AI trains against 3 rule-based AI opponents
  - Goal: learn basic hand completion, discard logic
  - Stop when AI win rate vs. rule-based > 50%

Phase B — Self-play (League):
  - All 4 seats filled by AI agents from pool
  - League-based opponent sampling
  - ELO tracking begins
  - Continue until ELO plateaus or target win rate vs. human achieved

Phase C — Fine-tuning (Optional):
  - Human game data / expert play data for supervised pre-training boost
  - Not planned initially; optional future enhancement
```

### 11.3 Hardware

- **Development / testing:** CPU (local Windows machine)
- **Full training:** Remote GPU machine on **same LAN, accessed via SSH**
- Docker image includes: Python 3.11, PyTorch 2.x (CUDA), PettingZoo, training scripts
- Workflow:
  1. Push code to GitHub
  2. SSH into remote GPU machine, pull latest code
  3. Run training in Docker container
  4. Sync checkpoints back to local machine via `scp` or shared network folder

### 11.4 Training Metrics (TensorBoard)

| Metric | Description |
|--------|-------------|
| Mean episode reward | Average total score per game session |
| Win rate vs. rule-based AI | Evaluated every 1000 episodes |
| Win rate vs. pool | Tournament results |
| ELO rating over time | Model strength curve |
| Mean hand value on win | Average 台數 when winning |
| Policy entropy | Ensures sufficient exploration |
| Value loss / policy loss | Standard PPO diagnostics |

### 11.5 Hyperparameters (Initial — to be tuned)

| Parameter | Initial Value |
|-----------|--------------|
| Learning rate | 3e-4 |
| Clip ratio (ε) | 0.2 |
| Discount (γ) | 0.99 |
| GAE λ | 0.95 |
| Batch size | 2048 |
| Mini-batch size | 256 |
| PPO epochs per update | 10 |
| Entropy coefficient | 0.01 |

---

## 12. Human vs AI Mode

### 12.1 Game Setup
- Human player assigned a **random seat** at game start
- 3 seats filled by the **current best checkpoint** of the trained AI
- Game follows standard Taiwan 16-tile rules

### 12.2 Human Player Controls
| Action | UI Element |
|--------|-----------|
| Discard | Click tile in hand → tile highlights → confirm discard |
| Chi | Pop-up action panel with sequence options |
| Pong | Pop-up button: "碰" (highlighted available) |
| Kong | Pop-up button: "槓" |
| Win | Pop-up button: "胡" (only shown when legally valid) |
| Pass | Pop-up button: "過" (decline optional action) |

### 12.3 Timer
- 10-second countdown shown as a progress bar during human's turn
- Audible soft tick in the last 3 seconds (if sound enabled)
- Auto-discard on timeout: most recently drawn tile is discarded

### 12.4 ELO Tracking (Human vs AI)
- Each full game session records win/draw/loss for human
- Human ELO starts at 1200 (standard starting ELO)
- AI ELO carried over from training pool rating
- Match history stored locally (JSON or SQLite)

---

## 13. Testing Strategy

### 13.1 Unit Tests (pytest)

| Test Category | Coverage Target |
|--------------|----------------|
| Tile set construction | 100% |
| Wall build & shuffle | 100% |
| Deal logic (配牌/補花) | 100% |
| Win validator (all hand shapes) | 100% |
| Scoring engine (all 計台名堂) | 100% |
| Chi/Pong/Kong validators | 100% |
| Action masking | 100% |
| Game session state machine | ≥ 90% |
| RL environment step correctness | ≥ 90% |

### 13.2 Integration Tests
- Full game simulation: 10,000 random games complete without error
- Rule-based AI vs rule-based AI: verify game terminates without illegal states
- Scoring consistency: replay known hands from the official rule source, verify exact 台數 match

### 13.3 Regression Tests
- Any scoring rule change must be accompanied by regression test for that rule
- Win validator tested against all example hands in the official rule source

---

## 14. Repository & DevOps

### 14.1 Repository Structure

```
mahjong-project-x/
├── backend/                    # Python — game engine + AI
│   ├── engine/
│   │   ├── tiles.py            # Tile definitions, encodings
│   │   ├── wall.py             # Wall building, shuffle
│   │   ├── deal.py             # Deal, flower replacement
│   │   ├── actions.py          # Action types, validators
│   │   ├── win_validator.py    # Winning hand detector
│   │   ├── scorer.py           # 計台名堂 scoring engine
│   │   └── game_session.py     # Game session state machine
│   ├── ai/
│   │   ├── rule_based.py       # Greedy rule-based baseline AI
│   │   ├── ppo_agent.py        # PPO agent
│   │   ├── network.py          # Neural network architecture
│   │   └── tile_tracker.py     # Tile tracking / opponent model
│   ├── training/
│   │   ├── env.py              # PettingZoo AEC environment
│   │   ├── self_play.py        # Self-play + league loop
│   │   ├── train.py            # Main training entry point
│   │   └── evaluate.py         # ELO evaluation tournament
│   ├── server/
│   │   └── ws_server.py        # WebSocket game server
│   ├── tests/
│   │   ├── test_tiles.py
│   │   ├── test_win_validator.py
│   │   ├── test_scorer.py
│   │   └── test_game_session.py
│   ├── requirements.txt
│   └── Dockerfile              # GPU training environment
│
├── frontend/                   # TypeScript — Electron + React UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── GameTable.tsx
│   │   │   ├── PlayerHand.tsx
│   │   │   ├── DiscardPool.tsx
│   │   │   ├── ScoringScreen.tsx
│   │   │   ├── InspectOverlay.tsx
│   │   │   └── ReplayViewer.tsx
│   │   ├── hooks/
│   │   │   └── useGameSocket.ts
│   │   ├── store/
│   │   │   └── gameStore.ts
│   │   └── App.tsx
│   ├── electron/
│   │   └── main.ts
│   ├── package.json
│   └── tsconfig.json
│
├── checkpoints/                # Saved AI model checkpoints
├── replays/                    # Saved game replays (JSON)
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions: run pytest on push
├── project-X.md               # This document
└── README.md                  # Setup + run instructions
```

### 14.2 GitHub Actions CI

On every push to `main` or pull request:
1. Setup Python 3.11
2. Install dependencies (`pip install -r requirements.txt`)
3. Run `pytest backend/tests/ --cov=backend/engine --cov-report=term`
4. Fail if any test fails

### 14.3 Open Source
- Repository: public GitHub
- License: MIT
- No proprietary tile assets — use open-source or self-drawn tile graphics

---

## 15. Resolved Decisions

| # | Question | Decision |
|---|---------|----------|
| 1 | Point value of 1 底? | **1底 = 1 abstract point (no NTD)** |
| 2 | Include 嚦咕嚦咕? | **No — excluded** |
| 3 | 清一色 台數 source? | **8台 (memu015)** |
| 4 | 四暗坎/五暗坎 values? | **5台 / 8台 (memu015)** |
| 5 | 天聽/地聽 台數? | **8台 / 4台 (memu015)** |
| 6 | Inspect mode playback? | **Auto-play + pause/step controls (both)** |
| 7 | Tile art source? | **CSS/SVG drawn in code** |
| 8 | GPU training method? | **Remote GPU via LAN/SSH + Docker** |
| 9 | Difficulty modes? | **Easy = rule-based AI; Hard = trained RL AI** |
| 10 | 插花 side bets? | **Out of scope — not implemented** |

## 16. Still Open

| # | Question | Status |
|---|---------|--------|
| 1 | Window size / resolution for the desktop app? | ❓ Pending |
| 2 | Replay viewer: manual step-by-step or speed-adjustable playback? | ❓ Pending |
| 3 | ELO/replay storage: SQLite or flat JSON? | ❓ Pending |

---

*This document is a living specification. All sections marked ❓ will be resolved before implementation of the relevant phase begins.*

*Last updated: 2026-02-21*
