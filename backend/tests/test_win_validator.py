import pytest
from engine.win_validator import is_standard_win, decompose_hand

# --- STANDARD WIN ---
def test_simple_win_all_sequences():
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p5p6p + 1s1s pair = 5 sequences + pair = 17 tiles
    hand = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    assert is_standard_win(hand, melds=[]) is True

def test_simple_win_all_triplets():
    # 1m1m1m 2p2p2p 3s3s3s EEE NNN + CC pair = 5 triplets + pair = 17 tiles
    hand = ["1m","1m","1m","2p","2p","2p","3s","3s","3s","E","E","E","N","N","N","C","C"]
    assert is_standard_win(hand, melds=[]) is True

def test_not_a_win():
    hand = ["1m","2m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","1s","1s"]
    assert is_standard_win(hand, melds=[]) is False

def test_win_with_melds():
    # 3 exposed melds (already counted), hand has 2 sets + 1 pair = 8 tiles
    from engine.state import Meld
    melds = [
        Meld(type="pong", tiles=["E","E","E"], from_player=1),
        Meld(type="pong", tiles=["S","S","S"], from_player=2),
        Meld(type="chi",  tiles=["1m","2m","3m"], from_player=3),
    ]
    hand = ["4m","5m","6m","7m","8m","9m","1p","1p"]
    assert is_standard_win(hand, melds=melds) is True

def test_pair_only_not_a_win():
    hand = ["1m","1m"]
    assert is_standard_win(hand, melds=[]) is False

def test_thirteen_orphans_not_win():
    # Kokushi / 13 orphans -- not a valid hand in Taiwan rules
    hand = ["1m","9m","1p","9p","1s","9s","E","S","W","N","C","F","B","1m"]
    assert is_standard_win(hand, melds=[]) is False

def test_decompose_returns_valid_grouping():
    from engine.state import Meld
    # 4 exposed melds already, hand has 1 set + 1 pair = 5 tiles
    melds = [
        Meld(type="pong", tiles=["E","E","E"], from_player=1),
        Meld(type="pong", tiles=["S","S","S"], from_player=2),
        Meld(type="chi",  tiles=["4m","5m","6m"], from_player=3),
        Meld(type="pong", tiles=["N","N","N"], from_player=0),
    ]
    hand = ["1m","2m","3m","1p","1p"]
    result = decompose_hand(hand, melds=melds)
    assert result is not None
    sets, pair = result
    assert len(sets) == 1
    assert pair == ["1p", "1p"]

def test_decompose_returns_none_for_non_winning():
    hand = ["1m","3m","5m","7m","9m"]
    assert decompose_hand(hand, melds=[]) is None
