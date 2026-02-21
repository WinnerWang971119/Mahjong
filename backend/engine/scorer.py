"""Scoring engine (計台名堂) for Taiwan 16-tile Mahjong.

Computes all applicable yaku, total tai (capped at MAX_TAI = 81),
and payment breakdown for a winning hand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from engine.state import GameState, Meld, WindType
from engine.tiles import (
    DRAGONS,
    HONORS,
    SEASON_FLOWERS,
    PLANT_FLOWERS,
    SUITS,
    WINDS,
    is_dragon_tile,
    is_honor_tile,
    is_number_tile,
    is_wind_tile,
    own_seat_flowers,
    tile_suit,
    tile_value,
)

MAX_TAI = 81

# Seat wind mapping: seat index -> wind code
_SEAT_WINDS: tuple[str, ...] = WINDS  # 0=E, 1=S, 2=W, 3=N


@dataclass
class ScoringResult:
    """Result of scoring a winning hand."""

    yaku: list[tuple[str, int]]  # list of (yaku_name, tai_value)
    subtotal: int                # sum of tai before cap
    total: int                   # min(subtotal, MAX_TAI)
    payments: dict[int, int]     # player_idx -> amount owed (positive = pays winner)


def score_hand(
    gs: GameState,
    *,
    winner_idx: int,
    win_tile: str,
    win_type: str,                                  # "self_draw" | "discard"
    hand: list[str],                                # concealed tiles (excluding win_tile)
    melds: list[Meld],
    flowers: list[str],
    decomp: Optional[tuple[list[list[str]], list[str]]],
    discarder_idx: Optional[int] = None,
    is_two_sided_wait: bool = False,
    is_qiangang: bool = False,                      # 搶槓
    is_gangshang: bool = False,                      # 槓上開花
    is_haidi: bool = False,                          # 海底撈月 / 河底撈魚
    is_diting: bool = False,                         # 地聽
    is_tianting: bool = False,                       # 天聽
    is_tianhu: bool = False,                         # 天胡
    is_dihu: bool = False,                           # 地胡
    is_renhu: bool = False,                          # 人胡
    is_qiqiang_yi: bool = False,                     # 七搶一
    is_bajian_guohai: bool = False,                  # 八仙過海
    is_peipai_huahu: bool = False,                   # 配牌花胡
) -> ScoringResult:
    """Compute all applicable yaku and payment breakdown for a winning hand.

    Parameters
    ----------
    gs : GameState
        Current game state (for round wind, dealer info).
    winner_idx : int
        Index of the winning player (0-3).
    win_tile : str
        The tile that completed the win.
    win_type : str
        "self_draw" or "discard".
    hand : list[str]
        Concealed tiles in hand (NOT including *win_tile*).
    melds : list[Meld]
        Declared melds (chi, pong, kong).
    flowers : list[str]
        Flower tiles the player has collected.
    decomp : tuple or None
        Result of ``decompose_hand(hand + [win_tile], melds)``.
    discarder_idx : int or None
        Index of player who discarded the winning tile (None for self-draw).
    is_two_sided_wait : bool
        True if the winning tile completes a two-sided wait (兩面聽).
    """
    player = gs.players[winner_idx]
    seat_wind = _SEAT_WINDS[player.seat]
    round_wind = gs.round_wind
    is_self_draw = win_type == "self_draw"

    # Determine if the hand is fully concealed (門清)
    open_melds = [m for m in melds if m.type in ("chi", "pong", "open_kong", "added_kong")]
    is_concealed = len(open_melds) == 0

    # Build the full hand for analysis (hand tiles + win_tile)
    full_hand = hand + [win_tile]

    # Extract sets and pair from decomposition
    sets: list[list[str]] = []
    pair: list[str] = []
    if decomp is not None:
        sets, pair = decomp

    # Combine concealed sets with meld tiles for full analysis
    all_sets = list(sets)
    for m in melds:
        all_sets.append(m.tiles[:3])  # first 3 tiles represent the set

    yaku: list[tuple[str, int]] = []

    # ---------------------------------------------------------------
    # 16台 yaku (highest priority)
    # ---------------------------------------------------------------
    if is_tianhu:
        yaku.append(("天胡", 16))
    if is_dihu:
        yaku.append(("地胡", 16))
    if is_renhu:
        yaku.append(("人胡", 16))

    # 大四喜: 4 wind triplets
    wind_triplet_count = _count_wind_triplets(all_sets, melds)
    wind_in_pair = pair and len(pair) == 2 and is_wind_tile(pair[0])
    if wind_triplet_count == 4:
        yaku.append(("大四喜", 16))

    # 字一色: all tiles are honor tiles
    if decomp is not None and _all_honors(full_hand, melds):
        yaku.append(("字一色", 16))

    # ---------------------------------------------------------------
    # 12台 yaku
    # ---------------------------------------------------------------
    if is_peipai_huahu:
        yaku.append(("配牌花胡", 12))

    # ---------------------------------------------------------------
    # 8台 yaku
    # ---------------------------------------------------------------
    if is_tianting:
        yaku.append(("天聽", 8))

    if is_bajian_guohai:
        yaku.append(("八仙過海", 8))

    if is_qiqiang_yi:
        yaku.append(("七搶一", 8))

    # 大三元: 3 dragon triplets
    dragon_triplet_count = _count_dragon_triplets(all_sets, melds)
    if dragon_triplet_count == 3:
        yaku.append(("大三元", 8))

    # 小四喜: 3 wind triplets + wind pair
    if wind_triplet_count == 3 and wind_in_pair:
        yaku.append(("小四喜", 8))

    # 清一色: all number tiles of one suit (no honors)
    if decomp is not None and _is_qingyise(full_hand, melds):
        yaku.append(("清一色", 8))

    # 五暗坎: 5 concealed triplets
    concealed_kong_count = sum(1 for m in melds if m.type == "concealed_kong")
    concealed_triplet_count = _count_concealed_triplets(sets, is_self_draw, win_tile) + concealed_kong_count
    if concealed_triplet_count >= 5:
        yaku.append(("五暗坎", 8))

    # ---------------------------------------------------------------
    # 5台 yaku
    # ---------------------------------------------------------------
    # 四暗坎: 4 concealed triplets (but not 5)
    if concealed_triplet_count == 4 and not any(n == "五暗坎" for n, _ in yaku):
        yaku.append(("四暗坎", 5))

    # ---------------------------------------------------------------
    # 4台 yaku
    # ---------------------------------------------------------------
    if is_diting:
        yaku.append(("地聽", 4))

    # 對對胡: all sets are triplets (no sequences), plus pair
    if decomp is not None and _is_duiduihu(all_sets, melds):
        yaku.append(("對對胡", 4))

    # 小三元: 2 dragon triplets + dragon pair
    if dragon_triplet_count == 2 and pair and is_dragon_tile(pair[0]):
        yaku.append(("小三元", 4))

    # 湊一色(混一色): one suit + honors only
    if decomp is not None and _is_hunyise(full_hand, melds):
        # Don't award if already 清一色 or 字一色
        if not any(n in ("清一色", "字一色") for n, _ in yaku):
            yaku.append(("湊一色", 4))

    # 三暗坎: 3 concealed triplets (but not 4 or 5)
    if concealed_triplet_count == 3 and not any(n in ("四暗坎", "五暗坎") for n, _ in yaku):
        yaku.append(("三暗坎", 2))

    # ---------------------------------------------------------------
    # 2台 yaku
    # ---------------------------------------------------------------
    # 不求: 門清 + 自摸 = 2台 (replaces separate 門清 and 自摸)
    buqiu = is_concealed and is_self_draw
    if buqiu:
        yaku.append(("不求", 2))

    # 平胡: 5 sequences + pair, all number tiles, two-sided wait, not self-draw
    if decomp is not None and _is_pinghu(all_sets, pair, full_hand, melds,
                                         is_self_draw, is_two_sided_wait):
        yaku.append(("平胡", 2))

    # 全求: only 1 concealed tile + win by discard (4 open melds)
    if len(open_melds) == 4 and not is_self_draw:
        yaku.append(("全求", 2))

    # 花槓: complete set of 4 seasonal or 4 plant flowers
    season_count = sum(1 for f in flowers if f in SEASON_FLOWERS)
    plant_count = sum(1 for f in flowers if f in PLANT_FLOWERS)
    if season_count == 4:
        yaku.append(("花槓", 2))
    if plant_count == 4:
        yaku.append(("花槓", 2))

    # ---------------------------------------------------------------
    # 1台 yaku
    # ---------------------------------------------------------------
    # 作莊: winner is dealer
    if gs.players[winner_idx].is_dealer:
        yaku.append(("作莊", 1))

    # 連莊: dealer streak (awarded to winner when dealer has streak >= 1)
    dealer = gs.players[gs.dealer_index]
    if dealer.streak > 0:
        yaku.append(("連莊", dealer.streak))

    # 門清: no open melds, win by discard (not 不求)
    if is_concealed and not is_self_draw and not buqiu:
        yaku.append(("門清", 1))

    # 自摸: self-draw (only when NOT 不求 — which already includes 自摸)
    if is_self_draw and not buqiu:
        yaku.append(("自摸", 1))

    # 風牌(開門風): seat wind triplet
    if _has_wind_triplet(all_sets, melds, seat_wind):
        yaku.append(("風牌", 1))

    # 風圈(圈風): round wind triplet (awarded alongside 風牌 when seat == round wind)
    if _has_wind_triplet(all_sets, melds, round_wind):
        yaku.append(("風圈", 1))

    # 箭字坎: dragon triplet (1台 each)
    for dragon in DRAGONS:
        if _has_dragon_triplet(all_sets, melds, dragon):
            yaku.append(("箭字坎", 1))

    # 花牌: own seat flower (1台 each)
    seat_flowers = own_seat_flowers(player.seat)
    for flower in flowers:
        if flower in seat_flowers:
            yaku.append(("花牌", 1))

    # 搶槓
    if is_qiangang:
        yaku.append(("搶槓", 1))

    # 獨聽: waiting on exactly one tile (single wait)
    # This is passed externally; we don't compute it here since it requires
    # full wait analysis which is outside the decomposition scope.

    # 槓上開花
    if is_gangshang:
        yaku.append(("槓上開花", 1))

    # 海底撈月 (self-draw on last tile) / 河底撈魚 (win on last discard)
    if is_haidi:
        if is_self_draw:
            yaku.append(("海底撈月", 1))
        else:
            yaku.append(("河底撈魚", 1))

    # ---------------------------------------------------------------
    # Compute totals
    # ---------------------------------------------------------------
    subtotal = sum(tai for _, tai in yaku)

    # Minimum 1 tai if no yaku (雞胡 is not a standard rule in Taiwan 16-tile,
    # but we ensure at least 1 tai for payment calculation)
    if subtotal == 0:
        subtotal = 1

    total = min(subtotal, MAX_TAI)

    payments = _compute_payments(
        gs=gs,
        winner_idx=winner_idx,
        total_tai=total,
        is_self_draw=is_self_draw,
        discarder_idx=discarder_idx,
    )

    return ScoringResult(
        yaku=yaku,
        subtotal=subtotal,
        total=total,
        payments=payments,
    )


# ---------------------------------------------------------------------------
# Payment computation
# ---------------------------------------------------------------------------


def _compute_payments(
    gs: GameState,
    winner_idx: int,
    total_tai: int,
    is_self_draw: bool,
    discarder_idx: Optional[int],
) -> dict[int, int]:
    """Compute payment amounts for each player.

    Positive values = amount owed to the winner.
    The winner's entry is the negative total (amount received).

    拉莊 (lazhuang): dealer's streak count, paid by all non-winners
    regardless of who discarded.

    Self-draw: each of the 3 other players pays total_tai + lazhuang.
    Discard: discarder pays total_tai + lazhuang; other 2 non-winners pay lazhuang only.
    """
    dealer = gs.players[gs.dealer_index]
    lazhuang = dealer.streak

    payments: dict[int, int] = {}
    total_received = 0

    for i in range(4):
        if i == winner_idx:
            continue

        if is_self_draw:
            # All 3 pay tai + lazhuang
            amount = total_tai + lazhuang
        else:
            if i == discarder_idx:
                amount = total_tai + lazhuang
            else:
                amount = lazhuang

        payments[i] = amount
        total_received += amount

    # Winner receives the total
    payments[winner_idx] = -total_received

    return payments


# ---------------------------------------------------------------------------
# Helper functions for yaku detection
# ---------------------------------------------------------------------------


def _is_triplet(s: list[str]) -> bool:
    """Check if a set of tiles is a triplet (3 identical tiles)."""
    return len(s) >= 3 and s[0] == s[1] == s[2]


def _is_sequence(s: list[str]) -> bool:
    """Check if a set of tiles is a sequence (3 consecutive number tiles of same suit)."""
    if len(s) < 3:
        return False
    if not all(is_number_tile(t) for t in s):
        return False
    suits = [tile_suit(t) for t in s]
    if len(set(suits)) != 1:
        return False
    vals = sorted(tile_value(t) for t in s)
    return vals[1] == vals[0] + 1 and vals[2] == vals[1] + 1


def _count_concealed_triplets(
    sets: list[list[str]],
    is_self_draw: bool,
    win_tile: str,
) -> int:
    """Count concealed triplets in the decomposed sets.

    A concealed triplet is one formed entirely from drawn tiles.
    If winning by discard, one triplet containing the win_tile might
    not be concealed — but for simplicity, if the set is in the concealed
    decomposition and is a triplet, we count it.
    On discard win, if the win_tile forms a triplet, that triplet is
    not concealed (the last tile came from another player).
    """
    count = 0
    win_tile_used = False
    for s in sets:
        if _is_triplet(s):
            # On discard, one triplet containing win_tile is not concealed
            if not is_self_draw and not win_tile_used and s[0] == win_tile:
                win_tile_used = True
                continue
            count += 1
    return count


def _count_dragon_triplets(all_sets: list[list[str]], melds: list[Meld]) -> int:
    """Count how many dragon triplets exist in all sets."""
    count = 0
    for s in all_sets:
        if _is_triplet(s) and is_dragon_tile(s[0]):
            count += 1
    # Also count kong melds with dragons
    for m in melds:
        if m.type in ("concealed_kong", "open_kong", "added_kong") and is_dragon_tile(m.tiles[0]):
            # Already counted in all_sets if from decomposition, avoid double count
            pass
    return count


def _count_wind_triplets(all_sets: list[list[str]], melds: list[Meld]) -> int:
    """Count how many wind triplets exist in all sets."""
    count = 0
    for s in all_sets:
        if _is_triplet(s) and is_wind_tile(s[0]):
            count += 1
    return count


def _has_wind_triplet(all_sets: list[list[str]], melds: list[Meld], wind: str) -> bool:
    """Check if there is a triplet of the specified wind tile."""
    for s in all_sets:
        if _is_triplet(s) and s[0] == wind:
            return True
    return False


def _has_dragon_triplet(all_sets: list[list[str]], melds: list[Meld], dragon: str) -> bool:
    """Check if there is a triplet of the specified dragon tile."""
    for s in all_sets:
        if _is_triplet(s) and s[0] == dragon:
            return True
    return False


def _all_honors(full_hand: list[str], melds: list[Meld]) -> bool:
    """Check if all tiles (hand + melds) are honor tiles."""
    for tile in full_hand:
        if not is_honor_tile(tile):
            return False
    for m in melds:
        for tile in m.tiles:
            if not is_honor_tile(tile):
                return False
    return True


def _is_qingyise(full_hand: list[str], melds: list[Meld]) -> bool:
    """清一色: all tiles are number tiles of one suit (no honors)."""
    all_tiles = list(full_hand)
    for m in melds:
        all_tiles.extend(m.tiles)

    if not all(is_number_tile(t) for t in all_tiles):
        return False

    suits_used = {tile_suit(t) for t in all_tiles}
    return len(suits_used) == 1


def _is_hunyise(full_hand: list[str], melds: list[Meld]) -> bool:
    """湊一色(混一色): one suit + honors only."""
    all_tiles = list(full_hand)
    for m in melds:
        all_tiles.extend(m.tiles)

    number_suits: set[str] = set()
    has_honors = False

    for tile in all_tiles:
        if is_number_tile(tile):
            number_suits.add(tile_suit(tile))
        elif is_honor_tile(tile):
            has_honors = True
        else:
            return False

    # Must have exactly one number suit AND some honors
    return len(number_suits) == 1 and has_honors


def _is_duiduihu(all_sets: list[list[str]], melds: list[Meld]) -> bool:
    """對對胡: all 5 sets are triplets (no sequences)."""
    for s in all_sets:
        if not _is_triplet(s):
            return False
    return len(all_sets) == 5


def _is_pinghu(
    all_sets: list[list[str]],
    pair: list[str],
    full_hand: list[str],
    melds: list[Meld],
    is_self_draw: bool,
    is_two_sided_wait: bool,
) -> bool:
    """平胡: 5 sequences + pair, all number tiles, two-sided wait, not self-draw.

    Requirements:
    - All 5 sets are sequences
    - Pair is number tiles
    - All tiles are number tiles (no honors)
    - Two-sided wait
    - Win by discard (not self-draw)
    - No open melds (must be fully concealed)
    """
    if melds:  # 平胡 requires fully concealed hand
        return False

    if is_self_draw:
        return False

    if not is_two_sided_wait:
        return False

    # Check all tiles are number tiles
    all_tiles = list(full_hand)
    for m in melds:
        all_tiles.extend(m.tiles)
    if not all(is_number_tile(t) for t in all_tiles):
        return False

    # Check pair is number tiles
    if not pair or not is_number_tile(pair[0]):
        return False

    # All 5 sets must be sequences
    if len(all_sets) != 5:
        return False
    for s in all_sets:
        if not _is_sequence(s):
            return False

    return True
