from engine.tiles import (
    SUITS, HONORS, FLOWERS,
    build_full_deck, build_flower_set,
    is_number_tile, is_honor_tile, is_flower_tile,
    tile_suit, tile_value, tile_wind_index,
)

def test_full_deck_size():
    deck = build_full_deck()
    assert len(deck) == 136  # 144 tiles minus 8 flowers

def test_full_deck_has_four_of_each_normal_tile():
    deck = build_full_deck()
    from collections import Counter
    counts = Counter(deck)
    assert all(v == 4 for v in counts.values()), f"Some tiles don't have 4 copies: {counts}"

def test_flower_set_size():
    flowers = build_flower_set()
    assert len(flowers) == 8

def test_flower_set_unique():
    flowers = build_flower_set()
    assert len(set(flowers)) == 8

def test_number_tiles_count():
    deck = build_full_deck()
    numbers = [t for t in deck if is_number_tile(t)]
    assert len(numbers) == 108  # 9x3 suits x 4 copies

def test_honor_tiles_count():
    deck = build_full_deck()
    honors = [t for t in deck if is_honor_tile(t)]
    assert len(honors) == 28  # 7 honor types x 4 copies

def test_tile_suit_number():
    assert tile_suit("1m") == "m"
    assert tile_suit("9p") == "p"
    assert tile_suit("5s") == "s"

def test_tile_suit_raises_for_honor():
    import pytest
    with pytest.raises(ValueError):
        tile_suit("E")

def test_tile_value():
    assert tile_value("1m") == 1
    assert tile_value("9s") == 9

def test_tile_value_raises_for_honor():
    import pytest
    with pytest.raises(ValueError):
        tile_value("C")

def test_is_flower_tile():
    assert is_flower_tile("f1") is True
    assert is_flower_tile("f8") is True
    assert is_flower_tile("1m") is False

def test_tile_wind_index():
    assert tile_wind_index("E") == 0
    assert tile_wind_index("S") == 1
    assert tile_wind_index("W") == 2
    assert tile_wind_index("N") == 3

def test_tile_wind_index_raises_for_non_wind():
    import pytest
    with pytest.raises(ValueError):
        tile_wind_index("C")
