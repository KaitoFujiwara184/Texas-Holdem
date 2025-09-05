import random
from Card import Card
from HandEvaluator import hand_strength, best_hand
from Player import Player

class TexasHoldem:
    POSITION_NAMES = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']

    def __init__(self):
        self.players = [Player(f"Player {i+1}", 100) for i in range(6)]
        self.deck = []
        self.board = []
        self.pot = 0
        self.small_blind = 0.5
        self.big_blind = 1
        self.dealer_position = 0
        # 以下は Web インターフェース向けの進行管理用
        self.stage = None  # 'preflop', 'flop', 'turn', 'river', 'showdown'
        self.action_order = []
        self.action_index = 0
        self.current_bet = 0
        self.winner = None
        # ショーダウン情報
        self.showdown_hands = {}
        self.showdown_payouts = {}
        self.side_pots = []

    def assign_positions(self):
        for i in range(6):
            pos_index = (self.dealer_position + 3 + i) % 6
            self.players[pos_index].position = TexasHoldem.POSITION_NAMES[i]

    def create_deck(self):
        self.deck = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]
        random.shuffle(self.deck)

    def deal_hole_cards(self):
        for player in self.players:
            player.hand = [self.deck.pop(), self.deck.pop()]

    def rotate_positions(self):
        self.dealer_position = (self.dealer_position + 1) % len(self.players)

    def post_blinds(self):
        sb_pos = (self.dealer_position + 1) % 6
        bb_pos = (self.dealer_position + 2) % 6

        self.players[sb_pos].current_bet = self.small_blind
        self.players[sb_pos].stack -= self.small_blind

        self.players[bb_pos].current_bet = self.big_blind
        self.players[bb_pos].stack -= self.big_blind

        self.pot += self.small_blind + self.big_blind

    def check_for_winner_after_fold(self):
        """ベッティングラウンド中に一人以外がフォールドした場合、勝者を決定する"""
        active_players = [player for player in self.players if player.in_hand]
        if len(active_players) == 1:
            winner = active_players[0]
            if self.pot > 0:  
                print(f"\n{winner.name} wins the pot of {self.pot} as all other players folded!")
                winner.stack += self.pot 
                self.pot = 0

                print("\n-- Final Player States --")
                for player in self.players:
                    print(player)
            return True
        return False

    def update_side_pots(self):
        """現在のベット額に基づいてサイドポットを再計算する"""
        contributions = {
            p: p.total_bet + p.current_bet for p in self.players if p.total_bet + p.current_bet > 0
        }
        sorted_players = sorted(contributions.items(), key=lambda x: x[1])
        pots = []
        prev = 0
        players_remaining = [p for p, _ in sorted_players]
        for player, amount in sorted_players:
            if amount > prev:
                pot_amt = (amount - prev) * len(players_remaining)
                eligible = [pl for pl in players_remaining if pl.in_hand]
                if pot_amt > 0:
                    pots.append({"amount": pot_amt, "players": eligible})
                prev = amount
            players_remaining.remove(player)
        self.side_pots = pots

    def betting_round(self, stage):
        print(f"\n--- {stage.upper()} BETTING ROUND ---")
        print(f"total pot {self.pot}")
        current_bet = max(p.current_bet for p in self.players)
        players_in_hand = [p for p in self.players if p.in_hand]
        action_order = self.get_action_order(stage)

        bb_position = (self.dealer_position + 2) % len(self.players)  # BBの位置
        bb_player = self.players[bb_position]
        bb_has_option = (stage == 'preflop' and current_bet == self.big_blind)  # プリフロップでレイズがない場合

        while True:
            for player in action_order:
                if not player.in_hand or player.stack == 0:
                    continue
                if player.current_bet < current_bet or not player.has_acted:
                    print(f"\n{player.name}'s turn (stack: {player.stack}, bet: {player.current_bet}, to call: {current_bet - player.current_bet})")
                    if player == bb_player and bb_has_option and current_bet == self.big_blind:
                        move = input("Enter action (call/raise): ").strip().lower()
                    else:
                        move = input("Enter action (fold/call/raise): ").strip().lower()

                    if move == 'fold':
                        if player == bb_player and bb_has_option and current_bet == self.big_blind:
                            print("Big Blind cannot fold as no raise has been made.")
                            continue
                        player.in_hand = False
                        if self.check_for_winner_after_fold():
                            return
                    elif move == 'call':
                        to_call = current_bet - player.current_bet
                        actual_call = min(to_call, player.stack)
                        player.stack -= actual_call
                        player.current_bet += actual_call
                        self.pot += actual_call
                    elif move == 'raise':
                        while True:
                            min_raise = max(self.big_blind, 2 * (current_bet))
                            raise_amount = int(input(f"Enter raise amount (minimum: {min_raise}): "))
                            if raise_amount < min_raise:
                                print(f"Raise amount must be at least {min_raise}.")
                                continue
                            if raise_amount > player.stack + player.current_bet:
                                raise_amount = player.stack + player.current_bet
                            self.pot += raise_amount - player.current_bet
                            player.stack -= (raise_amount - player.current_bet)
                            player.current_bet = raise_amount
                            current_bet = raise_amount
                            # レイズ後に他のプレイヤーのアクションをリセット
                            for p in players_in_hand:
                                if p != player:
                                    p.has_acted = False
                            break
                    player.has_acted = True
                    self.update_side_pots()

            # すべてのプレイヤーが現在のベット額に一致しているか、スタックが 0 またはフォールドしている場合に終了
            all_done = all((p.current_bet == current_bet or p.stack == 0 or not p.in_hand) for p in players_in_hand)
            if all_done:
                break

        for player in self.players:
            player.total_bet += player.current_bet
            player.current_bet = 0
            player.has_acted = False
        self.update_side_pots()

    def get_action_order(self, stage):
        if stage == 'preflop':
            start = (self.dealer_position + 3) % 6
        else:
            start = (self.dealer_position + 1) % 6 
        order = []
        for i in range(6):
            pos = (start + i) % 6
            order.append(self.players[pos])
        return order

    def deal_board(self, stage):
        if stage == 'flop':
            self.board += [self.deck.pop() for _ in range(3)]
        elif stage in ('turn', 'river'):
            self.board.append(self.deck.pop())
        print(f"\nBoard ({stage}): {' '.join(map(str, self.board))}")

    def determine_winner(self):
        active_players = [p for p in self.players if p.in_hand]
        self.showdown_hands = {}
        best_hands = {}
        for player in active_players:
            player_best_hand = best_hand(player.hand + self.board)
            strength, hand_name = hand_strength(player_best_hand)
            best_hands[player] = (player_best_hand, (strength, hand_name))
            self.showdown_hands[player.name] = {
                'hand': list(player.hand),
                'best': player_best_hand,
                'hand_name': hand_name,
            }

        print("\n-- Showdown --")
        for p in active_players:
            hand_str = ' '.join(map(str, self.showdown_hands[p.name]['hand']))
            best_str = ' '.join(map(str, self.showdown_hands[p.name]['best']))
            name = self.showdown_hands[p.name]['hand_name']
            print(f"{p.name}: {hand_str} -> {name} ({best_str})")

        self.update_side_pots()

        payouts = {}
        main_pot_winners = []
        for i, pot in enumerate(self.side_pots):
            amount = pot["amount"]
            eligible = [p for p in pot["players"] if p.in_hand]
            if not eligible:
                self.pot -= amount
                continue
            best_strength = max(best_hands[p][1][0] for p in eligible)
            winners = [p for p in eligible if best_hands[p][1][0] == best_strength]
            split = amount / len(winners)
            for j, w in enumerate(winners):
                if j == len(winners) - 1:
                    win = amount - split * (len(winners) - 1)
                else:
                    win = split
                w.stack += win
                payouts[w.name] = payouts.get(w.name, 0) + win
                print(f"{w.name} wins {win} chips from pot {i+1}")
            self.pot -= amount
            if i == 0:
                main_pot_winners = winners

        self.showdown_payouts = payouts

        print("\n-- Final Player States --")
        for player in self.players:
            print(player)

        if main_pot_winners:
            self.winner = ", ".join(w.name for w in main_pot_winners)
            return self.winner
        return None

    # Web アプリ用のメソッド
    def start_hand(self):
        """ゲームを初期化して新しいハンドを開始する"""
        self.board = []
        self.pot = 0
        self.winner = None
        self.showdown_hands = {}
        self.showdown_payouts = {}
        self.side_pots = []

        for player in self.players:
            if player.stack == 0:
                player.stack = 100
            player.reset_for_new_round()

        self.create_deck()
        self.deal_hole_cards()
        self.rotate_positions()
        self.assign_positions()
        self.post_blinds()


        self.stage = 'preflop'
        self.current_bet = self.big_blind
        self.action_order = self.get_action_order('preflop')
        self.action_index = 0
        self.current_player()

    def current_player(self):
        for _ in range(len(self.action_order)):
            player = self.action_order[self.action_index]
            if player.in_hand and player.stack > 0:
                return player
            self.action_index = (self.action_index + 1) % len(self.action_order)
        return self.action_order[self.action_index]

    def process_action(self, action, amount=0):
        """現在のプレイヤーのアクションを処理する"""
        if self.stage is None or self.stage == 'showdown':
            return

        player = self.current_player()

        if action == 'fold':
            player.in_hand = False
        elif action == 'call':
            to_call = self.current_bet - player.current_bet
            actual_call = min(to_call, player.stack)
            player.stack -= actual_call
            player.current_bet += actual_call
            self.pot += actual_call
        elif action == 'raise':
            raise_to = max(amount, self.current_bet + self.big_blind)
            if raise_to > player.stack + player.current_bet:
                raise_to = player.stack + player.current_bet
            diff = raise_to - player.current_bet
            player.stack -= diff
            player.current_bet = raise_to
            self.pot += diff
            self.current_bet = raise_to
            for p in self.players:
                if p != player and p.in_hand:
                    p.has_acted = False
        player.has_acted = True
        self.update_side_pots()

        self.action_index = (self.action_index + 1) % len(self.action_order)
        for _ in range(len(self.action_order)):
            nxt = self.action_order[self.action_index]
            if nxt.in_hand and nxt.stack > 0:
                break
            self.action_index = (self.action_index + 1) % len(self.action_order)

        players_in_hand = [p for p in self.players if p.in_hand]
        if len(players_in_hand) == 1:
            for p in self.players:
                p.total_bet += p.current_bet
                p.current_bet = 0
                p.has_acted = False
            self.update_side_pots()
            self.skip_to_showdown()
            return

        players_can_act = [p for p in players_in_hand if p.stack > 0]

        all_done = all(
            (p.current_bet == self.current_bet or p.stack == 0) and
            (p.has_acted or p.stack == 0)
            for p in players_in_hand
        )
        if all_done:
            for p in self.players:
                p.total_bet += p.current_bet
                p.current_bet = 0
                p.has_acted = False
            self.update_side_pots()
            p.has_acted = (p.stack == 0)

            players_in_hand = [p for p in self.players if p.in_hand]
            players_can_act = [p for p in players_in_hand if p.stack > 0]

            if len(players_can_act) <= 1:
                self.skip_to_showdown()
                return

            if self.stage == 'preflop':
                self.stage = 'flop'
                self.deal_board('flop')
            elif self.stage == 'flop':
                self.stage = 'turn'
                self.deal_board('turn')
            elif self.stage == 'turn':
                self.stage = 'river'
                self.deal_board('river')
            else:
                self.stage = 'showdown'
                self.winner = self.determine_winner()
                return

            self.current_bet = 0
            self.action_order = self.get_action_order(self.stage)
            self.action_index = 0
            self.current_player()


    def skip_to_showdown(self):
        """残りのコミュニティカードをすべてめくってショーダウンに進む"""
        if self.stage == 'preflop':
            self.deal_board('flop')
            self.deal_board('turn')
            self.deal_board('river')
        elif self.stage == 'flop':
            self.deal_board('turn')
            self.deal_board('river')
        elif self.stage == 'turn':
            self.deal_board('river')
        self.stage = 'showdown'

        active_players = [p for p in self.players if p.in_hand]
        if len(active_players) == 1:
            winner = active_players[0]
            winner.stack += self.pot
            self.showdown_payouts = {winner.name: self.pot}
            self.showdown_hands = {
                winner.name: {
                    'hand': list(winner.hand),
                    'best': [],
                    'hand_name': 'No showdown',
                }
            }
            self.pot = 0
            self.winner = winner.name
        else:
            self.winner = self.determine_winner()
            
    def play_hand(self):
        self.board = []
        self.pot = 0
        self.side_pots = []

        for player in self.players:
            if player.stack == 0:
                player.stack = 100
            player.reset_for_new_round()

        self.create_deck()
        self.deal_hole_cards()
        self.rotate_positions()
        self.assign_positions()
        self.post_blinds()

        print("\n-- Player Positions --")
        for player in self.players:
            print(player)

        self.betting_round('preflop')
        if self.check_for_winner_after_fold():
            return

        self.deal_board('flop')
        self.betting_round('flop')
        if self.check_for_winner_after_fold():
            return

        self.deal_board('turn')
        self.betting_round('turn')
        if self.check_for_winner_after_fold():
            return

        self.deal_board('river')
        self.betting_round('river')
        if self.check_for_winner_after_fold():
            return

        # ショーダウンによる勝者判定
        print(f"\nPot total: {self.pot}")
        self.determine_winner()  # クラス内メソッドとして呼び出し


if __name__ == "__main__":
    game = TexasHoldem()

    while True:
        print("\n--- Starting a new hand ---")
        game.play_hand()


        continue_game = input("\nDo you want to play another hand? (yes/no): ").strip().lower()
        if continue_game != 'yes':
            print("Exiting the game.")
            break
