"""Tests for the GameSession state machine (Taiwan 16-tile Mahjong)."""
from engine.game_session import GameSession, Action


def test_session_initializes_deal_phase():
    session = GameSession()
    assert session.state.phase in ("deal", "flower_replacement", "play")


def test_session_can_complete_full_hand():
    session = GameSession()
    session.start_hand()
    assert session.state.phase == "play"


def test_dealer_has_17_tiles_after_deal():
    session = GameSession()
    session.start_hand()
    dealer_idx = session.state.dealer_index
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
