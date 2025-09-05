class Player:
    def __init__(self, name, stack):
        self.name = name
        self.stack = stack
        self.hand = []
        self.in_hand = True
        self.current_bet = 0
        self.total_bet = 0
        self.has_acted = False
        self.position = ""

    def __str__(self):
        hand_str = ", ".join(str(card) for card in self.hand)  # カードを文字列化
        return f"{self.name} ({self.position}) - Stack: {self.stack}, Bet: {self.current_bet}, Hand: [{hand_str}]"

    def reset_for_new_round(self):
        self.in_hand = True
        self.current_bet = 0
        self.total_bet = 0
        self.has_acted = False
        self.hand = []
        self.position = ""
