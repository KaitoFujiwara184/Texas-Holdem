class Card:
    SUITS = ['c', 'd', 'h', 's']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}{self.suit}"  # カードのランクとスートを文字列として返す

    def rank_value(self):
        return Card.RANKS.index(self.rank)
