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
