import tkinter as tk
from tkinter import font as tkFont, scrolledtext
import random
import os

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

class Card:
    def __init__(self, rank, suit, image_path):
        self.rank = rank
        self.suit = suit
        self.image_path = image_path

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self, card_folder="cards_polished"):
        self.cards = []
        for suit in SUITS:
            for rank in RANKS:
                filename = f"{rank}_of_{suit}.png"
                path = os.path.join(card_folder, filename)
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Missing card image: {path}")
                self.cards.append(Card(rank, suit, path))
        random.shuffle(self.cards)

    def deal(self):
        if self.cards:
            return self.cards.pop()
        return None

def rank_hand(cards):
    from collections import Counter
    values = sorted([RANK_VALUES[c.rank] for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    vcount = Counter(values)
    scount = Counter(suits)

    is_flush = any(count >= 5 for count in scount.values())
    unique_vals = sorted(set(values), reverse=True)
    is_straight, straight_high = check_straight(unique_vals)

    freqs = sorted(vcount.values(), reverse=True)
    if 4 in freqs:
        quad_val = get_key_by_value(vcount, 4)
        kicker = max(v for v in values if v != quad_val)
        return (8, quad_val, kicker)
    if 3 in freqs and 2 in freqs:
        three_val = get_key_by_value(vcount, 3)
        pair_val = get_key_by_value(vcount, 2)
        return (7, three_val, pair_val)
    if is_flush:
        sf_high = straight_flush_high(cards)
        if sf_high:
            return (9, sf_high)
        flush_cards = flush_top_values(cards)
        return (6,) + tuple(flush_cards)
    if is_straight:
        return (5, straight_high)
    if 3 in freqs:
        three_val = get_key_by_value(vcount, 3)
        kickers = sorted([v for v in values if v != three_val], reverse=True)[:2]
        return (4, three_val) + tuple(kickers)
    if freqs.count(2) >= 2:
        pairs = [k for k, cnt in vcount.items() if cnt == 2]
        pairs = sorted(pairs, reverse=True)
        kicker = max(v for v in values if v not in pairs)
        return (3, pairs[0], pairs[1], kicker)
    if 2 in freqs:
        pair_val = get_key_by_value(vcount, 2)
        kickers = sorted([v for v in values if v != pair_val], reverse=True)[:3]
        return (2, pair_val) + tuple(kickers)
    top_five = values[:5]
    return (1,) + tuple(top_five)

def flush_top_values(cards):
    from collections import defaultdict
    suit_cards = defaultdict(list)
    for c in cards:
        suit_cards[c.suit].append(RANK_VALUES[c.rank])
    for s, vals in suit_cards.items():
        if len(vals) >= 5:
            return sorted(vals, reverse=True)[:5]
    return []

def get_key_by_value(counter, val):
    for k, v in counter.items():
        if v == val:
            return k

def check_straight(vals):
    if 14 in vals:
        temp = vals + [1]
    else:
        temp = vals
    current_len = 1
    best_high = None
    for i in range(len(temp)-1):
        if temp[i] - 1 == temp[i+1]:
            current_len += 1
            if current_len >= 5:
                best_high = temp[i-3]
        elif temp[i] != temp[i+1]:
            current_len = 1
    if best_high is not None:
        return True, best_high
    return False, None

def straight_flush_high(cards):
    from collections import defaultdict
    suit_cards = defaultdict(list)
    for c in cards:
        suit_cards[c.suit].append(RANK_VALUES[c.rank])
    for s, vals in suit_cards.items():
        vals = sorted(set(vals), reverse=True)
        is_str, high = check_straight(vals)
        if is_str:
            return high
    return None

def best_five_from_seven(cards):
    from itertools import combinations
    best = None
    for combo in combinations(cards, 5):
        val = rank_hand(list(combo))
        if best is None or val > best:
            best = val
    return best

def hand_description(val):
    rank_type = val[0]
    if rank_type == 9:
        high_card = val[1]
        if high_card == 14:
            return "Royal Flush"
        return "Straight Flush"
    elif rank_type == 8:
        return "Four of a Kind"
    elif rank_type == 7:
        return "Full House"
    elif rank_type == 6:
        return "Flush"
    elif rank_type == 5:
        return "Straight"
    elif rank_type == 4:
        return "Three of a Kind"
    elif rank_type == 3:
        return "Two Pair"
    elif rank_type == 2:
        return "One Pair"
    else:
        return "High Card"

class Player:
    def __init__(self, name, chips=1000, is_human=False):
        self.name = name
        self.chips = chips
        self.cards = []
        self.is_human = is_human
        self.folded = False
        self.current_bet = 0
        self.last_action = ""

    def reset_hand(self):
        self.cards = []
        self.folded = False
        self.current_bet = 0
        self.last_action = ""

    def bet(self, amount):
        actual = min(amount, self.chips)
        self.chips -= actual
        self.current_bet += actual
        return actual

    def fold(self):
        self.folded = True
        self.last_action = "Fold"

    def __str__(self):
        return f"{self.name} ({'Human' if self.is_human else 'AI'}): {self.chips} chips"

def ai_decision(player, community_cards, current_bet, pot, stage):
    call_needed = current_bet - player.current_bet
    if call_needed > player.chips:
        return "fold"
    if call_needed > (player.chips * 0.5):
        if random.random() < 0.5:
            return "fold"
        else:
            return "call"
    if random.random() < 0.1 and player.chips > call_needed + 50:
        return "raise"
    return "call"

class TexasHoldemGame:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x600")  # Wider window for horizontal layout

        self.deck = Deck()
        self.players = [
            Player("You", 1000, is_human=True),
            Player("AI1", 1000),
            Player("AI2", 1000),
            Player("AI3", 1000),
            Player("AI4", 1000),
        ]

        self.dealer_index = 0
        self.small_blind = 10
        self.big_blind = 20

        self.current_player_index = 0
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.betting_completed = False
        self.continue_button = None

        self.card_images = {}
        self.card_back_image = None
        self.load_images("cards_polished")

        self.setup_ui()
        self.start_hand()

    def load_images(self, folder):
        # Smaller cards again, say subsample(6,6)
        scale_factor = (3, 3)
        back_path = os.path.join(folder, "card_back.png")
        back_img = tk.PhotoImage(file=back_path).subsample(*scale_factor)
        self.card_back_image = back_img

        for suit in SUITS:
            for rank in RANKS:
                filename = f"{rank}_of_{suit}.png"
                path = os.path.join(folder, filename)
                img = tk.PhotoImage(file=path).subsample(*scale_factor)
                self.card_images[(rank, suit)] = img

    def setup_ui(self):
        self.root.title("Texas Hold'em v1.13")

        bg_main = "#F0F0F0"
        bg_info = "#F8F8F8"
        bg_game = "#EEEEEE"
        bg_player_frame = "#FFFFFF"
        bg_community_frame = "#DDDDDD"
        bg_action = "#D0D0D0"

        self.bold_font = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.status_font = tkFont.Font(family="Helvetica", size=10, slant="italic")

        self.root.configure(bg=bg_main)

        # Top info bar
        self.info_frame = tk.Frame(self.root, bg=bg_info)
        self.info_frame.pack(side=tk.TOP, fill=tk.X)
        self.status_label = tk.Label(self.info_frame, text="Welcome to Texas Hold'em!", fg="black", bg=bg_info, font=self.status_font)
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Action frame at the bottom for buttons
        self.action_frame = tk.Frame(self.root, bg=bg_action, bd=2, relief=tk.RAISED)
        self.action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.call_button = tk.Button(self.action_frame, text="Call/Check", command=self.human_call, bg="#C0C0C0", fg="black")
        self.call_button.pack(side=tk.LEFT, padx=5)
        self.fold_button = tk.Button(self.action_frame, text="Fold", command=self.human_fold, bg="#C0C0C0", fg="black")
        self.fold_button.pack(side=tk.LEFT, padx=5)
        self.bet_button = tk.Button(self.action_frame, text="Bet/Raise 50", command=self.human_bet, bg="#C0C0C0", fg="black")
        self.bet_button.pack(side=tk.LEFT, padx=5)

        # Main game area
        self.game_frame = tk.Frame(self.root, bg=bg_game)
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # On the right side, a log
        self.log_frame = tk.Frame(self.root, bg=bg_main)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.log_frame, text="Game Log:", bg=bg_main, fg="black", font=self.bold_font).pack(anchor='w')
        self.log_text = scrolledtext.ScrolledText(self.log_frame, width=40, height=35, bg="#FFFFFF")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Community cards & Pot/Stage at top center of the game frame
        top_area = tk.Frame(self.game_frame, bg=bg_game)
        top_area.pack(side=tk.TOP, pady=10)

        self.stage_label = tk.Label(top_area, text="Stage: Preflop", font=self.bold_font, fg="black", bg=bg_game)
        self.stage_label.pack(side=tk.TOP, pady=5)

        self.pot_label = tk.Label(top_area, text="Pot: 0", font=self.bold_font, fg="black", bg=bg_game)
        self.pot_label.pack(side=tk.TOP, pady=5)

        self.community_frame = tk.Frame(top_area, bd=2, relief=tk.RIDGE, bg=bg_community_frame, padx=5, pady=5)
        self.community_frame.pack(side=tk.TOP, pady=10)

        # Players arranged horizontally at the bottom of the game_frame
        self.players_frame = tk.Frame(self.game_frame, bg=bg_game)
        self.players_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.player_frames = []
        for p in self.players:
            f = tk.Frame(self.players_frame, bd=2, relief=tk.GROOVE, bg=bg_player_frame, padx=5, pady=5)
            f.pack(side=tk.LEFT, padx=5)
            self.player_frames.append(f)

    def log(self, message):
        """Append a line to the game log."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)

    def start_hand(self):
        self.deck = Deck()
        for p in self.players:
            p.reset_hand()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.betting_completed = False

        if self.continue_button:
            self.continue_button.destroy()
            self.continue_button = None

        self.deal_hole_cards()
        self.post_blinds()
        self.update_ui()

        # Log start of a new hand
        self.log("---- New Hand Started ----")
        self.log(f"Dealer: {self.players[self.dealer_index].name}")

        self.current_player_index = (self.dealer_index + 3) % len(self.players)
        self.root.after(1000, self.run_betting_round)

    def deal_hole_cards(self):
        for _ in range(2):
            for p in self.players:
                p.cards.append(self.deck.deal())

    def post_blinds(self):
        sb_player = self.players[(self.dealer_index + 1) % len(self.players)]
        sb_amount = sb_player.bet(self.small_blind)
        sb_player.last_action = f"Post SB {sb_amount}"
        self.pot += sb_amount

        bb_player = self.players[(self.dealer_index + 2) % len(self.players)]
        bb_amount = bb_player.bet(self.big_blind)
        bb_player.last_action = f"Post BB {bb_amount}"
        self.pot += bb_amount
        self.current_bet = self.big_blind

        self.status_label.config(text=f"{sb_player.name} posts SB {sb_amount}, {bb_player.name} posts BB {bb_amount}")
        self.log(f"{sb_player.name} posts SB {sb_amount}")
        self.log(f"{bb_player.name} posts BB {bb_amount}")

    def run_betting_round(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            self.single_player_win(active_players[0])
            return

        if self.betting_completed:
            self.next_stage()
            return

        current_player = self.players[self.current_player_index]
        if current_player.folded:
            self.next_player()
            return

        if current_player.is_human:
            return
        else:
            action = ai_decision(current_player, self.community_cards, self.current_bet, self.pot, self.stage)
            required = self.current_bet - current_player.current_bet
            if action == "fold":
                current_player.fold()
                self.status_label.config(text=f"{current_player.name} folds.")
                self.log(f"{current_player.name} folds.")
            elif action == "call":
                if required > 0:
                    added = current_player.bet(required)
                    self.pot += added
                    current_player.last_action = "Call"
                    self.status_label.config(text=f"{current_player.name} calls {required}.")
                    self.log(f"{current_player.name} calls {required}")
                else:
                    current_player.last_action = "Check"
                    self.status_label.config(text=f"{current_player.name} checks.")
                    self.log(f"{current_player.name} checks")
            elif action == "raise":
                call_amount = current_player.bet(required)
                raise_amount = 50
                extra = current_player.bet(raise_amount)
                self.pot += (call_amount + extra)
                self.current_bet += extra
                current_player.last_action = "Raise 50"
                self.status_label.config(text=f"{current_player.name} raises by 50.")
                self.log(f"{current_player.name} raises by 50")

            self.update_ui()
            self.next_player()

    def next_player(self):
        if self.check_betting_complete():
            self.betting_completed = True
            self.root.after(1000, self.run_betting_round)
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.root.after(1000, self.run_betting_round)

    def check_betting_complete(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            return True
        for p in active_players:
            if p.current_bet < self.current_bet and p.chips > 0:
                return False
        return True

    def next_stage(self):
        if self.stage == "preflop":
            for _ in range(3):
                self.community_cards.append(self.deck.deal())
            self.stage = "flop"
        elif self.stage == "flop":
            self.community_cards.append(self.deck.deal())
            self.stage = "turn"
        elif self.stage == "turn":
            self.community_cards.append(self.deck.deal())
            self.stage = "river"
        elif self.stage == "river":
            self.do_showdown()
            return

        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.last_action = ""

        self.betting_completed = False
        self.status_label.config(text=f"Dealing {self.stage.capitalize()}. Pot: {self.pot}")
        self.log(f"Dealing {self.stage.capitalize()}, Pot: {self.pot}")
        self.update_ui()

        self.current_player_index = (self.dealer_index + 1) % len(self.players)
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        self.root.after(1000, self.run_betting_round)

    def do_showdown(self):
        self.stage = "showdown"
        active_players = [p for p in self.players if not p.folded]

        if len(active_players) == 1:
            self.single_player_win(active_players[0])
            return

        best_value = None
        winners = []
        for p in active_players:
            val = best_five_from_seven(p.cards + self.community_cards)
            if best_value is None or val > best_value:
                best_value = val
                winners = [p]
            elif val == best_value:
                winners.append(p)

        winning_hand_description = hand_description(best_value)
        if len(winners) == 1:
            winner = winners[0]
            winner.chips += self.pot
            self.status_label.config(text=f"{winner.name} wins {self.pot} chips with a {winning_hand_description}!")
            self.log(f"{winner.name} wins {self.pot} with {winning_hand_description}")
        else:
            share = self.pot // len(winners)
            for w in winners:
                w.chips += share
            winner_names = ", ".join([w.name for w in winners])
            self.status_label.config(text=f"Split pot! {winner_names} each win {share} chips with a {winning_hand_description}!")
            self.log(f"Split pot among {winner_names}, each {share} chips with {winning_hand_description}")

        self.update_ui()
        self.show_continue_button()

    def single_player_win(self, player):
        player.chips += self.pot
        self.status_label.config(text=f"{player.name} wins {self.pot} chips!")
        self.log(f"{player.name} wins {self.pot} chips (everyone else folded)")
        self.update_ui()
        self.show_continue_button()

    def show_continue_button(self):
        if self.continue_button is None:
            self.continue_button = tk.Button(self.action_frame, text="Continue", command=self.end_hand, bg="#C0C0C0", fg="black")
            self.continue_button.pack(side=tk.LEFT, padx=10)

    def end_hand(self):
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        self.log("---- Hand Ended ----")
        self.start_hand()

    def update_ui(self):
        self.stage_label.config(text=f"Stage: {self.stage.capitalize()}")
        self.pot_label.config(text=f"Pot: {self.pot}")

        # Update players
        for frame, player in zip(self.player_frames, self.players):
            for widget in frame.winfo_children():
                widget.destroy()

            action_display = ""
            action_color = "black"
            if player.last_action:
                action_display = f" ({player.last_action})"
                if "Fold" in player.last_action:
                    action_color = "red"
                elif "Check" in player.last_action or "Call" in player.last_action:
                    action_color = "blue"
                elif "Raise" in player.last_action:
                    action_color = "green"
                elif "Post" in player.last_action:
                    action_color = "gray"

            dealer_button = " (D)" if self.players.index(player) == self.dealer_index else ""
            label_text = str(player) + dealer_button + action_display
            lbl = tk.Label(frame, text=label_text, fg=action_color, bg="#FFFFFF", font=self.bold_font)
            lbl.pack()

            # Show player cards
            for c in player.cards:
                if player.is_human or self.stage == "showdown":
                    img = self.card_images[(c.rank, c.suit)]
                else:
                    img = self.card_back_image
                lbl_card = tk.Label(frame, image=img, bg="#FFFFFF")
                lbl_card.image = img
                lbl_card.pack(side=tk.LEFT, padx=2, pady=2)

        # Update community cards
        for widget in self.community_frame.winfo_children():
            widget.destroy()
        tk.Label(self.community_frame, text="Community Cards:", bg="#DDDDDD", fg="black", font=self.bold_font).pack(side=tk.LEFT, padx=5)
        for c in self.community_cards:
            img = self.card_images[(c.rank, c.suit)]
            lbl = tk.Label(self.community_frame, image=img, bg="#DDDDDD")
            lbl.image = img
            lbl.pack(side=tk.LEFT, padx=2)

        self.root.update_idletasks()

    # ------------ Human Actions ------------
    def human_call(self):
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            if required > 0:
                added = player.bet(required)
                self.pot += added
                player.last_action = "Call"
                self.status_label.config(text="You call.")
                self.log(f"You call {added}")
            else:
                player.last_action = "Check"
                self.status_label.config(text="You check.")
                self.log("You check")
            self.update_ui()
            self.next_player()

    def human_fold(self):
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text="You fold.")
            self.log("You fold")
            self.update_ui()
            self.next_player()

    def human_bet(self):
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            call_amount = player.bet(required)
            raise_amount = 50
            extra = player.bet(raise_amount)
            self.pot += (call_amount + extra)
            self.current_bet += extra
            player.last_action = "Raise 50"
            self.status_label.config(text="You raise by 50.")
            self.log(f"You raise by 50")
            self.update_ui()
            self.next_player()

if __name__ == "__main__":
    root = tk.Tk()
    app = TexasHoldemGame(root)
    root.mainloop()
