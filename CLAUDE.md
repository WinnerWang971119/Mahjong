# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Taiwan 16-Tile Mahjong (台灣16張麻將) AI/RL system. Phase 1 (game engine + rule-based AI) is complete. Phase 2 (desktop UI) is in design. Future phases: RL training and strong AI.

Master specification: `project-X.md`
Design docs: `docs/plans/`

## Commands

All commands run from `backend/`:

```bash
# Run all tests with coverage
uv run pytest -v

# Run a single test file
uv run pytest tests/test_scorer.py -v

# Run a single test function
uv run pytest tests/test_tiles.py::test_full_deck_size -v

# Run tests matching a pattern
uv run pytest tests/test_tiles.py -k "deck" -v

# Integration test (1000 AI games, ~10s)
uv run pytest tests/test_integration.py -v -s

# Coverage gate (CI threshold: ≥85%, excludes integration tests)
uv run pytest --cov=engine --cov=ai --cov-fail-under=85 --ignore=tests/test_integration.py -q
```

Package manager is `uv`. Install deps: `uv pip install -e ".[dev]" --system`

## Architecture

```
backend/
├── engine/          # Core game logic (pure Python, no external deps)
│   ├── tiles.py     # 34 tile types + 8 flowers, deck construction
│   ├── wall.py      # Wall shuffle & 槓尾 (back wall) building
│   ├── deal.py      # Initial deal + flower replacement
│   ├── state.py     # GameState, PlayerState, Meld dataclasses
│   ├── actions.py   # Chi/Pong/Kong validators
│   ├── game_session.py  # State machine: manages one full hand
│   ├── win_validator.py # 胡牌 detection (all hand shapes)
│   └── scorer.py    # 計台名堂 scoring (tai calculation, payment)
├── ai/
│   ├── shanten.py   # Array-based shanten calculator
│   └── rule_based.py    # Greedy AI: minimize shanten at each step
└── tests/           # pytest suite, one test_*.py per module
```

**State machine flow:** `GameSession.__init__()` → `start_hand()` → loop of `get_legal_actions()` + `step(action)` → "win" or "draw"

**Game phases:** `"deal"` → `"flower_replacement"` → `"play"` → `"win"`/`"draw"`
**Play subphases:** `"active_turn"` (draw/discard) and `"claim"` (chi/pong/kong from discard)

**Winning hand structure:** 5 sets (sequences/triplets) + 1 pair = 17 tiles (16 in hand + 1 drawn/claimed)

## Conventions

- Python 3.11+ with type hints; `from __future__ import annotations` for forward refs
- Dataclass-based immutable state (`@dataclass` for GameState, PlayerState, Meld)
- Conventional commits: `feat:`, `fix:`, `perf:`, `test:`, `ci:`, `docs:`, `refactor:`
- CI runs on GitHub Actions: unit tests + coverage ≥85% + integration test (10min timeout)
