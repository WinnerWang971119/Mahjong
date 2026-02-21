"""Action types and validators for chi, pong, kong."""
from __future__ import annotations
from collections import Counter
from engine.tiles import is_number_tile, tile_suit, tile_value
from engine.state import Meld


# --- CHI ---

def get_chi_combinations(hand: list[str], discard: str) -> list[list[str]]:
    """
    Return all valid 3-tile sequences that include `discard` and 2 tiles from `hand`.
    Sequences must be same suit, consecutive values.
    Returns list of sorted 3-tile sequences.
    """
    if not is_number_tile(discard):
        return []
    suit = tile_suit(discard)
    val = tile_value(discard)
    hand_counts = Counter(hand)
    combos = []
    # Try all 3 offsets: discard is low, mid, or high of sequence
    for offset in range(3):
        seq_vals = [val - offset + i for i in range(3)]
        if any(v < 1 or v > 9 for v in seq_vals):
            continue
        needed = [f"{v}{suit}" for v in seq_vals if v != val]
        temp = hand_counts.copy()
        valid = True
        for t in needed:
            if temp[t] < 1:
                valid = False
                break
            temp[t] -= 1
        if valid:
            full_seq = sorted([f"{v}{suit}" for v in seq_vals])
            combos.append(full_seq)
    # Deduplicate sequences
    unique: list[list[str]] = []
    for seq in combos:
        if seq not in unique:
            unique.append(seq)
    return unique


def validate_chi(hand: list[str], discard: str) -> bool:
    """True if player can chi the discard using 2 tiles from hand."""
    return len(get_chi_combinations(hand, discard)) > 0


# --- PONG ---

def validate_pong(hand: list[str], discard: str) -> bool:
    """True if player has at least 2 copies of discard in hand (to form a triplet)."""
    return Counter(hand)[discard] >= 2


# --- OPEN KONG (from discard) ---

def validate_open_kong(hand: list[str], discard: str) -> bool:
    """True if player has 3 copies of discard in hand (to form a 4-tile open kong)."""
    return Counter(hand)[discard] >= 3


# --- ADDED KONG (extend existing pong with drawn tile) ---

def validate_added_kong(melds: list[Meld], drawn_tile: str) -> bool:
    """True if player has an existing pong meld matching drawn_tile."""
    return any(
        m.type == "pong" and drawn_tile in m.tiles
        for m in melds
    )


# --- CONCEALED KONG ---

def validate_concealed_kong(hand: list[str], tile: str) -> bool:
    """True if player has all 4 copies of tile in hand."""
    return Counter(hand)[tile] >= 4
