"""Integration test: 1,000 complete games without crash or illegal state."""
import random
from engine.game_session import GameSession, Action
from ai.rule_based import RuleBasedAI

AI = RuleBasedAI()
MAX_MOVES_PER_HAND = 1000

# Claim priority: win > open_kong > pong > chi > pass
_CLAIM_PRIORITY = {"win": 0, "open_kong": 1, "pong": 2, "chi": 3, "pass": 4}


def _step_once(session: GameSession) -> bool:
    """Advance the game by one logical step. Returns True if an action was taken.

    During claim phase, collects AI choices from all eligible claimers and
    resolves them by priority (win > kong > pong > chi > pass).  If everyone
    passes, submits all three pass actions so the engine advances to the next
    turn.
    """
    gs = session.state
    if gs.phase != "play":
        return False

    # Detect claim phase by checking if _sub_phase is "claim"
    if session._sub_phase == "claim":
        # Gather the best action each non-discarder would take
        candidates: list[tuple[int, Action]] = []  # (priority, action)
        pass_actions: list[Action] = []

        for p in range(4):
            legal = session.get_legal_actions(p)
            if not legal:
                continue  # discarder or no actions
            action = AI.choose_action(gs, p, legal)
            if action.player_idx is None:
                action.player_idx = p
            if action.type == "pass":
                pass_actions.append(action)
            else:
                priority = _CLAIM_PRIORITY.get(action.type, 99)
                candidates.append((priority, action))

        if candidates:
            # Submit the highest-priority (lowest number) claim
            candidates.sort(key=lambda x: x[0])
            session.step(candidates[0][1])
        else:
            # Everyone passes — submit all pass actions to advance the game
            for pa in pass_actions:
                session.step(pa)
        return True

    # Active turn phase — only the current player has legal actions
    legal = session.get_legal_actions(gs.current_player)
    if not legal:
        return False
    action = AI.choose_action(gs, gs.current_player, legal)
    if action.player_idx is None:
        action.player_idx = gs.current_player
    session.step(action)
    return True


def run_one_hand(seed: int) -> str:
    """Run one hand to completion using the AI. Returns phase at end."""
    random.seed(seed)
    session = GameSession()
    session.start_hand()
    moves = 0
    while session.state.phase == "play" and moves < MAX_MOVES_PER_HAND:
        if not _step_once(session):
            break
        moves += 1
    return session.state.phase


def _run_batch(start: int, count: int) -> dict[str, int]:
    """Run a batch of hands and return result counts."""
    results: dict[str, int] = {}
    for seed in range(start, start + count):
        result = run_one_hand(seed)
        results[result] = results.get(result, 0) + 1
    return results


def test_batch_0_100():
    results = _run_batch(0, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 0-99: {results}")


def test_batch_100_200():
    results = _run_batch(100, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 100-199: {results}")


def test_batch_200_300():
    results = _run_batch(200, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 200-299: {results}")


def test_batch_300_400():
    results = _run_batch(300, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 300-399: {results}")


def test_batch_400_500():
    results = _run_batch(400, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 400-499: {results}")


def test_batch_500_600():
    results = _run_batch(500, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 500-599: {results}")


def test_batch_600_700():
    results = _run_batch(600, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 600-699: {results}")


def test_batch_700_800():
    results = _run_batch(700, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 700-799: {results}")


def test_batch_800_900():
    results = _run_batch(800, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 800-899: {results}")


def test_batch_900_1000():
    results = _run_batch(900, 100)
    assert results.get("play", 0) == 0, f"Hands stuck: {results}"
    print(f"Batch 900-999: {results}")


def test_no_illegal_states_during_play():
    """Verify hand + melds always have correct tile counts during a game."""
    random.seed(12345)
    session = GameSession()
    session.start_hand()
    for _ in range(200):
        if session.state.phase != "play":
            break
        gs = session.state
        for p in gs.players:
            assert 0 <= len(p.hand) <= 17, f"Hand size out of range: {len(p.hand)}"
            assert len(p.flowers) <= 8, f"Too many flowers: {len(p.flowers)}"
        if not _step_once(session):
            break
