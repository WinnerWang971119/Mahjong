import random
from collections import Counter
from engine.wall import shuffle_and_build_wall
from engine.tiles import build_full_deck, build_flower_set


def test_wall_total_size():
    deck = build_full_deck() + build_flower_set()
    wall, back = shuffle_and_build_wall(deck)
    assert len(wall) + len(back) == 144


def test_wall_and_back_cover_all_tiles():
    deck = build_full_deck() + build_flower_set()
    wall, back = shuffle_and_build_wall(deck)
    combined = wall + back
    assert Counter(combined) == Counter(deck)


def test_back_has_16_tiles():
    deck = build_full_deck() + build_flower_set()
    _, back = shuffle_and_build_wall(deck)
    assert len(back) == 16


def test_wall_has_128_tiles():
    deck = build_full_deck() + build_flower_set()
    wall, _ = shuffle_and_build_wall(deck)
    assert len(wall) == 128


def test_wall_is_shuffled():
    deck = build_full_deck() + build_flower_set()
    random.seed(42)
    wall1, _ = shuffle_and_build_wall(deck)
    random.seed(99)
    wall2, _ = shuffle_and_build_wall(deck)
    assert wall1 != wall2  # Statistically overwhelmingly true


def test_shuffle_does_not_modify_input():
    deck = build_full_deck() + build_flower_set()
    original = deck.copy()
    shuffle_and_build_wall(deck)
    assert deck == original
