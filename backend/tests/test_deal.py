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
    # Use a deterministic setup: put known flowers in hand, no flowers in back wall
    from engine.tiles import FLOWERS
    gs = GameState.new_game()
    gs.wall = build_full_deck()[:128]  # non-flower tiles only
    gs.wall_back = build_full_deck()[:16]  # non-flower tiles for replacements
    # Give each player 16 non-flower tiles
    for i, p in enumerate(gs.players):
        p.hand = [f"{(i*4+j) % 9 + 1}m" for j in range(16)]
    # Dealer gets 17
    gs.players[0].hand.append("1p")
    # Force exactly 2 flowers into player 0's hand
    gs.players[0].hand[0] = "f1"
    gs.players[0].hand[1] = "f2"
    back_size_before = len(gs.wall_back)
    flower_replacement(gs)
    # Exactly 2 flowers replaced = 2 draws from back wall
    assert len(gs.wall_back) == back_size_before - 2
    assert "f1" not in gs.players[0].hand
    assert "f2" not in gs.players[0].hand

def test_flower_replacement_phase_set_to_play():
    gs = make_game_with_wall()
    deal_initial_hands(gs)
    flower_replacement(gs)
    assert gs.phase == "play"
