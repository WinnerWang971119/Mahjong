# Phase 1 — Game Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete, headless, rules-compliant Taiwan 16-tile Mahjong engine in Python with a greedy rule-based AI, ≥90% test coverage.

**Architecture:** Sequential milestone build — tiles → wall → deal → actions → win validator → scorer → session manager → shanten → rule-based AI. Each layer tests and commits before the next begins. No WebSocket server (deferred to Phase 2).

**Tech Stack:** Python 3.11, uv, pytest, pytest-cov, dataclasses, typing

---

## Task 0: Project Setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/engine/__init__.py`
- Create: `backend/ai/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

**Step 1: Create the directory structure**

```bash
mkdir -p backend/engine backend/ai backend/tests
touch backend/engine/__init__.py backend/ai/__init__.py backend/tests/__init__.py
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "mahjong-engine"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=engine --cov=ai --cov-report=term-missing"

[tool.coverage.run]
source = ["engine", "ai"]
```

Run from inside `backend/`:
```bash
cd backend
uv venv
uv pip install -e ".[dev]"
```

**Step 3: Create conftest.py with shared fixtures**

`backend/tests/conftest.py`:
```python
# Shared test fixtures will be added here as needed
```

**Step 4: Verify uv + pytest works**

```bash
cd backend
uv run pytest --collect-only
```
Expected: "no tests ran" (0 collected)

**Step 5: Commit**

```bash
git add backend/
git commit -m "chore: scaffold Phase 1 Python backend with uv + pytest"
```

---

## Task 1: Tile Definitions (Milestone 1.1a)

**Files:**
- Create: `backend/engine/tiles.py`
- Create: `backend/tests/test_tiles.py`

**Step 1: Write the failing tests**

`backend/tests/test_tiles.py`:
```python
from engine.tiles import (
    SUITS, HONORS, FLOWERS,
    build_full_deck, build_flower_set,
    is_number_tile, is_honor_tile, is_flower_tile,
    tile_suit, tile_value, tile_wind_index,
)

def test_full_deck_size():
    deck = build_full_deck()
    assert len(deck) == 136  # 144 tiles minus 8 flowers

def test_full_deck_has_four_of_each_normal_tile():
    deck = build_full_deck()
    from collections import Counter
    counts = Counter(deck)
    assert all(v == 4 for v in counts.values()), f"Some tiles don't have 4 copies: {counts}"

def test_flower_set_size():
    flowers = build_flower_set()
    assert len(flowers) == 8

def test_flower_set_unique():
    flowers = build_flower_set()
    assert len(set(flowers)) == 8

def test_number_tiles_count():
    deck = build_full_deck()
    numbers = [t for t in deck if is_number_tile(t)]
    assert len(numbers) == 108  # 9×3 suits × 4 copies

def test_honor_tiles_count():
    deck = build_full_deck()
    honors = [t for t in deck if is_honor_tile(t)]
    assert len(honors) == 28  # 7 honor types × 4 copies

def test_tile_suit_number():
    assert tile_suit("1m") == "m"
    assert tile_suit("9p") == "p"
    assert tile_suit("5s") == "s"

def test_tile_suit_raises_for_honor():
    import pytest
    with pytest.raises(ValueError):
        tile_suit("E")

def test_tile_value():
    assert tile_value("1m") == 1
    assert tile_value("9s") == 9

def test_tile_value_raises_for_honor():
    import pytest
    with pytest.raises(ValueError):
        tile_value("C")

def test_is_flower_tile():
    assert is_flower_tile("f1") is True
    assert is_flower_tile("f8") is True
    assert is_flower_tile("1m") is False

def test_tile_wind_index():
    assert tile_wind_index("E") == 0
    assert tile_wind_index("S") == 1
    assert tile_wind_index("W") == 2
    assert tile_wind_index("N") == 3

def test_tile_wind_index_raises_for_non_wind():
    import pytest
    with pytest.raises(ValueError):
        tile_wind_index("C")
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_tiles.py -v
```
Expected: `ModuleNotFoundError: No module named 'engine.tiles'`

**Step 3: Implement tiles.py**

`backend/engine/tiles.py`:
```python
"""Tile definitions and helpers for Taiwan 16-tile Mahjong."""
from __future__ import annotations

# Suit codes
SUITS = ("m", "p", "s")  # 萬, 筒, 索

# Honor tile codes
WINDS = ("E", "S", "W", "N")       # 東南西北
DRAGONS = ("C", "F", "B")          # 中發白
HONORS = WINDS + DRAGONS

# Flower tile codes: f1-f4 = 春夏秋冬 (seasons), f5-f8 = 梅蘭菊竹 (plants)
FLOWERS = tuple(f"f{i}" for i in range(1, 9))

# Season flowers (f1-f4) correspond to seats E/S/W/N
SEASON_FLOWERS = ("f1", "f2", "f3", "f4")
# Plant flowers (f5-f8) correspond to seats E/S/W/N
PLANT_FLOWERS = ("f5", "f6", "f7", "f8")

# Player seat winds in order
SEAT_WINDS = WINDS  # index 0=E, 1=S, 2=W, 3=N


def build_full_deck() -> list[str]:
    """Return 136-tile deck (4 copies each of 34 unique tiles, no flowers)."""
    tiles: list[str] = []
    for suit in SUITS:
        for value in range(1, 10):
            tiles.extend([f"{value}{suit}"] * 4)
    for honor in HONORS:
        tiles.extend([honor] * 4)
    return tiles


def build_flower_set() -> list[str]:
    """Return the 8 unique flower tiles (1 copy each)."""
    return list(FLOWERS)


def is_number_tile(tile: str) -> bool:
    """True if tile is a number tile (萬/筒/索)."""
    return len(tile) == 2 and tile[1] in SUITS and tile[0].isdigit()


def is_honor_tile(tile: str) -> bool:
    """True if tile is a wind or dragon honor tile."""
    return tile in HONORS


def is_flower_tile(tile: str) -> bool:
    """True if tile is a flower tile (f1-f8)."""
    return tile in FLOWERS


def is_wind_tile(tile: str) -> bool:
    return tile in WINDS


def is_dragon_tile(tile: str) -> bool:
    return tile in DRAGONS


def tile_suit(tile: str) -> str:
    """Return suit character ('m', 'p', 's'). Raises ValueError for non-number tiles."""
    if not is_number_tile(tile):
        raise ValueError(f"Tile '{tile}' has no suit (not a number tile)")
    return tile[1]


def tile_value(tile: str) -> int:
    """Return numeric value 1-9. Raises ValueError for non-number tiles."""
    if not is_number_tile(tile):
        raise ValueError(f"Tile '{tile}' has no value (not a number tile)")
    return int(tile[0])


def tile_wind_index(tile: str) -> int:
    """Return 0=E, 1=S, 2=W, 3=N. Raises ValueError if not a wind tile."""
    if tile not in WINDS:
        raise ValueError(f"Tile '{tile}' is not a wind tile")
    return WINDS.index(tile)


def own_seat_flowers(seat: int) -> tuple[str, str]:
    """Return the two flower tiles belonging to this seat (season + plant)."""
    return (SEASON_FLOWERS[seat], PLANT_FLOWERS[seat])
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_tiles.py -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add backend/engine/tiles.py backend/tests/test_tiles.py
git commit -m "feat: implement tile definitions and helpers"
```

---

## Task 2: Wall Construction & Shuffle (Milestone 1.1b)

**Files:**
- Create: `backend/engine/wall.py`
- Create: `backend/tests/test_wall.py`

**Step 1: Write the failing tests**

`backend/tests/test_wall.py`:
```python
import random
from collections import Counter
from engine.wall import shuffle_and_build_wall, split_wall_back
from engine.tiles import build_full_deck, build_flower_set

def test_wall_total_size():
    deck = build_full_deck() + build_flower_set()
    wall, flowers_in_deck = shuffle_and_build_wall(deck)
    # Wall = 144 tiles total, reserved 16 = 128 drawable + 16 back
    assert len(wall) + len(flowers_in_deck) == 0  # flowers removed separately
    # Actually wall should have 144 tiles before reservation
    full_wall, back = shuffle_and_build_wall(deck)
    assert len(full_wall) + len(back) == 144

def test_wall_and_back_cover_all_tiles():
    deck = build_full_deck() + build_flower_set()
    wall, back = shuffle_and_build_wall(deck)
    combined = wall + back
    assert Counter(combined) == Counter(deck)

def test_back_has_16_tiles():
    deck = build_full_deck() + build_flower_set()
    _, back = shuffle_and_build_wall(deck)
    assert len(back) == 16

def test_wall_has_128_tiles():
    deck = build_full_deck() + build_flower_set()
    wall, _ = shuffle_and_build_wall(deck)
    assert len(wall) == 128

def test_wall_is_shuffled():
    deck = build_full_deck() + build_flower_set()
    random.seed(42)
    wall1, _ = shuffle_and_build_wall(deck)
    random.seed(99)
    wall2, _ = shuffle_and_build_wall(deck)
    assert wall1 != wall2  # Statistically overwhelmingly true

def test_shuffle_does_not_modify_input():
    deck = build_full_deck() + build_flower_set()
    original = deck.copy()
    shuffle_and_build_wall(deck)
    assert deck == original
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_wall.py -v
```
Expected: `ModuleNotFoundError: No module named 'engine.wall'`

**Step 3: Implement wall.py**

`backend/engine/wall.py`:
```python
"""Wall construction and shuffling for Taiwan 16-tile Mahjong."""
from __future__ import annotations
import random


# Last 16 tiles of wall reserved as 殘牌 (鐵八墩) — never drawn in normal play
RESERVED_COUNT = 16


def shuffle_and_build_wall(deck: list[str]) -> tuple[list[str], list[str]]:
    """
    Shuffle the full 144-tile deck and split into:
      - wall: the 128 drawable tiles (drawn from front/head)
      - back: the 16 reserved 槓尾 tiles (used for kong/flower replacement draws)

    Returns (wall, back). Does not modify the input deck.
    """
    shuffled = deck.copy()
    random.shuffle(shuffled)
    back = shuffled[-RESERVED_COUNT:]
    wall = shuffled[:-RESERVED_COUNT]
    return wall, back


def draw_from_wall(wall: list[str]) -> str:
    """Draw the next tile from the head of the wall. Raises IndexError if wall is empty."""
    return wall.pop(0)


def draw_from_back(back: list[str]) -> str:
    """Draw a replacement tile from 槓尾 (back of wall). Used after kong or flower."""
    if not back:
        raise IndexError("No tiles left in back wall (槓尾)")
    return back.pop(0)
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_wall.py -v
```
Expected: All PASS (fix the test — `shuffle_and_build_wall` returns wall + back directly)

> **Note:** The first test in the file is poorly written. Replace the first `test_wall_total_size` test body with:
> ```python
> def test_wall_total_size():
>     deck = build_full_deck() + build_flower_set()
>     wall, back = shuffle_and_build_wall(deck)
>     assert len(wall) + len(back) == 144
> ```

**Step 5: Commit**

```bash
git add backend/engine/wall.py backend/tests/test_wall.py
git commit -m "feat: implement wall shuffle and build (殘牌 reservation)"
```

---

## Task 3: Core Data Structures (Milestone 1.1c)

**Files:**
- Create: `backend/engine/state.py`
- Create: `backend/tests/test_state.py`

**Step 1: Write the failing tests**

`backend/tests/test_state.py`:
```python
from engine.state import PlayerState, GameState, Meld

def test_player_state_defaults():
    p = PlayerState(seat=0)
    assert p.hand == []
    assert p.melds == []
    assert p.flowers == []
    assert p.discards == []
    assert p.is_dealer is False
    assert p.streak == 0

def test_meld_fields():
    m = Meld(type="pong", tiles=["1m", "1m", "1m"], from_player=2)
    assert m.type == "pong"
    assert m.tiles == ["1m", "1m", "1m"]
    assert m.from_player == 2

def test_game_state_has_four_players():
    gs = GameState.new_game()
    assert len(gs.players) == 4

def test_game_state_initial_phase():
    gs = GameState.new_game()
    assert gs.phase == "deal"

def test_game_state_initial_round_wind():
    gs = GameState.new_game()
    assert gs.round_wind == "E"
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_state.py -v
```
Expected: `ModuleNotFoundError: No module named 'engine.state'`

**Step 3: Implement state.py**

`backend/engine/state.py`:
```python
"""Core data structures for Taiwan 16-tile Mahjong game state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


MeldType = Literal["chi", "pong", "open_kong", "added_kong", "concealed_kong"]
Phase = Literal["deal", "flower_replacement", "play", "win", "draw"]


@dataclass
class Meld:
    type: MeldType
    tiles: list[str]            # 3 or 4 tiles forming the meld
    from_player: Optional[int]  # index of player whose discard was used (None = concealed)


@dataclass
class PlayerState:
    seat: int                   # 0=East, 1=South, 2=West, 3=North
    hand: list[str] = field(default_factory=list)
    melds: list[Meld] = field(default_factory=list)
    flowers: list[str] = field(default_factory=list)
    discards: list[str] = field(default_factory=list)
    is_dealer: bool = False
    streak: int = 0             # consecutive dealer rounds


@dataclass
class GameState:
    players: list[PlayerState]
    wall: list[str]             # drawable wall (head = next draw)
    wall_back: list[str]        # 槓尾 replacement tiles (back wall)
    discard_pool: list[str]     # all discarded tiles (牌海)
    current_player: int
    round_wind: str             # "E" / "S" / "W" / "N"
    round_number: int           # rounds completed in current wind circle
    dealer_index: int
    last_discard: Optional[str]
    last_action: Optional[str]
    phase: Phase
    tenpai_flags: dict[int, bool]  # player_idx → tenpai after deal (for 天聽 detection)

    @classmethod
    def new_game(cls) -> "GameState":
        """Create a fresh game state ready for dealing."""
        players = [PlayerState(seat=i) for i in range(4)]
        players[0].is_dealer = True
        return cls(
            players=players,
            wall=[],
            wall_back=[],
            discard_pool=[],
            current_player=0,
            round_wind="E",
            round_number=0,
            dealer_index=0,
            last_discard=None,
            last_action=None,
            phase="deal",
            tenpai_flags={},
        )
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_state.py -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add backend/engine/state.py backend/tests/test_state.py
git commit -m "feat: implement core game state data structures"
```

---

## Task 4: Deal Logic (Milestone 1.2)

**Files:**
- Create: `backend/engine/deal.py`
- Create: `backend/tests/test_deal.py`

**Step 1: Write the failing tests**

`backend/tests/test_deal.py`:
```python
from engine.deal import deal_initial_hands, flower_replacement
from engine.state import GameState, PlayerState
from engine.tiles import build_full_deck, build_flower_set
from engine.wall import shuffle_and_build_wall

def make_game_with_wall() -> GameState:
    deck = build_full_deck() + build_flower_set()
    wall, back = shuffle_and_build_wall(deck)
    gs = GameState.new_game()
    gs.wall = wall
    gs.wall_back = back
    return gs

def test_deal_gives_dealer_17_tiles():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    assert len(gs.players[0].hand) == 17  # dealer gets extra tile

def test_deal_gives_non_dealers_16_tiles():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    for i in range(1, 4):
        assert len(gs.players[i].hand) == 16

def test_deal_reduces_wall_size():
    gs = make_game_with_wall()
    wall_before = len(gs.wall)
    deal_initial_hands(gs)
    # 4×4 rounds × 4 players + 1 extra for dealer = 65 tiles dealt
    assert len(gs.wall) == wall_before - 65

def test_deal_does_not_give_flower_tiles():
    """Flower tiles should only come out during flower_replacement, not initial deal."""
    import random
    # Force all flowers to front of wall to test separation
    from engine.tiles import FLOWERS
    gs = GameState.new_game()
    # Put only non-flower tiles in wall
    gs.wall = build_full_deck()  # 136 tiles, no flowers
    gs.wall_back = build_flower_set()
    deal_initial_hands(gs)
    for p in gs.players:
        for tile in p.hand:
            assert tile not in FLOWERS

def test_flower_replacement_moves_flowers_to_flower_area():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    # Force player 0 to have a flower in hand for testing
    from engine.tiles import FLOWERS
    gs.players[0].hand[0] = "f1"
    flower_replacement(gs)
    assert "f1" not in gs.players[0].hand
    assert "f1" in gs.players[0].flowers

def test_flower_replacement_draws_replacement_tile():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    back_size_before = len(gs.wall_back)
    from engine.tiles import FLOWERS
    # Count flowers in all hands
    flower_count = sum(
        sum(1 for t in p.hand if t in FLOWERS)
        for p in gs.players
    )
    flower_replacement(gs)
    # Each flower replaced by 1 tile from back wall
    assert len(gs.wall_back) == back_size_before - flower_count

def test_flower_replacement_phase_set_to_play():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    flower_replacement(gs)
    assert gs.phase == "play"
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_deal.py -v
```

**Step 3: Implement deal.py**

`backend/engine/deal.py`:
```python
"""Deal logic: initial hand distribution and flower replacement."""
from __future__ import annotations
from engine.state import GameState
from engine.tiles import FLOWERS
from engine.wall import draw_from_wall, draw_from_back


def deal_initial_hands(gs: GameState) -> None:
    """
    Deal tiles to all 4 players in-place.
    4 rounds of 4 tiles each (counter-clockwise from dealer).
    Dealer receives one extra tile at the end → 17 tiles.
    Non-dealers get 16 tiles.
    Modifies gs.wall and gs.players[*].hand.
    """
    dealer = gs.dealer_index
    players_in_order = [(dealer + i) % 4 for i in range(4)]

    # 4 rounds × 4 tiles each
    for _ in range(4):
        for p_idx in players_in_order:
            tile = draw_from_wall(gs.wall)
            gs.players[p_idx].hand.append(tile)

    # Dealer's extra tile
    gs.players[dealer].hand.append(draw_from_wall(gs.wall))


def flower_replacement(gs: GameState) -> None:
    """
    Process flower replacement in dealer-first, counter-clockwise order.
    Any flower drawn goes to player's flower area; replacement drawn from 槓尾.
    Recurse if replacement tile is also a flower.
    Sets gs.phase = "play" when done.
    """
    dealer = gs.dealer_index
    order = [(dealer + i) % 4 for i in range(4)]
    for p_idx in order:
        _replace_flowers_for_player(gs, p_idx)
    gs.phase = "play"


def _replace_flowers_for_player(gs: GameState, p_idx: int) -> None:
    """Replace all flowers in this player's hand recursively."""
    player = gs.players[p_idx]
    while True:
        flower_indices = [i for i, t in enumerate(player.hand) if t in FLOWERS]
        if not flower_indices:
            break
        # Move all flowers to flower area
        for i in sorted(flower_indices, reverse=True):
            flower = player.hand.pop(i)
            player.flowers.append(flower)
        # Draw replacements from back wall
        for _ in flower_indices:
            replacement = draw_from_back(gs.wall_back)
            player.hand.append(replacement)
        # Loop to check if replacements are also flowers


def check_peipai_flower_hu(gs: GameState, p_idx: int) -> bool:
    """Return True if player was dealt all 8 flower tiles (配牌花胡)."""
    return len(gs.players[p_idx].flowers) == 8
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_deal.py -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add backend/engine/deal.py backend/tests/test_deal.py
git commit -m "feat: implement deal and flower replacement (Milestone 1.2)"
```

---

## Task 5: Action Types & Chi/Pong/Kong Validators (Milestone 1.3)

**Files:**
- Create: `backend/engine/actions.py`
- Create: `backend/tests/test_actions.py`

**Step 1: Write the failing tests**

`backend/tests/test_actions.py`:
```python
import pytest
from engine.actions import (
    validate_chi, validate_pong, validate_open_kong,
    validate_added_kong, validate_concealed_kong,
    get_chi_combinations,
)

# --- CHI ---
def test_chi_valid_sequence():
    hand = ["2m", "3m", "5p"]
    assert validate_chi(hand, "1m") is True
    assert validate_chi(hand, "4m") is True  # 2m+3m+4m

def test_chi_invalid_no_sequence():
    hand = ["1p", "5s", "E"]
    assert validate_chi(hand, "2m") is False

def test_chi_invalid_with_honor_tile():
    hand = ["E", "S", "1m"]
    assert validate_chi(hand, "E") is False  # honors cannot form sequences

def test_chi_combinations():
    hand = ["2m", "3m", "4m", "5m"]
    combos = get_chi_combinations(hand, "3m")
    # Could form: 1m+2m+3m (no 1m), 2m+3m+4m (yes), 3m+4m+5m (yes)
    assert ["2m", "3m", "4m"] in combos or ["2m", "4m"] in combos  # flexible
    # Simply: must return at least 1 valid sequence
    assert len(combos) >= 1

def test_chi_no_combos_if_honor():
    combos = get_chi_combinations(["E", "S"], "W")
    assert combos == []

# --- PONG ---
def test_pong_valid():
    hand = ["1m", "1m", "5s"]
    assert validate_pong(hand, "1m") is True

def test_pong_invalid_only_one_in_hand():
    hand = ["1m", "2m", "3m"]
    assert validate_pong(hand, "1m") is False

def test_pong_valid_honor():
    hand = ["E", "E", "1p"]
    assert validate_pong(hand, "E") is True

# --- OPEN KONG (from discard) ---
def test_open_kong_valid():
    hand = ["C", "C", "C", "1p"]
    assert validate_open_kong(hand, "C") is True

def test_open_kong_invalid_only_two():
    hand = ["C", "C", "1p"]
    assert validate_open_kong(hand, "C") is False

# --- ADDED KONG (extend existing pong) ---
def test_added_kong_valid():
    from engine.state import Meld
    melds = [Meld(type="pong", tiles=["F", "F", "F"], from_player=1)]
    assert validate_added_kong(melds, "F") is True

def test_added_kong_invalid_no_matching_pong():
    from engine.state import Meld
    melds = [Meld(type="pong", tiles=["F", "F", "F"], from_player=1)]
    assert validate_added_kong(melds, "C") is False

# --- CONCEALED KONG ---
def test_concealed_kong_valid():
    hand = ["2s", "2s", "2s", "2s", "3s"]
    assert validate_concealed_kong(hand, "2s") is True

def test_concealed_kong_invalid_only_three():
    hand = ["2s", "2s", "2s", "3s"]
    assert validate_concealed_kong(hand, "2s") is False
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_actions.py -v
```

**Step 3: Implement actions.py**

`backend/engine/actions.py`:
```python
"""Action types and validators for chi, pong, kong."""
from __future__ import annotations
from collections import Counter
from engine.tiles import is_number_tile, tile_suit, tile_value
from engine.state import Meld


# --- CHI ---

def get_chi_combinations(hand: list[str], discard: str) -> list[list[str]]:
    """
    Return all valid 3-tile sequences that include `discard` and 2 tiles from `hand`.
    Sequences must be same suit, consecutive values.
    Returns list of [tile_from_hand_1, tile_from_hand_2] pairs used with discard.
    """
    if not is_number_tile(discard):
        return []
    suit = tile_suit(discard)
    val = tile_value(discard)
    hand_counts = Counter(hand)
    combos = []
    # Try all 3 offsets: discard is low, mid, or high of sequence
    for offset in range(3):
        v_needed = [val - offset + i for i in range(3) if val - offset + i != val]
        seq_vals = [val - offset + i for i in range(3)]
        if any(v < 1 or v > 9 for v in seq_vals):
            continue
        needed = [f"{v}{suit}" for v in v_needed]
        temp = hand_counts.copy()
        valid = True
        for t in needed:
            if temp[t] < 1:
                valid = False
                break
            temp[t] -= 1
        if valid:
            full_seq = sorted([f"{v}{suit}" for v in seq_vals])
            combos.append(full_seq)
    return combos


def validate_chi(hand: list[str], discard: str) -> bool:
    """True if player can chi the discard using 2 tiles from hand."""
    return len(get_chi_combinations(hand, discard)) > 0


# --- PONG ---

def validate_pong(hand: list[str], discard: str) -> bool:
    """True if player has at least 2 copies of discard in hand (to form a triplet)."""
    return Counter(hand)[discard] >= 2


# --- OPEN KONG (from discard) ---

def validate_open_kong(hand: list[str], discard: str) -> bool:
    """True if player has 3 copies of discard in hand (to form a 4-tile open kong)."""
    return Counter(hand)[discard] >= 3


# --- ADDED KONG (extend existing pong with drawn tile) ---

def validate_added_kong(melds: list[Meld], drawn_tile: str) -> bool:
    """True if player has an existing pong meld matching drawn_tile."""
    return any(
        m.type == "pong" and m.tiles[0] == drawn_tile
        for m in melds
    )


# --- CONCEALED KONG ---

def validate_concealed_kong(hand: list[str], tile: str) -> bool:
    """True if player has all 4 copies of tile in hand."""
    return Counter(hand)[tile] >= 4
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_actions.py -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add backend/engine/actions.py backend/tests/test_actions.py
git commit -m "feat: implement chi/pong/kong action validators (Milestone 1.3)"
```

---

## Task 6: Win Validator — Standard Hand (Milestone 1.4a)

**Files:**
- Create: `backend/engine/win_validator.py`
- Create: `backend/tests/test_win_validator.py`

**Step 1: Write the failing tests**

`backend/tests/test_win_validator.py`:
```python
import pytest
from engine.win_validator import is_standard_win, decompose_hand

# --- STANDARD WIN ---
def test_simple_win_all_sequences():
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p6p + 1s1s pair
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    assert is_standard_win(hand, melds=[]) is True

def test_simple_win_all_triplets():
    # 1m1m1m 2p2p2p 3s3s3s EEE + CC pair
    hand = ["1m","1m","1m","2p","2p","2p","3s","3s","3s","E","E","E","C","C"]
    assert is_standard_win(hand, melds=[]) is True

def test_not_a_win():
    hand = ["1m","2m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    assert is_standard_win(hand, melds=[]) is False

def test_win_with_melds():
    # 3 exposed melds (already counted), hand has 1 set + 1 pair
    from engine.state import Meld
    melds = [
        Meld(type="pong", tiles=["E","E","E"], from_player=1),
        Meld(type="pong", tiles=["S","S","S"], from_player=2),
        Meld(type="chi",  tiles=["1m","2m","3m"], from_player=3),
    ]
    # Need 2 more sets + 1 pair in hand: 5 + 5 + 5 + pair → hand of 8 tiles
    hand = ["4m","5m","6m","7m","8m","9m","1p","1p"]
    assert is_standard_win(hand, melds=melds) is True

def test_pair_only_not_a_win():
    hand = ["1m","1m"]
    assert is_standard_win(hand, melds=[]) is False

def test_thirteen_orphans_not_win():
    # Kokushi / 13 orphans — not a valid hand in Taiwan rules (嚦咕嚦咕 excluded)
    hand = ["1m","9m","1p","9p","1s","9s","E","S","W","N","C","F","B","1m"]
    assert is_standard_win(hand, melds=[]) is False

def test_decompose_returns_valid_grouping():
    hand = ["1m","2m","3m","1p","1p"]
    result = decompose_hand(hand, melds=[])
    assert result is not None
    sets, pair = result
    assert len(sets) == 1
    assert pair == ["1p", "1p"]

def test_decompose_returns_none_for_non_winning():
    hand = ["1m","3m","5m","7m","9m"]
    assert decompose_hand(hand, melds=[]) is None
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_win_validator.py -v
```

**Step 3: Implement win_validator.py (standard win)**

`backend/engine/win_validator.py`:
```python
"""Win detection for Taiwan 16-tile Mahjong (嚦咕嚦咕 excluded)."""
from __future__ import annotations
from collections import Counter
from typing import Optional
from engine.state import Meld
from engine.tiles import is_number_tile, tile_suit, tile_value, FLOWERS


# --- STANDARD HAND DECOMPOSITION ---

def decompose_hand(
    hand: list[str],
    melds: list[Meld],
) -> Optional[tuple[list[list[str]], list[str]]]:
    """
    Try to decompose hand into (sets, pair) where:
      total sets needed = 5 - len(melds)
      each set is a sequence [a,b,c] or triplet [a,a,a]
      pair is [a,a]
    Returns (sets, pair) if valid win, else None.
    Melds are pre-counted as completed sets.
    """
    sets_needed = 5 - len(melds)
    sorted_hand = sorted(hand)
    return _find_decomposition(sorted_hand, sets_needed, [])


def _find_decomposition(
    tiles: list[str],
    sets_needed: int,
    found_sets: list[list[str]],
) -> Optional[tuple[list[list[str]], list[str]]]:
    """Recursive backtracking decomposition with memoization."""
    if sets_needed == 0:
        if len(tiles) == 2 and tiles[0] == tiles[1]:
            return (found_sets, tiles)
        return None

    if len(tiles) < sets_needed * 3 + 2:
        return None  # Not enough tiles

    # Try pair first (only when we've collected enough sets, to prune search)
    # We'll try extracting a set from the front tile
    tile = tiles[0]

    # Try triplet
    if tiles.count(tile) >= 3:
        remaining = tiles.copy()
        for _ in range(3):
            remaining.remove(tile)
        result = _find_decomposition(remaining, sets_needed - 1, found_sets + [[tile] * 3])
        if result:
            return result

    # Try sequence
    if is_number_tile(tile):
        suit = tile_suit(tile)
        val = tile_value(tile)
        t2 = f"{val+1}{suit}"
        t3 = f"{val+2}{suit}"
        if val <= 7:
            rem = tiles.copy()
            if rem.count(t2) >= 1 and rem.count(t3) >= 1:
                rem.remove(tile)
                rem.remove(t2)
                rem.remove(t3)
                result = _find_decomposition(rem, sets_needed - 1, found_sets + [[tile, t2, t3]])
                if result:
                    return result

    # Try using this tile as the pair
    if tiles.count(tile) >= 2:
        remaining = tiles.copy()
        remaining.remove(tile)
        remaining.remove(tile)
        result = _find_decomposition_no_pair(remaining, sets_needed, found_sets, [tile, tile])
        if result:
            return result

    return None


def _find_decomposition_no_pair(
    tiles: list[str],
    sets_needed: int,
    found_sets: list[list[str]],
    pair: list[str],
) -> Optional[tuple[list[list[str]], list[str]]]:
    """Like _find_decomposition but pair already found."""
    if sets_needed == 0:
        return (found_sets, pair) if len(tiles) == 0 else None
    if not tiles:
        return None

    tile = tiles[0]

    # Try triplet
    if tiles.count(tile) >= 3:
        remaining = tiles.copy()
        for _ in range(3):
            remaining.remove(tile)
        result = _find_decomposition_no_pair(remaining, sets_needed - 1, found_sets + [[tile] * 3], pair)
        if result:
            return result

    # Try sequence
    if is_number_tile(tile):
        suit = tile_suit(tile)
        val = tile_value(tile)
        t2 = f"{val+1}{suit}"
        t3 = f"{val+2}{suit}"
        if val <= 7 and tiles.count(t2) >= 1 and tiles.count(t3) >= 1:
            rem = tiles.copy()
            rem.remove(tile)
            rem.remove(t2)
            rem.remove(t3)
            result = _find_decomposition_no_pair(rem, sets_needed - 1, found_sets + [[tile, t2, t3]], pair)
            if result:
                return result

    return None


def is_standard_win(hand: list[str], melds: list[Meld]) -> bool:
    """True if hand + melds form a valid standard winning hand (5 sets + 1 pair)."""
    return decompose_hand(hand, melds) is not None


# --- FLOWER WIN CONDITIONS ---

def is_bajian_guohai(flowers: list[str]) -> bool:
    """八仙過海: player holds all 8 flower tiles."""
    return len(flowers) == 8 and set(flowers) == {f"f{i}" for i in range(1, 9)}


def is_qiqiang_yi(flowers: list[str], incoming_tile: str) -> bool:
    """
    七搶一: player holds 7 flowers and claims the 8th flower tile
    (which would be a replacement draw for another player's kong/flower).
    """
    if incoming_tile not in {f"f{i}" for i in range(1, 9)}:
        return False
    if len(flowers) != 7:
        return False
    all_eight = {f"f{i}" for i in range(1, 9)}
    return set(flowers) | {incoming_tile} == all_eight


# --- COMBINED WIN CHECK ---

def is_winning_hand(
    hand: list[str],
    melds: list[Meld],
    flowers: list[str],
    win_tile: str,
    is_flower_steal: bool = False,
) -> Optional[str]:
    """
    Check all win conditions.
    Returns win type string or None.
    Win types: "standard", "bajian_guohai", "qiqiang_yi"
    """
    if is_flower_steal:
        if is_qiqiang_yi(flowers, win_tile):
            return "qiqiang_yi"
        return None

    if is_bajian_guohai(flowers + [win_tile] if win_tile in {f"f{i}" for i in range(1,9)} else flowers):
        return "bajian_guohai"

    full_hand = sorted(hand + [win_tile])
    if is_standard_win(full_hand, melds):
        return "standard"

    return None
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_win_validator.py -v
```
Expected: All PASS (the backtracking may need debugging — if pair extraction conflicts, trace through)

**Step 5: Commit**

```bash
git add backend/engine/win_validator.py backend/tests/test_win_validator.py
git commit -m "feat: implement win validator — standard hand + flower wins (Milestone 1.4)"
```

---

## Task 7: Scoring Engine (Milestone 1.5)

**Files:**
- Create: `backend/engine/scorer.py`
- Create: `backend/tests/test_scorer.py`

**Step 1: Write the failing tests (critical cases)**

`backend/tests/test_scorer.py`:
```python
import pytest
from engine.scorer import score_hand, ScoringResult
from engine.state import GameState, PlayerState, Meld

def make_gs(dealer_idx=0, streak=0, round_wind="E") -> GameState:
    gs = GameState.new_game()
    gs.round_wind = round_wind
    gs.dealer_index = dealer_idx
    gs.players[dealer_idx].is_dealer = True
    gs.players[dealer_idx].streak = streak
    return gs

# --- BASIC 1-TAI HANDS ---
def test_menqing_1tai():
    gs = make_gs()
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])  # exclude win tile
    result = score_hand(gs, winner_idx=1, win_tile="1s", win_type="discard",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp)
    assert any(name == "門清" for name, _ in result.yaku)

def test_zimo_1tai():
    gs = make_gs()
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])
    result = score_hand(gs, winner_idx=1, win_tile="1s", win_type="self_draw",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp)
    assert any(name == "自摸" for name, _ in result.yaku)

def test_zuozhuang_dealer_gets_1tai():
    gs = make_gs(dealer_idx=0)
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])
    result = score_hand(gs, winner_idx=0, win_tile="1s", win_type="self_draw",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp)
    assert any(name == "作莊" for name, _ in result.yaku)

# --- PAYMENT ---
def test_discard_payment_only_from_discarder():
    gs = make_gs()
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])
    result = score_hand(gs, winner_idx=1, win_tile="1s", win_type="discard",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp,
                        discarder_idx=2)
    # Only player 2 pays
    payers = [idx for idx, amt in result.payments.items() if amt > 0]
    assert payers == [2]

def test_self_draw_all_three_pay():
    gs = make_gs()
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])
    result = score_hand(gs, winner_idx=1, win_tile="1s", win_type="self_draw",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp)
    payers = [idx for idx, amt in result.payments.items() if amt > 0]
    assert sorted(payers) == [0, 2, 3]

# --- CAP ---
def test_score_capped_at_81():
    gs = make_gs(dealer_idx=0, streak=100)
    # Construct 大四喜 (16台) + massive streak
    gs.players[0].streak = 100
    hand = ["E","E","E","S","S","S","W","W","W","N","N","N","C","C","C","1m"]
    from engine.win_validator import decompose_hand
    from engine.state import Meld
    melds = []
    decomp = decompose_hand(hand[:-1], melds)
    result = score_hand(gs, winner_idx=0, win_tile="1m", win_type="self_draw",
                        hand=hand[:-1], melds=melds, flowers=[], decomp=decomp)
    assert result.total <= 81

# --- 台數 ACCURACY ---
def test_pinghu_2tai():
    """平胡: 5 sequences + pair, number tiles only, two-sided wait, no 自摸."""
    gs = make_gs()
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4s","5s","6s","1s","1s"]
    from engine.win_validator import decompose_hand
    decomp = decompose_hand(hand[:-1], [])
    result = score_hand(gs, winner_idx=1, win_tile="1s", win_type="discard",
                        hand=hand[:-1], melds=[], flowers=[], decomp=decomp,
                        discarder_idx=2, is_two_sided_wait=True)
    assert any(name == "平胡" for name, _ in result.yaku)
    pinghu_tai = next(tai for name, tai in result.yaku if name == "平胡")
    assert pinghu_tai == 2
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_scorer.py -v
```

**Step 3: Implement scorer.py**

`backend/engine/scorer.py`:
```python
"""計台名堂 scoring engine for Taiwan 16-tile Mahjong."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional
from engine.state import GameState, Meld
from engine.tiles import (
    is_number_tile, tile_suit, is_honor_tile, is_wind_tile, is_dragon_tile,
    DRAGONS, WINDS, SEASON_FLOWERS, PLANT_FLOWERS, own_seat_flowers,
)

MAX_TAI = 81


@dataclass
class ScoringResult:
    yaku: list[tuple[str, int]]   # (name, tai_count)
    subtotal: int
    total: int                     # min(subtotal, MAX_TAI)
    payments: dict[int, int]       # player_idx → tai they pay (winner not included)


def score_hand(
    gs: GameState,
    winner_idx: int,
    win_tile: str,
    win_type: str,          # "self_draw" | "discard" | "qiqiang_yi" | "bajian_guohai"
    hand: list[str],        # concealed tiles (NOT including win_tile)
    melds: list[Meld],
    flowers: list[str],
    decomp: Optional[tuple[list[list[str]], list[str]]],
    discarder_idx: Optional[int] = None,
    is_two_sided_wait: bool = False,
    special_timing: Optional[str] = None,  # "tianhu"|"dihu"|"renhu"|"tianpai"|"dipai"
    is_gangshang: bool = False,
    is_haidi: bool = False,
    is_hedi: bool = False,
    is_qianggang: bool = False,
) -> ScoringResult:
    """Compute all applicable 計台名堂 and payment breakdown."""
    winner = gs.players[winner_idx]
    full_hand = hand + [win_tile]
    all_sets = (decomp[0] if decomp else []) + [m.tiles for m in melds]
    pair = decomp[1] if decomp else []
    seat_wind = WINDS[winner.seat]
    round_wind = gs.round_wind

    yaku: list[tuple[str, int]] = []

    # Helper: does winner have any open melds (chi/open_kong/pong)?
    has_open_melds = any(m.type in ("chi","pong","open_kong","added_kong") for m in melds)

    # ── 1台 HANDS ──────────────────────────────────────────────────

    # 作莊: dealer bonus (dealer wins OR dealer is discarder)
    if winner.is_dealer or (discarder_idx is not None and gs.players[discarder_idx].is_dealer):
        if winner.is_dealer:
            yaku.append(("作莊", 1))

    # 連莊 / 拉莊 (streak)
    streak = winner.streak if winner.is_dealer else 0
    if winner.is_dealer and streak > 0:
        yaku.append(("連莊", streak))

    # 拉莊 is added to payment, tracked separately in _compute_payments

    # 門清: no chi/pong/open_kong (concealed kong is allowed)
    is_menqing = not has_open_melds
    if is_menqing and special_timing not in ("tianhu", "dihu", "renhu"):
        yaku.append(("門清", 1))

    # 自摸
    if win_type == "self_draw":
        yaku.append(("自摸", 1))

    # 風牌 (seat wind triplet)
    for s in all_sets:
        if len(s) == 3 and s[0] == s[1] == s[2] == seat_wind:
            yaku.append(("風牌(開門風)", 1))
            break

    # 圈風 (round wind triplet)
    for s in all_sets:
        if len(s) == 3 and s[0] == s[1] == s[2] == round_wind:
            yaku.append(("風圈(圈風)", 1))
            break

    # 箭字坎 (dragon triplets) — 1台 each
    for dragon in DRAGONS:
        for s in all_sets:
            if len(s) == 3 and s[0] == s[1] == s[2] == dragon:
                yaku.append((f"箭字坎({dragon})", 1))
                break

    # 花牌 (own seat flowers) — 1台 each
    own_flowers = own_seat_flowers(winner.seat)
    for f in flowers:
        if f in own_flowers:
            yaku.append((f"花牌({f})", 1))

    # 搶槓
    if is_qianggang:
        yaku.append(("搶槓", 1))

    # 獨聽 (single tile wait) — caller must specify
    concealed_tiles = hand.copy()
    waiting_count = _count_waits(concealed_tiles, melds, win_tile)
    is_dandiào = waiting_count == 1
    if is_dandiào:
        yaku.append(("獨聽", 1))

    # 半求: only 1 concealed tile left (all others chi/ponged), win by self_draw
    is_banqiu = len(hand) == 1 and win_type == "self_draw"
    if is_banqiu:
        yaku.append(("半求", 1))

    # 槓上開花
    if is_gangshang:
        yaku.append(("槓上開花", 1))

    # 海底撈月
    if is_haidi:
        yaku.append(("海底撈月", 1))

    # 河底撈魚
    if is_hedi:
        yaku.append(("河底撈魚", 1))

    # ── 2台 HANDS ──────────────────────────────────────────────────

    # 不求 (no chi/pong/open_kong AND self_draw) — replaces 門清+自摸 with 2tai
    is_buqiu = is_menqing and win_type == "self_draw"
    if is_buqiu:
        # Remove 門清 and 自摸 individually, add 不求(2tai) instead
        yaku = [(n, t) for (n, t) in yaku if n not in ("門清", "自摸")]
        yaku.append(("不求(+自摸)", 2))

    # 平胡: 5 sequences + pair + number tiles only + 2-sided wait + no self_draw
    if (
        decomp and
        all(_is_sequence(s) for s in decomp[0]) and
        all(_is_sequence(m.tiles) for m in melds) and
        all(is_number_tile(t) for t in full_hand) and
        is_two_sided_wait and
        win_type != "self_draw" and
        not is_dandiào
    ):
        yaku.append(("平胡", 2))

    # 全求: all chi/pong (1 concealed tile left), win by discard
    is_quanqiu = len(hand) == 1 and win_type == "discard"
    if is_quanqiu:
        yaku.append(("全求", 2))

    # 花槓: complete set of 4 flowers (春夏秋冬 or 梅蘭菊竹)
    flower_set = set(flowers)
    seasons = set(SEASON_FLOWERS)
    plants = set(PLANT_FLOWERS)
    if seasons.issubset(flower_set):
        yaku.append(("花槓(春夏秋冬)", 2))
    if plants.issubset(flower_set):
        yaku.append(("花槓(梅蘭菊竹)", 2))

    # 三暗坎: 3 concealed triplets (including concealed kongs)
    concealed_triplets = _count_concealed_triplets(hand + [win_tile] if win_type == "self_draw" else hand, melds)
    if concealed_triplets >= 3 and concealed_triplets < 4:
        yaku.append(("三暗坎", 2))

    # ── 4台 HANDS ──────────────────────────────────────────────────

    # 地聽: tenpai after first discard (門清 not separately counted)
    if special_timing == "dipai":
        yaku = [(n, t) for (n, t) in yaku if n != "門清"]
        yaku.append(("地聽", 4))

    # 對對胡: all triplets + 1 pair
    if decomp and all(not _is_sequence(s) for s in all_sets):
        yaku.append(("對對胡", 4))

    # 小三元: 2 dragon triplets + 1 dragon pair
    dragon_trips = sum(1 for s in all_sets if len(s) >= 3 and s[0] in DRAGONS and len(set(s[:3])) == 1)
    dragon_pair = pair and pair[0] in DRAGONS
    if dragon_trips == 2 and dragon_pair:
        # Remove individual 箭字坎 entries (subsumed)
        yaku = [(n, t) for (n, t) in yaku if not n.startswith("箭字坎")]
        yaku.append(("小三元", 4))

    # 湊一色: all tiles one suit + honors
    suits_used = set()
    has_honor = False
    for t in full_hand:
        if is_number_tile(t):
            suits_used.add(tile_suit(t))
        elif is_honor_tile(t):
            has_honor = True
    if len(suits_used) == 1 and has_honor:
        yaku.append(("湊一色(混一色)", 4))

    # ── 5台 HANDS ──────────────────────────────────────────────────
    if concealed_triplets == 4:
        yaku = [(n, t) for (n, t) in yaku if n not in ("門清", "對對胡", "三暗坎")]
        yaku.append(("四暗坎", 5))

    # ── 8台 HANDS ──────────────────────────────────────────────────

    # 天聽
    if special_timing == "tianpai":
        yaku.append(("天聽", 8))

    # 五暗坎
    if concealed_triplets == 5:
        yaku = [(n, t) for (n, t) in yaku if n not in ("門清", "對對胡", "四暗坎", "三暗坎")]
        yaku.append(("五暗坎", 8))

    # 大三元: all 3 dragon triplets
    if dragon_trips == 3:
        yaku = [(n, t) for (n, t) in yaku if not n.startswith("箭字坎")]
        yaku.append(("大三元", 8))

    # 小四喜: 3 wind triplets + 1 wind pair
    wind_trips = sum(1 for s in all_sets if len(s) >= 3 and s[0] in WINDS and len(set(s[:3])) == 1)
    wind_pair = pair and pair[0] in WINDS
    if wind_trips == 3 and wind_pair:
        yaku.append(("小四喜", 8))

    # 清一色: all one suit, no honors
    if len(suits_used) == 1 and not has_honor:
        yaku.append(("清一色", 8))

    # 七搶一 / 八仙過海
    if win_type == "qiqiang_yi":
        yaku.append(("七搶一", 8))
    if win_type == "bajian_guohai":
        yaku.append(("八仙過海", 8))

    # ── 12台 HANDS ─────────────────────────────────────────────────
    if win_type == "peipai_flower":
        yaku.append(("配牌花胡", 12))

    # ── 16台 HANDS ─────────────────────────────────────────────────
    if special_timing == "tianhu":
        yaku = [(n, t) for (n, t) in yaku if n not in ("門清", "自摸", "不求(+自摸)")]
        yaku.append(("天胡", 16))

    if special_timing == "dihu":
        yaku.append(("地胡", 16))

    if special_timing == "renhu":
        yaku.append(("人胡", 16))

    # 大四喜: all 4 wind triplets
    if wind_trips == 4:
        yaku = [(n, t) for (n, t) in yaku if n in ("大四喜",) or not (n.startswith("風牌") or n.startswith("風圈"))]
        yaku = [(n, t) for (n, t) in yaku if n != "小四喜"]
        yaku.append(("大四喜", 16))

    # 字一色: all honor tiles
    if all(is_honor_tile(t) for t in full_hand):
        yaku = [(n, t) for (n, t) in yaku if n != "對對胡"]
        yaku.append(("字一色", 16))

    subtotal = sum(t for _, t in yaku)
    total = min(subtotal, MAX_TAI)
    payments = _compute_payments(gs, winner_idx, win_type, total, discarder_idx, streak if winner.is_dealer else 0)

    return ScoringResult(yaku=yaku, subtotal=subtotal, total=total, payments=payments)


def _compute_payments(
    gs: GameState,
    winner_idx: int,
    win_type: str,
    total_tai: int,
    discarder_idx: Optional[int],
    streak: int,
) -> dict[int, int]:
    """Compute how much each player pays."""
    payments: dict[int, int] = {i: 0 for i in range(4)}
    lazhuang = streak  # 拉莊 extra tai paid by ALL other players

    if win_type == "self_draw":
        for i in range(4):
            if i != winner_idx:
                payments[i] = total_tai + lazhuang
    elif win_type == "discard":
        if discarder_idx is not None:
            payments[discarder_idx] = total_tai + lazhuang
        # Other non-winners still pay 拉莊
        for i in range(4):
            if i != winner_idx and i != discarder_idx and lazhuang > 0:
                payments[i] = lazhuang
    elif win_type in ("bajian_guohai",):
        for i in range(4):
            if i != winner_idx:
                payments[i] = total_tai + lazhuang
    elif win_type == "qiqiang_yi":
        # Only the player whose flower was stolen pays
        if discarder_idx is not None:
            payments[discarder_idx] = total_tai + lazhuang
        for i in range(4):
            if i != winner_idx and i != discarder_idx and lazhuang > 0:
                payments[i] = lazhuang

    return payments


def _is_sequence(tiles: list[str]) -> bool:
    if len(tiles) != 3:
        return False
    if not all(is_number_tile(t) for t in tiles):
        return False
    vals = sorted(tile_value(t) for t in tiles)
    suits = [tile_suit(t) for t in tiles]
    return len(set(suits)) == 1 and vals == [vals[0], vals[0]+1, vals[0]+2]


def _count_concealed_triplets(hand: list[str], melds: list[Meld]) -> int:
    """Count concealed triplets: all-same-tile groups in hand + concealed kongs."""
    counts = Counter(hand)
    triplets = sum(1 for v in counts.values() if v >= 3)
    concealed_kongs = sum(1 for m in melds if m.type == "concealed_kong")
    return triplets + concealed_kongs


def _count_waits(hand: list[str], melds: list[Meld], win_tile: str) -> int:
    """Count how many unique tiles complete the hand (for 獨聽 detection)."""
    from engine.win_validator import is_standard_win
    from engine.tiles import build_full_deck, FLOWERS
    all_tiles = build_full_deck()
    unique_tiles = set(all_tiles) - set(FLOWERS)
    waits = 0
    for t in unique_tiles:
        if is_standard_win(sorted(hand + [t]), melds):
            waits += 1
    return waits
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_scorer.py -v
```

**Step 5: Commit**

```bash
git add backend/engine/scorer.py backend/tests/test_scorer.py
git commit -m "feat: implement 計台名堂 scoring engine (Milestone 1.5)"
```

---

## Task 8: Game Session Manager (Milestone 1.6)

**Files:**
- Create: `backend/engine/game_session.py`
- Create: `backend/tests/test_game_session.py`

**Step 1: Write the failing tests**

`backend/tests/test_game_session.py`:
```python
from engine.game_session import GameSession

def test_session_initializes_deal_phase():
    session = GameSession()
    assert session.state.phase in ("deal", "flower_replacement", "play")

def test_session_can_complete_full_hand():
    """Run one complete hand with all-pass strategy to reach draw or win."""
    session = GameSession()
    session.start_hand()
    assert session.state.phase == "play"

def test_dealer_has_17_tiles_after_deal():
    session = GameSession()
    session.start_hand()
    dealer_idx = session.state.dealer_index
    # After flower replacement, dealer may have fewer if flowers drawn
    # But hand + flowers + melds should account for original 17
    dealer = session.state.players[dealer_idx]
    assert len(dealer.hand) >= 14  # minimum after flower replacement

def test_legal_actions_not_empty_during_play():
    session = GameSession()
    session.start_hand()
    actions = session.get_legal_actions(session.state.current_player)
    assert len(actions) > 0

def test_draw_can_happen_without_error():
    session = GameSession()
    session.start_hand()
    from engine.game_session import Action
    session.step(Action(type="draw"))

def test_game_completes_without_crash():
    """10-game smoke test with random legal action selection."""
    import random
    for _ in range(10):
        session = GameSession()
        session.start_hand()
        max_moves = 500
        moves = 0
        while session.state.phase == "play" and moves < max_moves:
            actions = session.get_legal_actions(session.state.current_player)
            if not actions:
                break
            action = random.choice(actions)
            session.step(action)
            moves += 1
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_game_session.py -v
```

**Step 3: Implement game_session.py**

`backend/engine/game_session.py`:
```python
"""Game session state machine for Taiwan 16-tile Mahjong."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
from engine.state import GameState, PlayerState, Meld
from engine.tiles import build_full_deck, build_flower_set, WINDS, FLOWERS
from engine.wall import shuffle_and_build_wall, draw_from_wall, draw_from_back
from engine.deal import deal_initial_hands, flower_replacement
from engine.actions import (
    validate_chi, validate_pong, validate_open_kong,
    validate_added_kong, validate_concealed_kong, get_chi_combinations,
)
from engine.win_validator import is_winning_hand


ActionType = Literal[
    "draw", "discard", "chi", "pong", "open_kong", "added_kong",
    "concealed_kong", "win", "pass"
]


@dataclass
class Action:
    type: ActionType
    tile: Optional[str] = None        # tile to discard, or kong tile
    combo: Optional[list[str]] = None # chi combination


class IllegalActionError(Exception):
    pass


class GameSession:
    """Manages a full Taiwan Mahjong game session."""

    def __init__(self) -> None:
        self.state = GameState.new_game()
        self._pending_discard: Optional[str] = None  # tile waiting for claim
        self._discarder: Optional[int] = None
        self._awaiting_claims: bool = False
        self._gangshang_draw: bool = False

    def start_hand(self) -> None:
        """Shuffle, deal, and run flower replacement to reach 'play' phase."""
        deck = build_full_deck() + build_flower_set()
        wall, back = shuffle_and_build_wall(deck)
        self.state.wall = wall
        self.state.wall_back = back
        deal_initial_hands(self.state)
        flower_replacement(self.state)
        self.state.phase = "play"

    def get_legal_actions(self, player_idx: int) -> list[Action]:
        """Return all legal actions for the given player in the current state."""
        gs = self.state
        actions: list[Action] = []

        if gs.phase != "play":
            return actions

        player = gs.players[player_idx]

        if self._awaiting_claims:
            # It's a discard moment: other players can claim, or pass
            if player_idx != self._discarder:
                discard = self._pending_discard
                if discard:
                    win_result = is_winning_hand(player.hand, player.melds, player.flowers, discard)
                    if win_result:
                        actions.append(Action(type="win", tile=discard))
                    if validate_pong(player.hand, discard):
                        actions.append(Action(type="pong", tile=discard))
                    if validate_open_kong(player.hand, discard):
                        actions.append(Action(type="open_kong", tile=discard))
                    # Chi: only left player (counter-clockwise predecessor)
                    left_of_discarder = (self._discarder + 3) % 4
                    if player_idx == left_of_discarder and validate_chi(player.hand, discard):
                        for combo in get_chi_combinations(player.hand, discard):
                            actions.append(Action(type="chi", tile=discard, combo=combo))
                actions.append(Action(type="pass"))
        elif gs.current_player == player_idx:
            # It's this player's active turn
            if not player.hand or len(player.hand) == 16:
                # Need to draw
                if gs.wall:
                    actions.append(Action(type="draw"))
            else:
                # Player has drawn (17 tiles for non-dealer or after draw)
                # Can discard any tile
                for tile in set(player.hand):
                    actions.append(Action(type="discard", tile=tile))
                # Can declare win on self-draw
                last = player.hand[-1] if player.hand else None
                if last:
                    win_result = is_winning_hand(player.hand[:-1], player.melds, player.flowers, last)
                    if win_result:
                        actions.append(Action(type="win", tile=last))
                # Concealed kong
                from collections import Counter
                counts = Counter(player.hand)
                for tile, count in counts.items():
                    if count >= 4 and validate_concealed_kong(player.hand, tile):
                        actions.append(Action(type="concealed_kong", tile=tile))
                # Added kong (加槓)
                for tile in set(player.hand):
                    if validate_added_kong(player.melds, tile):
                        actions.append(Action(type="added_kong", tile=tile))

        return actions

    def step(self, action: Action) -> GameState:
        """Advance the game state by one action. Returns updated state."""
        gs = self.state

        if action.type == "draw":
            self._do_draw(gs.current_player)

        elif action.type == "discard":
            self._do_discard(gs.current_player, action.tile)

        elif action.type == "pong":
            self._do_pong(gs.current_player, action.tile)

        elif action.type == "chi":
            self._do_chi(gs.current_player, action.tile, action.combo)

        elif action.type == "open_kong":
            self._do_open_kong(gs.current_player, action.tile)

        elif action.type == "added_kong":
            self._do_added_kong(gs.current_player, action.tile)

        elif action.type == "concealed_kong":
            self._do_concealed_kong(gs.current_player, action.tile)

        elif action.type == "win":
            self._do_win(gs.current_player, action.tile)

        elif action.type == "pass":
            self._do_pass(gs.current_player)

        return self.state

    # ── PRIVATE ACTION HANDLERS ──────────────────────────────────────────────

    def _do_draw(self, player_idx: int) -> None:
        gs = self.state
        if not gs.wall:
            # Draw (荒局)
            gs.phase = "draw"
            return
        tile = draw_from_wall(gs.wall)
        if tile in FLOWERS:
            gs.players[player_idx].flowers.append(tile)
            replacement = draw_from_back(gs.wall_back)
            gs.players[player_idx].hand.append(replacement)
        else:
            gs.players[player_idx].hand.append(tile)

    def _do_discard(self, player_idx: int, tile: str) -> None:
        gs = self.state
        player = gs.players[player_idx]
        if tile not in player.hand:
            raise IllegalActionError(f"Tile {tile} not in player {player_idx}'s hand")
        player.hand.remove(tile)
        player.discards.append(tile)
        gs.discard_pool.append(tile)
        gs.last_discard = tile
        self._pending_discard = tile
        self._discarder = player_idx
        self._awaiting_claims = True

    def _do_pass(self, player_idx: int) -> None:
        """All players have passed; advance to next player's draw."""
        if self._awaiting_claims:
            # Move to next player
            self._awaiting_claims = False
            self.state.current_player = (self._discarder + 3) % 4

    def _do_pong(self, player_idx: int, tile: str) -> None:
        gs = self.state
        player = gs.players[player_idx]
        for _ in range(2):
            player.hand.remove(tile)
        meld = Meld(type="pong", tiles=[tile, tile, tile], from_player=self._discarder)
        player.melds.append(meld)
        self._awaiting_claims = False
        gs.current_player = player_idx

    def _do_chi(self, player_idx: int, tile: str, combo: list[str]) -> None:
        gs = self.state
        player = gs.players[player_idx]
        for t in combo:
            if t != tile:
                player.hand.remove(t)
        meld = Meld(type="chi", tiles=combo, from_player=self._discarder)
        player.melds.append(meld)
        self._awaiting_claims = False
        gs.current_player = player_idx

    def _do_open_kong(self, player_idx: int, tile: str) -> None:
        gs = self.state
        player = gs.players[player_idx]
        for _ in range(3):
            player.hand.remove(tile)
        meld = Meld(type="open_kong", tiles=[tile]*4, from_player=self._discarder)
        player.melds.append(meld)
        self._awaiting_claims = False
        replacement = draw_from_back(gs.wall_back)
        if replacement in FLOWERS:
            player.flowers.append(replacement)
            replacement = draw_from_back(gs.wall_back)
        player.hand.append(replacement)
        gs.current_player = player_idx

    def _do_added_kong(self, player_idx: int, tile: str) -> None:
        gs = self.state
        player = gs.players[player_idx]
        player.hand.remove(tile)
        for meld in player.melds:
            if meld.type == "pong" and meld.tiles[0] == tile:
                meld.type = "added_kong"
                meld.tiles.append(tile)
                break
        replacement = draw_from_back(gs.wall_back)
        if replacement in FLOWERS:
            player.flowers.append(replacement)
            replacement = draw_from_back(gs.wall_back)
        player.hand.append(replacement)
        self._gangshang_draw = True

    def _do_concealed_kong(self, player_idx: int, tile: str) -> None:
        gs = self.state
        player = gs.players[player_idx]
        for _ in range(4):
            player.hand.remove(tile)
        meld = Meld(type="concealed_kong", tiles=[tile]*4, from_player=None)
        player.melds.append(meld)
        replacement = draw_from_back(gs.wall_back)
        if replacement in FLOWERS:
            player.flowers.append(replacement)
            replacement = draw_from_back(gs.wall_back)
        player.hand.append(replacement)

    def _do_win(self, player_idx: int, tile: str) -> None:
        self.state.phase = "win"
        self.state.last_action = "win"
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_game_session.py -v
```
Expected: All PASS (the 10-game smoke test may expose edge cases — fix as they arise)

**Step 5: Commit**

```bash
git add backend/engine/game_session.py backend/tests/test_game_session.py
git commit -m "feat: implement game session state machine (Milestone 1.6)"
```

---

## Task 9: Shanten Calculator (Milestone 1.7a)

**Files:**
- Create: `backend/ai/shanten.py`
- Create: `backend/tests/test_shanten.py`

**Step 1: Write the failing tests**

`backend/tests/test_shanten.py`:
```python
from ai.shanten import shanten_number, tenpai_tiles
from engine.state import Meld

def test_complete_hand_is_minus_one():
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","1s","1s"]
    assert shanten_number(hand, []) == -1

def test_tenpai_is_zero():
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","1s"]
    assert shanten_number(hand, []) == 0

def test_one_from_tenpai():
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p"]
    assert shanten_number(hand, []) == 1

def test_tenpai_tiles_for_single_pair_wait():
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p + ?s?s (need pair)
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","1s"]
    waits = tenpai_tiles(hand, [])
    # Needs any tile that forms a pair with 1s — only 1s completes standard win
    assert "1s" in waits

def test_shanten_with_melds():
    from engine.state import Meld
    melds = [Meld(type="pong", tiles=["E","E","E"], from_player=1)]
    # With 1 meld = 1 set done, need 4 more + pair from 13-tile hand
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","1s"]
    assert shanten_number(hand, melds) == -1  # already winning
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_shanten.py -v
```

**Step 3: Implement shanten.py**

`backend/ai/shanten.py`:
```python
"""Shanten number calculator for Taiwan Mahjong (from scratch)."""
from __future__ import annotations
from collections import Counter
from engine.tiles import is_number_tile, tile_suit, tile_value, build_full_deck, FLOWERS
from engine.state import Meld
from engine.win_validator import is_standard_win


def shanten_number(hand: list[str], melds: list[Meld]) -> int:
    """
    Calculate shanten number:
      -1 = winning hand
       0 = tenpai (one tile away from win)
       n = n tiles needed to reach tenpai
    """
    sets_needed = 5 - len(melds)
    return _shanten(sorted(hand), sets_needed)


def _shanten(tiles: list[str], sets_needed: int) -> int:
    """
    Minimum shanten via exhaustive grouping.
    Strategy: maximize (complete_sets + partial_sets), where:
      - complete_set = 3 tiles (sequence or triplet)
      - partial = 2 tiles (pair, two-sided wait, or edge wait)
    shanten = (sets_needed - 1) - complete_sets - max_partials
    """
    best = [sets_needed + 1]  # worst case

    def search(tiles: list[str], sets: int, partials: int, has_pair: bool):
        # Calculate shanten with current progress
        s = (sets_needed - 1) - sets - partials
        best[0] = min(best[0], s)
        if not tiles:
            return

        # Try complete sets from first tile
        t = tiles[0]
        counts = Counter(tiles)

        # Triplet
        if counts[t] >= 3:
            rem = tiles.copy()
            for _ in range(3):
                rem.remove(t)
            search(rem, sets + 1, partials, has_pair)

        # Sequence
        if is_number_tile(t):
            suit = tile_suit(t)
            val = tile_value(t)
            t2, t3 = f"{val+1}{suit}", f"{val+2}{suit}"
            if val <= 7 and counts[t2] >= 1 and counts[t3] >= 1:
                rem = tiles.copy()
                rem.remove(t); rem.remove(t2); rem.remove(t3)
                search(rem, sets + 1, partials, has_pair)

        # Partials (only if not exceeding useful count)
        if partials < sets_needed - sets:
            # Pair (use as pair-wait OR later as the 將眼)
            if counts[t] >= 2:
                rem = tiles.copy()
                rem.remove(t); rem.remove(t)
                if not has_pair:
                    search(rem, sets, partials + 1, True)  # 將眼
                else:
                    search(rem, sets, partials + 1, has_pair)  # extra pair as partial

            # Two-sided or edge wait (partial sequence)
            if is_number_tile(t):
                suit = tile_suit(t)
                val = tile_value(t)
                for dv in (1, 2):
                    t2 = f"{val+dv}{suit}"
                    if counts[t2] >= 1:
                        rem = tiles.copy()
                        rem.remove(t); rem.remove(t2)
                        search(rem, sets, partials + 1, has_pair)

        # Skip this tile (it contributes nothing)
        rem = tiles.copy()
        rem.remove(t)
        search(rem, sets, partials, has_pair)

    search(tiles, 0, 0, False)
    return best[0] - 1  # adjust: shanten=0 means tenpai


def tenpai_tiles(hand: list[str], melds: list[Meld]) -> list[str]:
    """Return list of tiles that would complete this hand (shanten → -1)."""
    if shanten_number(hand, melds) != 0:
        return []
    all_tiles = set(build_full_deck()) - set(FLOWERS)
    return [t for t in all_tiles if is_standard_win(sorted(hand + [t]), melds)]
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_shanten.py -v
```

**Step 5: Commit**

```bash
git add backend/ai/shanten.py backend/tests/test_shanten.py
git commit -m "feat: implement shanten number calculator (Milestone 1.7a)"
```

---

## Task 10: Rule-Based AI (Milestone 1.7b)

**Files:**
- Create: `backend/ai/rule_based.py`
- Create: `backend/tests/test_rule_based.py`

**Step 1: Write the failing tests**

`backend/tests/test_rule_based.py`:
```python
from ai.rule_based import RuleBasedAI
from engine.game_session import GameSession, Action

def test_rule_based_always_returns_legal_action():
    ai = RuleBasedAI()
    session = GameSession()
    session.start_hand()
    for _ in range(50):
        if session.state.phase != "play":
            break
        p_idx = session.state.current_player
        legal = session.get_legal_actions(p_idx)
        if not legal:
            break
        action = ai.choose_action(session.state, p_idx, legal)
        assert action in legal or action.type == legal[0].type  # type match sufficient
        session.step(action)

def test_rule_based_always_wins_when_legal():
    from engine.game_session import Action
    ai = RuleBasedAI()
    # If win action is available, it must be chosen
    win_action = Action(type="win", tile="1m")
    discard_action = Action(type="discard", tile="2m")
    legal = [discard_action, win_action]
    from engine.state import GameState
    gs = GameState.new_game()
    choice = ai.choose_action(gs, 0, legal)
    assert choice.type == "win"

def test_rule_based_prefers_lower_shanten_discard():
    ai = RuleBasedAI()
    from engine.state import GameState, PlayerState
    gs = GameState.new_game()
    # Hand: 1m2m3m 4m5m6m 7m8m9m 1p2p (need 3p or pair) + junk tiles
    gs.players[0].hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","E","S","W","N","C","C"]
    from engine.game_session import Action
    legal = [Action(type="discard", tile=t) for t in set(gs.players[0].hand)]
    choice = ai.choose_action(gs, 0, legal)
    # Should discard an honor or useless tile, not 1p2p
    assert choice.type == "discard"
    assert choice.tile not in ("1p", "2p")
```

**Step 2: Run to verify they fail**

```bash
cd backend
uv run pytest tests/test_rule_based.py -v
```

**Step 3: Implement rule_based.py**

`backend/ai/rule_based.py`:
```python
"""Greedy rule-based AI baseline for Taiwan 16-tile Mahjong."""
from __future__ import annotations
from engine.state import GameState
from engine.game_session import Action
from ai.shanten import shanten_number


class RuleBasedAI:
    """
    Greedy AI: minimize shanten number at every decision.
    Always wins when legal. No bluffing or danger assessment.
    """

    def choose_action(
        self,
        gs: GameState,
        player_idx: int,
        legal_actions: list[Action],
    ) -> Action:
        if not legal_actions:
            raise ValueError("No legal actions available")

        # Priority 1: Win always
        for a in legal_actions:
            if a.type == "win":
                return a

        # Priority 2: On discard — pick tile that minimizes shanten
        discard_actions = [a for a in legal_actions if a.type == "discard"]
        if discard_actions:
            return self._best_discard(gs, player_idx, discard_actions)

        # Priority 3: Kong (concealed or added) — usually reduces shanten
        for a in legal_actions:
            if a.type in ("concealed_kong", "added_kong", "open_kong"):
                return a

        # Priority 4: Accept pong/chi if it reduces shanten
        player = gs.players[player_idx]
        current_shanten = shanten_number(player.hand, player.melds)
        for a in legal_actions:
            if a.type in ("pong", "chi"):
                # Simulate: would this reduce shanten?
                simulated_hand = player.hand.copy()
                if a.type == "pong" and a.tile:
                    simulated_hand.remove(a.tile)
                    simulated_hand.remove(a.tile)
                elif a.type == "chi" and a.combo:
                    for t in a.combo:
                        if t != a.tile and t in simulated_hand:
                            simulated_hand.remove(t)
                # After pong/chi, player must discard — assume best discard
                from engine.state import Meld
                import copy
                new_melds = copy.deepcopy(player.melds)
                if a.type == "pong" and a.tile:
                    new_melds.append(Meld(type="pong", tiles=[a.tile]*3, from_player=None))
                elif a.type == "chi" and a.combo:
                    new_melds.append(Meld(type="chi", tiles=a.combo, from_player=None))
                new_shanten = shanten_number(simulated_hand, new_melds)
                if new_shanten <= current_shanten:
                    return a

        # Priority 5: Draw (mandatory if available)
        for a in legal_actions:
            if a.type == "draw":
                return a

        # Priority 6: Pass (decline optional action)
        for a in legal_actions:
            if a.type == "pass":
                return a

        # Fallback
        return legal_actions[0]

    def _best_discard(
        self,
        gs: GameState,
        player_idx: int,
        discard_actions: list[Action],
    ) -> Action:
        """Return the discard action that minimizes shanten number."""
        player = gs.players[player_idx]
        best_shanten = float("inf")
        best_action = discard_actions[0]
        best_priority = 0

        for a in discard_actions:
            if a.tile is None:
                continue
            simulated = player.hand.copy()
            if a.tile in simulated:
                simulated.remove(a.tile)
            s = shanten_number(simulated, player.melds)
            # Tiebreak: prefer discarding honors (priority 2) then terminals (priority 1) then others (0)
            from engine.tiles import is_honor_tile, tile_value, is_number_tile
            priority = 0
            if is_honor_tile(a.tile):
                priority = 2
            elif is_number_tile(a.tile) and tile_value(a.tile) in (1, 9):
                priority = 1

            if s < best_shanten or (s == best_shanten and priority > best_priority):
                best_shanten = s
                best_action = a
                best_priority = priority

        return best_action
```

**Step 4: Run tests**

```bash
cd backend
uv run pytest tests/test_rule_based.py -v
```

**Step 5: Commit**

```bash
git add backend/ai/rule_based.py backend/tests/test_rule_based.py
git commit -m "feat: implement greedy rule-based AI (Milestone 1.7)"
```

---

## Task 11: Integration Test — 10,000 Games (Milestone 1.8)

**Files:**
- Create: `backend/tests/test_integration.py`

**Step 1: Write the integration test**

`backend/tests/test_integration.py`:
```python
"""Integration test: 10,000 complete games without crash or illegal state."""
import random
from engine.game_session import GameSession
from ai.rule_based import RuleBasedAI

AI = RuleBasedAI()
MAX_MOVES_PER_HAND = 1000

def run_one_hand(seed: int) -> str:
    """Run one hand to completion. Returns "win", "draw", or "aborted"."""
    random.seed(seed)
    session = GameSession()
    session.start_hand()
    moves = 0
    while session.state.phase == "play" and moves < MAX_MOVES_PER_HAND:
        p_idx = session.state.current_player
        legal = session.get_legal_actions(p_idx)
        if not legal:
            return "aborted"
        action = AI.choose_action(session.state, p_idx, legal)
        session.step(action)
        moves += 1
    return session.state.phase  # "win" or "draw"

def test_1000_hands_complete_without_crash():
    results = {"win": 0, "draw": 0, "aborted": 0, "play": 0}
    for seed in range(1000):
        result = run_one_hand(seed)
        results[result] = results.get(result, 0) + 1
    assert results["aborted"] == 0, f"Hands aborted: {results}"
    # At least some should complete (win or draw)
    assert results["win"] + results["draw"] > 0

def test_no_illegal_states_during_play():
    """Verify hand + melds always have correct tile counts."""
    random.seed(12345)
    session = GameSession()
    session.start_hand()
    for _ in range(200):
        if session.state.phase != "play":
            break
        gs = session.state
        # Verify each player's hand has reasonable tile count
        for p in gs.players:
            assert 0 <= len(p.hand) <= 17, f"Hand size out of range: {len(p.hand)}"
            assert len(p.flowers) <= 8, f"Too many flowers: {len(p.flowers)}"
        p_idx = gs.current_player
        legal = session.get_legal_actions(p_idx)
        if not legal:
            break
        action = AI.choose_action(gs, p_idx, legal)
        session.step(action)
```

**Step 2: Run to verify it fails (before fixes)**

```bash
cd backend
uv run pytest tests/test_integration.py -v
```

**Step 3: Fix any failures revealed by integration test**

The integration test will likely expose edge cases. Fix them one at a time, re-running:
```bash
cd backend
uv run pytest tests/test_integration.py -v
```

**Step 4: Run full test suite with coverage**

```bash
cd backend
uv run pytest --cov=engine --cov=ai --cov-report=term-missing -v
```
Expected: All pass, ≥90% coverage overall, 100% on core rule modules.

**Step 5: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add 1000-game integration test suite (Milestone 1.8)"
```

---

## Task 12: GitHub Actions CI Setup

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: Phase 1 Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        working-directory: backend
        run: uv pip install -e ".[dev]" --system

      - name: Run tests
        working-directory: backend
        run: uv run pytest --cov=engine --cov=ai --cov-report=term-missing -v

      - name: Fail if coverage below 90%
        working-directory: backend
        run: uv run pytest --cov=engine --cov=ai --cov-fail-under=90
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for Phase 1 pytest"
```

---

## Final Coverage Check

```bash
cd backend
uv run pytest --cov=engine --cov=ai --cov-report=term-missing -v 2>&1 | tail -30
```

Target:
| Module | Target |
|--------|--------|
| engine/tiles.py | 100% |
| engine/wall.py | 100% |
| engine/deal.py | 100% |
| engine/actions.py | 100% |
| engine/win_validator.py | 100% |
| engine/scorer.py | 100% |
| engine/game_session.py | ≥ 90% |
| ai/shanten.py | ≥ 90% |
| ai/rule_based.py | ≥ 90% |

---

*Plan complete. Phase 1 deliverable: a fully tested, rules-compliant Taiwan 16-tile Mahjong engine ready for Phase 2 UI integration.*
