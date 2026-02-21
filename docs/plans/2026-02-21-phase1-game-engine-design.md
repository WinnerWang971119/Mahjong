# Phase 1 — Game Engine Design

**Date:** 2026-02-21
**Phase:** 1 — Python Game Engine
**Status:** Approved

---

## Summary

Build a complete, headless, rules-compliant Taiwan 16-tile Mahjong engine in Python. No UI, no WebSocket server. The engine must pass ≥ 90% test coverage (100% on core rule modules) and support a greedy rule-based AI capable of completing full games.

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| Package manager | `uv` + `pyproject.toml` |
| WebSocket server | Deferred to Phase 2 |
| 嚦咕嚦咕 hand | **Excluded** |
| Shanten calculator | Implemented from scratch |
| Implementation approach | Sequential milestone-by-milestone (A) |
| 七搶一 payment | Only the player whose flower was stolen pays |
| Scoring authority | memu015 (清一色=8台, 五暗坎=8台, 四暗坎=5台) |

---

## Repository Structure

```
Mahjong/                          ← repo root
├── backend/
│   ├── engine/
│   │   ├── tiles.py              # Tile constants, encodings, helpers
│   │   ├── wall.py               # Wall construction, shuffle
│   │   ├── deal.py               # Deal + flower replacement
│   │   ├── actions.py            # Action types + validators (chi/pong/kong)
│   │   ├── win_validator.py      # Win detection (standard + flower wins)
│   │   ├── scorer.py             # 計台名堂 scoring engine
│   │   └── game_session.py       # Full game state machine
│   ├── ai/
│   │   ├── shanten.py            # Shanten number calculator (from scratch)
│   │   └── rule_based.py         # Greedy baseline AI
│   ├── tests/
│   │   ├── test_tiles.py
│   │   ├── test_wall.py
│   │   ├── test_deal.py
│   │   ├── test_actions.py
│   │   ├── test_win_validator.py
│   │   ├── test_scorer.py
│   │   └── test_game_session.py
│   └── pyproject.toml
├── docs/
│   └── plans/
│       └── 2026-02-21-phase1-game-engine-design.md
├── project-X.md
└── README.md
```

---

## Core Data Structures

```python
# tiles.py
Tile = str
# number tiles: "1m"–"9m" (萬), "1p"–"9p" (筒), "1s"–"9s" (索)
# honors:       "E","S","W","N" (winds), "C","F","B" (dragons: 中/發/白)
# flowers:      "f1"–"f4" (seasons 春夏秋冬), "f5"–"f8" (plants 梅蘭菊竹)

FULL_DECK: list[Tile]   # 144 tiles (136 normal + 8 flower tiles excluded from main deck)
FLOWERS: list[Tile]     # 8 flower tiles

# actions.py
@dataclass
class Meld:
    type: Literal["chi", "pong", "open_kong", "concealed_kong", "added_kong"]
    tiles: list[Tile]           # 3 or 4 tiles forming the meld
    from_player: int | None     # which player the stolen tile came from (None = concealed)

@dataclass
class PlayerState:
    seat: int                   # 0=East, 1=South, 2=West, 3=North (relative)
    hand: list[Tile]            # concealed tiles (16 or 17)
    melds: list[Meld]           # exposed melds
    flowers: list[Tile]         # collected flower tiles
    discards: list[Tile]        # this player's discard history
    is_dealer: bool
    streak: int                 # consecutive dealer rounds

@dataclass
class GameState:
    players: list[PlayerState]
    wall: list[Tile]            # main wall (draw from head)
    wall_back: list[Tile]       # 槓尾 back wall (for kong/flower replacement draws)
    reserved: list[Tile]        # 殘牌 (last 16 tiles, never drawn)
    discard_pool: list[Tile]    # all discarded tiles (牌海)
    current_player: int
    round_wind: str             # "E" / "S" / "W" / "N"
    round_number: int           # which round within the wind circle
    dealer_index: int
    last_discard: Tile | None
    last_action: str | None
    phase: str                  # "deal" | "flower_replacement" | "play" | "win" | "draw"
    tenpai_flags: dict[int, bool]  # for 天聽/地聽/人胡 detection
```

---

## Milestones

### 1.1 — Tile Set, Deck, Wall

**File:** `engine/tiles.py`, `engine/wall.py`

- Define all 144 tiles as string constants
- `build_full_deck()` → returns 144-tile list (4× each normal tile)
- `build_flower_set()` → 8 flower tiles
- `shuffle_and_build_wall(deck)` → shuffled deck split into 18 stacks per player
- `reserve_tiles(wall)` → pop last 16 tiles as 殘牌 (鐵八墩)
- Tests: deterministic deck size, correct tile counts, no missing/extra tiles

### 1.2 — Deal + Flower Replacement

**File:** `engine/deal.py`

- `deal_initial_hands(wall)` → 4 rounds × 4 tiles; dealer gets +1 → 17 tiles
- `flower_replacement(players, wall_back)` → in dealer-first order, replace flowers with draws from 槓尾; recurse if replacement is also a flower
- `check_peipai_flower_hu(player)` → detect 配牌花胡 (dealt all 8 flowers)
- Tests: hand sizes correct, flowers moved to flower area, wall_back shrinks correctly

### 1.3 — Turn Engine: Actions & Validators

**File:** `engine/actions.py`

- Action types: `DRAW`, `DISCARD(tile)`, `CHI(tile, combo)`, `PONG`, `OPEN_KONG`, `ADDED_KONG`, `CONCEALED_KONG(tile)`, `WIN`, `PASS`
- `get_legal_actions(game_state, player_idx)` → returns list of legal `Action` objects
- `validate_chi(hand, discard)` → returns valid sequence combinations
- `validate_pong(hand, discard)` → True/False
- `validate_open_kong(hand, discard)` → True/False
- `validate_added_kong(melds, drawn_tile)` → True/False (extend existing pong)
- `validate_concealed_kong(hand, tile)` → True/False
- Priority enforcement: Win > Pong/Kong > Chi > Draw
- 攔胡 (multiple win declarations): closest counter-clockwise from discarder wins
- Tests: 100% coverage on all validator functions

### 1.4 — Win Validator

**File:** `engine/win_validator.py`

- `is_winning_hand(hand, melds, flowers, win_tile, game_state, player_idx)` → `WinResult | None`
- Standard decomposition: backtracking with memoization, tries all valid `5 sets + 1 pair` decompositions of concealed tiles + melds
- Flower wins:
  - `八仙過海`: player holds all 8 flowers → immediate win
  - `七搶一`: player holds 7 flowers + claims 8th from another player's kong supplement
- 天胡: dealer wins immediately after deal + flower replacement (flagged by session manager)
- 地胡: non-dealer draws first tile after 天聽, wins by self-draw
- 人胡: non-dealer on 天聽, wins off first discard
- 相公: hand flagged invalid → validator always returns None for this player
- Tests: 100% coverage; test all hand shapes including edge waits (站壁, 中洞, 單釣)

### 1.5 — Scoring Engine

**File:** `engine/scorer.py`

```
score_hand(game_state, winner_idx, win_tile, win_type, hand_decomp) -> ScoringResult

ScoringResult:
  yaku: list[tuple[str, int]]   # [("門清", 1), ("自摸", 1), ...]
  subtotal: int
  total: int                     # min(subtotal, 81)
  payments: dict[int, int]       # player_idx → points they pay (positive = they pay)
```

All 計台名堂 implemented per memu015 (authoritative):

**1台:** 作莊, 連莊(n), 拉莊(n), 門清, 自摸, 風牌(開門風), 風圈(圈風), 箭字坎×3, 花牌(自家花)×1台each, 搶槓, 獨聽, 半求, 槓上開花, 海底撈月, 河底撈魚
**2台:** 不求(+自摸), 平胡, 全求, 花槓, 三暗坎
**4台:** 地聽, 對對胡, 小三元, 湊一色
**5台:** 四暗坎
**8台:** 天聽, 五暗坎, 大三元, 小四喜, 清一色, 七搶一, 八仙過海
**12台:** 配牌花胡
**16台:** 天胡, 地胡, 人胡, 大四喜, 字一色

Mutual exclusion rules (only higher yaku counts when necessarily co-existing):
- 五暗坎 subsumes 門清, 對對胡
- 大三元 subsumes 箭字坎×3
- 大四喜 subsumes 開門風, 圈風
- 字一色 subsumes 對對胡

Payment model:
| Win type | Who pays |
|----------|---------|
| 自摸 | All 3 other players each pay full 台數 |
| 胡銃 (off discard) | Only the discarder pays |
| 八仙過海 | All 3 players each pay |
| 七搶一 | Only the player whose flower was stolen pays |

Cap: 81台 maximum. Tests: 100% coverage; verified against all named hands in memu015.

### 1.6 — Game Session Manager

**File:** `engine/game_session.py`

- State machine managing full game lifecycle:
  1. 搬風/定莊 (wind + dealer assignment via dice)
  2. 洗牌/砌牌 (shuffle, build wall)
  3. 配牌 (deal)
  4. 補花 (flower replacement)
  5. 行牌 loop (turn-by-turn play)
  6. Hand end: score, determine 連莊 or 下莊
  7. Wind rotation after all 4 players have dealt
  8. Game end after all 4 winds
- API: `GameSession.step(action: Action) -> GameState`
- Exposes `get_legal_actions(player_idx)` for AI/UI consumption
- Tracks 天聽 flags after deal phase for 天胡/地胡/人胡 detection
- Handles draw (荒局): dealer continues, streak +1, no payment
- Tests: ≥ 90% coverage; 10,000-game simulation completes without illegal states

### 1.7 — Rule-Based AI (Greedy Baseline)

**Files:** `ai/shanten.py`, `ai/rule_based.py`

**Shanten calculator** (`shanten.py`):
- `shanten_number(hand, melds)` → int (−1 = winning, 0 = tenpai, n = n tiles from tenpai)
- Algorithm: try all ways to group tiles into sets + pair, minimize remaining ungrouped tiles
- `tenpai_tiles(hand, melds)` → list of tiles that would complete the hand (for overlay display later)

**Rule-based AI** (`rule_based.py`):
- Implements `choose_action(game_state, player_idx) -> Action`
- Discard: pick tile whose removal minimizes shanten number (ties: prefer honor tiles, then terminals)
- Chi/Pong/Kong: accept if it reduces or maintains shanten (never reject a valid win opportunity)
- Win: always declare if legal
- No bluffing, no danger assessment — pure greedy

### 1.8 — Tests

**Files:** `tests/test_*.py`

Coverage targets:
| Module | Target |
|--------|--------|
| tiles.py | 100% |
| wall.py | 100% |
| deal.py | 100% |
| actions.py | 100% |
| win_validator.py | 100% |
| scorer.py | 100% |
| game_session.py | ≥ 90% |
| shanten.py | ≥ 90% |
| rule_based.py | ≥ 90% |

Integration test: 10,000 rule-based AI vs rule-based AI games, all complete without error or illegal state.

---

## Error Handling

- All validators raise `ValueError` on invalid input (malformed tile strings, wrong player index, etc.)
- Game session raises `IllegalActionError` for illegal moves
- No silent failures — all rule violations surface as exceptions during testing

---

## Testing Infrastructure

- Framework: `pytest` via `uv`
- Coverage: `pytest-cov`
- CI: GitHub Actions runs `pytest --cov=backend/engine backend/tests/` on every push to `main`
- pyproject.toml includes `[tool.pytest.ini_options]` for test discovery

---

## Out of Scope for Phase 1

- WebSocket server (Phase 2)
- Electron/React UI (Phase 2)
- RL training pipeline (Phase 3)
- 嚦咕嚦咕 hand (excluded entirely)
- 插花 side bets (excluded entirely)
- ELO tracking (Phase 4)

---

*Approved: 2026-02-21*
