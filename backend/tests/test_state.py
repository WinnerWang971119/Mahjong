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
