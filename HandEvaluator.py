from itertools import combinations
from collections import Counter


RANK_ORDER = "23456789TJQKA"
RANK_VALUE = {r: i for i, r in enumerate(RANK_ORDER)}
REVERSE_RANK_ORDER = RANK_ORDER[::-1]  # "AKQJT98765432"


def hand_strength(hand):
    hand = sorted(hand, key=lambda c: RANK_VALUE[c.rank], reverse=True)
    counts = Counter(card.rank for card in hand)
    count_vals = list(reversed(sorted(counts.values())))
    groups = sorted(counts.items(), key=lambda c: (c[1], RANK_VALUE[c[0]]), reverse=True)

    ranks = "".join(card.rank for card in hand)
    suits = [card.suit for card in hand]
    is_flush = len(set(suits)) == 1
    is_straight = ranks in REVERSE_RANK_ORDER or ranks == "A5432"
    if ranks == "A5432":
        straight_vals = (
            RANK_VALUE["5"],
            RANK_VALUE["4"],
            RANK_VALUE["3"],
            RANK_VALUE["2"],
            -1,
        )
    else:
        straight_vals = tuple(RANK_VALUE[r] for r in ranks)

    if is_flush and ranks == "AKQJT":
        return (9,) + tuple(RANK_VALUE[r] for r, _ in groups), "ロイヤルストレートフラッシュ"
    elif is_flush and is_straight:
        return (8,) + straight_vals, "ストレートフラッシュ"
    elif count_vals == [4, 1]:
        primary, kicker = groups[0][0], groups[1][0]
        return (7, RANK_VALUE[primary], RANK_VALUE[kicker]), "フォーカード"
    elif count_vals == [3, 2]:
        primary, secondary = groups[0][0], groups[1][0]
        return (6, RANK_VALUE[primary], RANK_VALUE[secondary]), "フルハウス"
    elif is_flush:
        return (5,) + tuple(RANK_VALUE[r] for r, _ in groups), "フラッシュ"
    elif is_straight:
        return (4,) + straight_vals, "ストレート"
    elif count_vals == [3, 1, 1]:
        primary, kicker1, kicker2 = groups[0][0], groups[1][0], groups[2][0]
        return (
            3,
            RANK_VALUE[primary],
            RANK_VALUE[kicker1],
            RANK_VALUE[kicker2],
        ), "スリーカード"
    elif count_vals == [2, 2, 1]:
        primary, secondary, kicker = groups[0][0], groups[1][0], groups[2][0]
        return (
            2,
            RANK_VALUE[primary],
            RANK_VALUE[secondary],
            RANK_VALUE[kicker],
        ), "ツーペア"
    elif count_vals == [2, 1, 1, 1]:
        primary, kicker1, kicker2, kicker3 = (
            groups[0][0],
            groups[1][0],
            groups[2][0],
            groups[3][0],
        )
        return (
            1,
            RANK_VALUE[primary],
            RANK_VALUE[kicker1],
            RANK_VALUE[kicker2],
            RANK_VALUE[kicker3],
        ), "ワンペア"
    else:
        return (0,) + tuple(RANK_VALUE[r] for r, _ in groups), "ハイカード"


def best_hand(cards):
    """最強の役とカードを左から順に並べて返す"""
    best = max(combinations(cards, 5), key=lambda hand: hand_strength(hand)[0])
    _, hand_name = hand_strength(best)

    # カードを役に応じて並べ替える
    if hand_name in ["ロイヤルストレートフラッシュ", "ストレートフラッシュ", "ストレート"]:
        # ストレート系はランク順に並べる
        sorted_hand = sorted(best, key=lambda c: RANK_VALUE[c.rank], reverse=True)
    elif hand_name in ["フラッシュ", "ハイカード"]:
        # フラッシュやハイカードはランク順に並べる
        sorted_hand = sorted(best, key=lambda c: RANK_VALUE[c.rank], reverse=True)
    elif hand_name in ["フォーカード", "フルハウス", "スリーカード", "ツーペア", "ワンペア"]:
        # グループ化して役の強さ順に並べる
        counts = Counter(card.rank for card in best)
        sorted_hand = sorted(best, key=lambda c: (counts[c.rank], RANK_VALUE[c.rank]), reverse=True)
    else:
        # その他の場合もランク順に並べる
        sorted_hand = sorted(best, key=lambda c: RANK_VALUE[c.rank], reverse=True)

    return sorted_hand

