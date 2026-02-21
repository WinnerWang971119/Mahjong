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
    # Could form: 2m+3m+4m, 3m+4m+5m
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
