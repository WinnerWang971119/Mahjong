"""Tests for the greedy rule-based AI."""
from ai.rule_based import RuleBasedAI
from engine.game_session import GameSession, Action
from engine.state import GameState


def test_rule_based_always_returns_legal_action():
    ai = RuleBasedAI()
    session = GameSession()
    session.start_hand()
    for _ in range(50):
        if session.state.phase != "play":
            break
        # Poll all players for legal actions (handles claim phase)
        all_actions = []
        for p in range(4):
            player_actions = session.get_legal_actions(p)
            all_actions.extend([(p, a) for a in player_actions])
        if not all_actions:
            break
        # Pick first player with actions and let AI choose
        p_idx, _ = all_actions[0]
        legal = session.get_legal_actions(p_idx)
        action = ai.choose_action(session.state, p_idx, legal)
        assert action.type in [a.type for a in legal]
        session.step(action)


def test_rule_based_always_wins_when_legal():
    ai = RuleBasedAI()
    win_action = Action(type="win", tile="1m")
    discard_action = Action(type="discard", tile="2m")
    legal = [discard_action, win_action]
    gs = GameState.new_game()
    choice = ai.choose_action(gs, 0, legal)
    assert choice.type == "win"


def test_rule_based_prefers_lower_shanten_discard():
    ai = RuleBasedAI()
    gs = GameState.new_game()
    gs.players[0].hand = [
        "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
        "1p", "2p", "E", "S", "W", "N", "C", "C",
    ]
    legal = [Action(type="discard", tile=t) for t in set(gs.players[0].hand)]
    choice = ai.choose_action(gs, 0, legal)
    assert choice.type == "discard"
    # Should discard an isolated honor, not a connected number tile
    assert choice.tile not in ("1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m")


def test_rule_based_draws_when_needed():
    ai = RuleBasedAI()
    gs = GameState.new_game()
    legal = [Action(type="draw")]
    choice = ai.choose_action(gs, 0, legal)
    assert choice.type == "draw"


def test_rule_based_passes_when_no_benefit():
    ai = RuleBasedAI()
    gs = GameState.new_game()
    gs.players[1].hand = [
        "1m", "3m", "5m", "7m", "9m", "1p", "3p", "5p",
        "7p", "9p", "E", "S", "W", "N", "C", "F",
    ]
    legal = [
        Action(type="pong", tile="B", player_idx=1),
        Action(type="pass", player_idx=1),
    ]
    choice = ai.choose_action(gs, 1, legal)
    # Ponging a random tile with a terrible hand shouldn't help
    assert choice.type == "pass"
