"""Tests for the scoring engine (計台名堂)."""
import pytest

from engine.scorer import score_hand, ScoringResult
from engine.state import GameState, PlayerState, Meld, WindType
from engine.win_validator import decompose_hand


def make_gs(dealer_idx=0, streak=0, round_wind: WindType = "E") -> GameState:
    gs = GameState.new_game()
    gs.round_wind = round_wind
    gs.dealer_index = dealer_idx
    for p in gs.players:
        p.is_dealer = False
        p.streak = 0
    gs.players[dealer_idx].is_dealer = True
    gs.players[dealer_idx].streak = streak
    return gs


# --- BASIC 1-TAI HANDS ---


def test_menqing_1tai():
    """門清: concealed hand (no open melds), win by discard."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=[], decomp=decomp,
        discarder_idx=2,
    )
    assert any(name == "門清" for name, _ in result.yaku)


def test_zimo_1tai():
    """自摸: self-draw win with concealed hand triggers 不求 (門清+自摸 = 2台)."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="self_draw",
        hand=hand, melds=[], flowers=[], decomp=decomp,
    )
    # Self-draw with concealed hand = 不求 2台 (replaces separate 門清 and 自摸)
    assert any("自摸" in name or "不求" in name for name, _ in result.yaku)


def test_zuozhuang_dealer_gets_1tai():
    """作莊: dealer wins = 1台."""
    gs = make_gs(dealer_idx=0)
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=0, win_tile=win_tile, win_type="self_draw",
        hand=hand, melds=[], flowers=[], decomp=decomp,
    )
    assert any(name == "作莊" for name, _ in result.yaku)


# --- PAYMENT ---


def test_discard_payment_only_from_discarder():
    """On discard win, only the discarder pays the full tai amount."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=[], decomp=decomp,
        discarder_idx=2,
    )
    # Only player 2 pays (positive = pays to winner)
    payers = [idx for idx, amt in result.payments.items() if amt > 0]
    assert payers == [2]


def test_self_draw_all_three_pay():
    """On self-draw win, all 3 other players pay."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="self_draw",
        hand=hand, melds=[], flowers=[], decomp=decomp,
    )
    payers = [idx for idx, amt in result.payments.items() if amt > 0]
    assert sorted(payers) == [0, 2, 3]


# --- CAP ---


def test_score_capped_at_81():
    """Total tai is capped at MAX_TAI = 81."""
    gs = make_gs(dealer_idx=0, streak=100)
    hand = ["E", "E", "E", "S", "S", "S", "W", "W", "W",
            "N", "N", "N", "C", "C", "C"]
    win_tile = "1m"
    full_hand = hand + [win_tile]
    melds = []
    decomp = decompose_hand(full_hand, melds)
    result = score_hand(
        gs, winner_idx=0, win_tile=win_tile, win_type="self_draw",
        hand=hand, melds=melds, flowers=[], decomp=decomp,
    )
    assert result.total <= 81


# --- 台數 ACCURACY ---


def test_pinghu_2tai():
    """平胡: 5 sequences + pair, number tiles only, two-sided wait, not self-draw."""
    gs = make_gs()
    # 16 tiles in hand: 1m-9m(3 seq), 1p-3p(1 seq), 4s5s6s(1 seq), 1s(pair half)
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4s", "5s", "6s", "1s"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=[], decomp=decomp,
        discarder_idx=2, is_two_sided_wait=True,
    )
    assert any(name == "平胡" for name, _ in result.yaku)
    pinghu_tai = next(tai for name, tai in result.yaku if name == "平胡")
    assert pinghu_tai == 2


# --- FLOWER SCORING ---


def test_own_seat_flower_1tai():
    """Player's own seat flower = 1台 each."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    # Player 1 = South seat, seat flowers are f2 (season) and f6 (plant)
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=["f2"], decomp=decomp,
        discarder_idx=2,
    )
    assert any(name == "花牌" for name, _ in result.yaku)


# --- DRAGON TRIPLET ---


def test_dragon_triplet_1tai():
    """A triplet of dragon tiles = 1台 (箭字坎)."""
    gs = make_gs()
    # 16 tiles in hand: 1m-3m(seq), 4m-6m(seq), 7m-9m(seq), C,C,C(triplet), 1p,2p,3p(seq), 1s(pair half)
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "C", "C", "C", "1p", "2p", "3p", "1s"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=[], decomp=decomp,
        discarder_idx=2,
    )
    assert any(name == "箭字坎" for name, _ in result.yaku)


# --- OPEN MELD = NO 門清 ---


def test_open_meld_no_menqing():
    """Open melds prevent 門清."""
    gs = make_gs()
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p"]
    melds = [Meld(type="pong", tiles=["1s", "1s", "1s"], from_player=2)]
    win_tile = "4p"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, melds)
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=melds, flowers=[], decomp=decomp,
        discarder_idx=2,
    )
    assert not any(name == "門清" for name, _ in result.yaku)


# --- 對對胡 (ALL TRIPLETS) ---


def test_duiduihu_4tai():
    """對對胡: all triplets + pair = 4台."""
    gs = make_gs()
    # 5 triplets + pair = 17 tiles: 1m*3, 2m*3, 3m*3, 4m*3, 9s*2(pair), 5m*2+win
    # 16 in hand + 1 win_tile
    hand = ["1m", "1m", "1m", "2m", "2m", "2m", "3m", "3m", "3m",
            "4m", "4m", "4m", "9s", "9s", "5m", "5m"]
    win_tile = "5m"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=1, win_tile=win_tile, win_type="discard",
        hand=hand, melds=[], flowers=[], decomp=decomp,
        discarder_idx=2,
    )
    assert any(name == "對對胡" for name, _ in result.yaku)
    duidui_tai = next(tai for name, tai in result.yaku if name == "對對胡")
    assert duidui_tai == 4


# --- 連莊 STREAK ---


def test_lianzhuang_streak():
    """連莊: dealer streak adds tai."""
    gs = make_gs(dealer_idx=0, streak=3)
    hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "1p", "2p", "3p", "4p", "5p", "6p"]
    win_tile = "1s"
    full_hand = hand + [win_tile]
    decomp = decompose_hand(full_hand, [])
    result = score_hand(
        gs, winner_idx=0, win_tile=win_tile, win_type="self_draw",
        hand=hand, melds=[], flowers=[], decomp=decomp,
    )
    assert any(name == "連莊" for name, _ in result.yaku)
    streak_tai = next(tai for name, tai in result.yaku if name == "連莊")
    assert streak_tai == 3
