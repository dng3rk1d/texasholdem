import tkinter as tk
from tkinter import font as tkFont, simpledialog
import random
import os
from collections import defaultdict, Counter
from itertools import combinations
import time

# Constants for suits and ranks
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

# Thresholds for strategic decisions
STRONG_HAND_THRESHOLD = 6  # Flush or better
MEDIUM_HAND_THRESHOLD = 3  # Three of a Kind or better
RAISE_THRESHOLD = 6        # For strategic player
CALL_THRESHOLD = 2        # For strategic player

# Table and chip constants
TABLE_COLOR = "#2F5D3D"
CHIP_COLORS = ["black", "blue", "green", "red", "white"]
CHIP_VALUES = {"black": 5, "blue": 10, "green": 20, "red": 50, "white": 100}
CHIP_IMAGE_NAMES = {
    "black": "black_chip.png",
    "blue": "blue_chip.png",
    "green": "green_chip.png",
    "red": "red_chip.png",
    "white": "white_chip.png",
}
CHIP_STACK_HEIGHT = 100
CHIP_STACK_WIDTH = 90
CHIP_STACK_LIMIT = 6  # Maximum chips in a stack
MAX_STACKS_PER_PLAYER = 3 # Maximum Stacks allowed for each player

# AI constants
AI_RAISE_AMOUNT = 50
UPDATE_DELAY = 100
MIN_AI_DELAY = 500
MAX_AI_DELAY = 1500

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

def check_straight(vals):
    """
    Returns (True, high_card) if there's a straight, otherwise (False, None).
    'high_card' should be the topmost card of that 5-card run.
    """
    # Ace can act as '1' in A-2-3-4-5
    if 14 in vals:
        temp = vals + [1]
    else:
        temp = vals

    longest_run = 1
    best_run_high = None
    run_length = 1
    run_start_index = 0

    for i in range(len(temp) - 1):
        if temp[i] - 1 == temp[i + 1]:
            run_length += 1
            if run_length >= 5:
                top_of_run = temp[run_start_index]
                if best_run_high is None or top_of_run > best_run_high:
                    best_run_high = top_of_run
        else:
            # If the current and next card are the same, ignore it but don't reset
            if temp[i] == temp[i + 1]:
                continue
            run_length = 1
            run_start_index = i + 1

    if best_run_high:
        return True, best_run_high
    return False, None

def rank_hand(cards):
    values = [RANK_VALUES[c.rank] for c in cards]
    suits = [c.suit for c in cards]
    vcount = Counter(values)
    scount = Counter(suits)
    
    sorted_values = sorted(values, reverse=True)
    unique_vals = sorted(set(values), reverse=True)

    is_flush = any(count >= 5 for count in scount.values())
    is_straight, straight_high = check_straight(unique_vals)

    freqs = sorted(vcount.values(), reverse=True)

    # Four of a Kind
    if 4 in freqs:
        quad_val = max(k for k, cnt in vcount.items() if cnt == 4)
        kicker = max(v for v in sorted_values if v != quad_val)
        return (8, quad_val, kicker)

    # Full House
    if 3 in freqs and 2 in freqs:
        three_vals = [k for k, cnt in vcount.items() if cnt == 3]
        best_three = max(three_vals)
        pair_candidates = [k for k, cnt in vcount.items() if cnt >= 2 and k != best_three]
        best_pair = max(pair_candidates) if pair_candidates else 0
        return (7, best_three, best_pair)

    # Check for Flush or Straight Flush
    if is_flush:
        sf_high = straight_flush_high(cards)
        if sf_high:
            return (9, sf_high)  # Straight Flush (or Royal if sf_high==14)
        flush_cards = flush_top_values(cards)
        return (6,) + tuple(flush_cards)

    # Straight
    if is_straight:
        return (5, straight_high)

    # Three of a Kind
    if 3 in freqs:
        three_val = max(k for k, cnt in vcount.items() if cnt == 3)
        kickers = sorted((v for v in sorted_values if v != three_val), reverse=True)[:2]
        return (4, three_val) + tuple(kickers)

    # Two Pair
    if freqs.count(2) >= 2:
        pairs = [k for k, cnt in vcount.items() if cnt == 2]
        pairs = sorted(pairs, reverse=True)
        top_two = pairs[:2]
        kicker = max(v for v in sorted_values if v not in top_two)
        return (3, top_two[0], top_two[1], kicker)

    # One Pair
    if 2 in freqs:
        pair_val = max(k for k, cnt in vcount.items() if cnt == 2)
        kickers = sorted((v for v in sorted_values if v != pair_val), reverse=True)[:3]
        return (2, pair_val) + tuple(kickers)

    # High Card
    top_five = sorted_values[:5]
    return (1,) + tuple(top_five)

def flush_top_values(cards):
    suit_cards = defaultdict(list)
    for c in cards:
        suit_cards[c.suit].append(RANK_VALUES[c.rank])
    for s, vals in suit_cards.items():
        if len(vals) >= 5:
            return sorted(vals, reverse=True)[:5]
    return []

def straight_flush_high(cards):
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
    def __init__(self, name, chips=1000, is_human=False, play_style="straightforward"):
        self.name = name
        self.chips = chips
        self.cards = []
        self.is_human = is_human
        self.folded = False
        self.current_bet = 0
        self.last_action = ""
        self.play_style = play_style
        self.placed_chips = []

    def reset_hand(self):
        self.cards = []
        self.folded = False
        self.current_bet = 0
        self.last_action = ""
        self.placed_chips = []

    def bet(self, amount):
        actual = min(amount, self.chips)
        self.chips -= actual
        self.current_bet += actual
        return actual

    def fold(self):
        self.folded = True
        self.last_action = "Fold"

    def __str__(self):
        return f"{self.name}: {self.chips} chips"

def ai_decision_straightforward(player, community_cards, current_bet, pot, stage, raise_count):
    hand_strength = evaluate_hand(player.cards, community_cards)
    if hand_strength >= STRONG_HAND_THRESHOLD:
        if player.chips > current_bet and raise_count < 2:
            return "raise", ai_raise_amount(hand_strength, pot, player.chips)
        else:
            return "call", 0
    elif hand_strength >= MEDIUM_HAND_THRESHOLD or random.random() > 0.8:
        return "call", 0
    else:
        return "fold", 0

def ai_decision_risk_taker(player, community_cards, current_bet, pot, stage, raise_count):
    hand_strength = evaluate_hand(player.cards, community_cards)
    if current_bet == 0:
         if player.chips > 0:
            return "call", 0
         else:
             return "fold", 0
    if player.chips > current_bet + AI_RAISE_AMOUNT and raise_count < 2:
        return "raise", ai_raise_amount(hand_strength, pot, player.chips)
    elif player.chips > current_bet:
        return "call", 0
    else:
        return "all-in", 0

def ai_decision_strategic(player, community_cards, current_bet, pot, stage, raise_count):
    hand_strength = evaluate_hand(player.cards, community_cards)
    position_factor = evaluate_position(player)
    pot_odds = calculate_pot_odds(current_bet, pot, player)
    decision_score = (hand_strength * 0.6) + (position_factor * 0.2) + (pot_odds * 0.2)

    if decision_score > RAISE_THRESHOLD:
        if player.chips > current_bet + AI_RAISE_AMOUNT and raise_count < 2:
            return "raise", ai_raise_amount(hand_strength, pot, player.chips)
        else:
            return "all-in", 0
    elif decision_score > CALL_THRESHOLD:
        return "call", 0
    else:
        return "fold", 0

def ai_decision_chaos(player, community_cards, current_bet, pot, stage, raise_count):
    actions = ["fold", "call", "raise", "all-in"]
    probabilities = [0.2, 0.3, 0.3, 0.2]
    action = random.choices(actions, probabilities)[0]
    
    hand_strength = evaluate_hand(player.cards, community_cards)

    if action == "raise" and player.chips <= current_bet + AI_RAISE_AMOUNT:
        if player.chips > current_bet:
            return "call", 0
        else:
            return "fold", 0
    elif action == "all-in" and player.chips < current_bet:
        return "fold", 0
    if action == "raise" and raise_count < 2:
        return action, ai_raise_amount(hand_strength, pot, player.chips)
    else:
        return "call", 0
    

def ai_decision(player, community_cards, current_bet, pot, stage, raise_count):
    if player.play_style == "straightforward":
        return ai_decision_straightforward(player, community_cards, current_bet, pot, stage, raise_count)
    elif player.play_style == "risk_taker":
       return ai_decision_risk_taker(player, community_cards, current_bet, pot, stage, raise_count)
    elif player.play_style == "strategic":
        return ai_decision_strategic(player, community_cards, current_bet, pot, stage, raise_count)
    elif player.play_style == "chaos":
        return ai_decision_chaos(player, community_cards, current_bet, pot, stage, raise_count)
    else:
        return "call", 0

def ai_raise_amount(hand_strength, pot, player_chips):
    # Define weights for each factor (adjust as needed)
    hand_weight = 0.4
    pot_weight = 0.3
    stack_weight = 0.3
    
    # Normalize the hand strength (range is 0-9)
    normalized_hand = hand_strength / 9.0
    
    # Normalize the pot size (adjust divisor as needed)
    normalized_pot = min(1, pot / 1000.0)
    
    # Normalize the player's chip stack (adjust divisor as needed)
    normalized_stack = min(1, player_chips / 1000.0)

    # Calculate a base raise amount
    base_raise = 50
    
    # Linear combination to determine the raise multiplier
    raise_multiplier = (
        (normalized_hand * hand_weight) +
        (normalized_pot * pot_weight) +
        (normalized_stack * stack_weight)
    )
    
    # Use raise multiplier to calculate dynamic raise amount
    dynamic_raise = int(base_raise * (1 + raise_multiplier))

    # Add a bit of randomness
    dynamic_raise += random.randint(-5, 5)
    
    return max(1, dynamic_raise)  # Ensure the raise is always at least 1

def evaluate_hand(cards, community_cards):
    best_hand = best_five_from_seven(cards + community_cards)
    return best_hand[0] if best_hand else 0

def evaluate_position(player):
    # Example position scores. Adjust as desired.
    position_scores = {
        "You": 3,    # Late position
        "Bob": 1,
        "Fernando": 2,
        "Alice": 1,
        "Lee": 2,
        "Tara": 1,
    }
    return position_scores.get(player.name, 1)

def calculate_pot_odds(current_bet, pot, player):
    if (pot + current_bet) == 0:
        return 0
    return (current_bet - player.current_bet) / (pot + current_bet) if (pot+current_bet)> 0 else 0

class TexasHoldemGame:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1500x900")

        self.deck = Deck()
        self.players = [
            Player("You", 5000, is_human=True, play_style="strategic"),
            Player("Bob", 5000, play_style="risk_taker"),
            Player("Fernando", 5000, play_style="strategic"),
            Player("Alice", 5000, play_style="risk_taker"),
            Player("Lee", 5000, play_style="strategic"),
            Player("Tara", 5000, play_style="risk_taker")
        ]

        self.dealer_index = 0
        self.small_blind = 50
        self.big_blind = 100

        self.current_player_index = 0
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.betting_completed = False
        self.continue_button = None

        self.player_contributions = [0 for _ in self.players]
        self.side_pots = []

        self.human_turn = False
        self.players_to_act = []
        self.raise_count = 0

        self.card_images = {}
        self.card_back_image = None
        self.load_images("cards_polished")
        
        self.chip_images = {}
        self.load_chip_images("chips")
        self.chip_cache = {}
        
        self.setup_ui()
        self.bind_keys()
        self.start_hand()

    def load_images(self, folder):
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

    def load_chip_images(self, folder):
        scale_factor = 6  # adjust if needed
        for color, filename in CHIP_IMAGE_NAMES.items():
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                img = tk.PhotoImage(file=path).subsample(scale_factor)
                self.chip_images[color] = img
            else:
                raise FileNotFoundError(f"Missing chip image: {path}")

    def setup_ui(self):
        self.root.title("♣︎ ♦︎ ♠︎ ♥︎ Texas Hold'em ♣︎ ♦︎ ♠︎ ♥︎")

        bg_main = "#F0F0F0"
        bg_info = "#F8F8F8"
        bg_game = TABLE_COLOR
        bg_player_frame = "#FFFFFF"
        bg_community_frame = "#DDDDDD"
        bg_action = "#D0D0D0"

        self.bold_font = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.status_font = tkFont.Font(family="Helvetica", size=18, slant="italic")

        self.root.configure(bg=bg_main)

        # Top info bar
        self.info_frame = tk.Frame(self.root, bg=bg_info)
        self.info_frame.pack(side=tk.TOP, fill=tk.X)
        self.status_label = tk.Label(
            self.info_frame, text="Welcome to Texas Hold'em!",
            fg="black", bg=bg_info, font=self.status_font
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Action frame
        self.action_frame = tk.Frame(self.root, bg=bg_action, bd=2, relief=tk.RAISED)
        self.action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.call_button = tk.Button(
            self.action_frame, text="Call/Check (C)",
            command=self.human_call, bg="#C0C0C0", fg="black", state=tk.DISABLED
        )
        self.call_button.pack(side=tk.LEFT, padx=5)

        self.fold_button = tk.Button(
            self.action_frame, text="Fold (F)",
            command=self.human_fold, bg="#C0C0C0", fg="black", state=tk.DISABLED
        )
        self.fold_button.pack(side=tk.LEFT, padx=5)

        self.bet_button = tk.Button(
            self.action_frame, text="Bet/Raise (B)",
            command=self.human_bet, bg="#C0C0C0", fg="black", state=tk.DISABLED
        )
        self.bet_button.pack(side=tk.LEFT, padx=5)

        self.all_in_button = tk.Button(
            self.action_frame, text="All-In (A)",
            command=self.human_all_in, bg="#C0C0C0", fg="black", state=tk.DISABLED
        )
        self.all_in_button.pack(side=tk.LEFT, padx=5)

        # Main game area
        self.game_frame = tk.Frame(self.root, bg=bg_game)
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top area for community cards
        top_area = tk.Frame(self.game_frame, bg=bg_game)
        top_area.pack(side=tk.TOP, pady=10)

        self.stage_label = tk.Label(top_area, text="Stage: Preflop", font=self.bold_font, fg="white", bg=bg_game)
        self.stage_label.pack(side=tk.TOP, pady=5)

        self.pot_label = tk.Label(top_area, text="Pot: 0", font=self.bold_font, fg="white", bg=bg_game)
        self.pot_label.pack(side=tk.TOP, pady=5)

        self.community_frame = tk.Frame(top_area, bd=2, relief=tk.RIDGE, bg=bg_community_frame, padx=5, pady=5)
        self.community_frame.pack(side=tk.TOP, pady=10)

        # Players frame
        self.players_frame = tk.Frame(self.game_frame, bg=bg_game)
        self.players_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.player_frames = []
        for p in self.players:
            f = tk.Frame(self.players_frame, bd=2, relief=tk.GROOVE, bg=bg_player_frame, padx=5, pady=5)
            f.pack(side=tk.LEFT, padx=5)
            self.player_frames.append(f)

    def bind_keys(self):
        self.root.bind('<c>', lambda event: self.human_call())
        self.root.bind('<C>', lambda event: self.human_call())
        self.root.bind('<f>', lambda event: self.human_fold())
        self.root.bind('<F>', lambda event: self.human_fold())
        self.root.bind('<b>', lambda event: self.human_bet())
        self.root.bind('<B>', lambda event: self.human_bet())
        self.root.bind('<a>', lambda event: self.human_all_in())
        self.root.bind('<A>', lambda event: self.human_all_in())
        self.root.focus_set()

    def reset_for_new_hand(self):
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.betting_completed = False
        self.player_contributions = [0 for _ in self.players]
        self.side_pots = []
        self.players_to_act = []
        self.raise_count = 0

    def start_hand(self):
        self.deck = Deck()
        for p in self.players:
            p.reset_hand()
        self.community_cards = []
        self.reset_for_new_hand()

        if self.continue_button:
            self.continue_button.destroy()
            self.continue_button = None

        self.deal_hole_cards()
        self.post_blinds()
        self.update_ui()

        # Preflop: first to act is (dealer+3) % len(players) 
        first_player_offset = 3
        self.current_player_index = (self.dealer_index + first_player_offset) % len(self.players)

        # Players to act on preflop is all players except big blind
        self.players_to_act = [
            p for p in self.players 
            if not p.folded and p != self.players[(self.dealer_index + 2) % len(self.players)]
        ]
        self.human_turn = False
        self.root.after(UPDATE_DELAY, self.run_betting_round)  # Reduced delay to 100ms

    def deal_hole_cards(self):
        for _ in range(2):
            for p in self.players:
                p.cards.append(self.deck.deal())

    def post_blinds(self):
        sb_player = self.players[(self.dealer_index + 1) % len(self.players)]
        bb_player = self.players[(self.dealer_index + 2) % len(self.players)]

        sb_amount = self.take_bet_from_player(sb_player, self.small_blind)
        bb_amount = self.take_bet_from_player(bb_player, self.big_blind)
        self.current_bet = self.big_blind

        self.status_label.config(
            text=f"{sb_player.name} posts SB {sb_amount}, {bb_player.name} posts BB {bb_amount}"
        )
    def take_bet_from_player(self, player, amount):
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        self.player_contributions[self.players.index(player)] += actual
        return actual
    def run_betting_round(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            self.single_player_win(active_players[0])
            return
        
        if self.betting_completed:
            self.next_stage()
            return

        if not self.players_to_act:
            self.betting_completed = True
            self.root.after(UPDATE_DELAY, self.run_betting_round)  # Reduced delay to 100ms
            return

        current_player = self.players[self.current_player_index]
        if current_player.folded:
            self.next_player()
            return

        # Human or AI
        if current_player.is_human:
            self.status_label.config(text=f"Your turn. Choose an action. (Max 2 Raises Per Betting Round)")
            self.human_turn = True
            self.enable_action_buttons()
            self.update_ui()
            return
        else:
            self.root.after(random.randint(MIN_AI_DELAY, MAX_AI_DELAY),
                lambda: self.process_ai_turn(current_player)
            )

    def process_ai_turn(self, current_player):
            action, raise_amount = ai_decision(
                current_player, self.community_cards, 
                self.current_bet, self.pot, self.stage, self.raise_count
            )
            self.process_ai_action(current_player, action, raise_amount)

    def process_ai_action(self, player, action, raise_amount):
        required = self.current_bet - player.current_bet
        if action == "fold":
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text=f"{player.name} folds.")
        elif action == "call":
            if required > 0:
                if player.chips < required:
                    all_in_amount = player.chips
                    self.place_bet_with_chips(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(
                        text=f"{player.name} goes all-in with {all_in_amount}."
                    )
                else:
                    added = self.place_bet_with_chips(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text=f"{player.name} calls {required}.")
            else:
                player.last_action = "Check"
                self.status_label.config(text=f"{player.name} checks.")
        elif action == "raise":
            # AI is hard-coded to raise AI_RAISE_AMOUNT if possible
            if player.chips > required + raise_amount:
                if required > 0:
                    self.place_bet_with_chips(player, required)
                
                if raise_amount > 0 :
                    extra = self.place_bet_with_chips(player, raise_amount)
                    self.current_bet += extra
                    player.last_action = f"Raise {raise_amount}"
                    self.status_label.config(
                        text=f"{player.name} raises by {raise_amount}"   
                    )                        
                    self.raise_count += 1
                    # Everyone else must act again
                    self.players_to_act = [
                        p for p in self.players if not p.folded and p != player
                    ]
            else:
                all_in_amount = player.chips
                self.place_bet_with_chips(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(
                    text=f"{player.name} all-in with {all_in_amount}."
                )
        elif action == "all-in":
            all_in_amount = player.chips
            self.place_bet_with_chips(player, all_in_amount)
            player.last_action = f"All-In {all_in_amount}"
            self.status_label.config(
                text=f"{player.name} all-in with {all_in_amount}."
            )

        self.update_pot()
        self.update_ui()

        if player in self.players_to_act:
            self.players_to_act.remove(player)

        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            self.single_player_win(active_players[0])
            return
        
        # Added this check so that if all players are all in, then we end the betting round.
        all_players_all_in = all(p.chips == 0 for p in self.players if not p.folded)
        if all_players_all_in:
              self.betting_completed = True
              self.root.after(UPDATE_DELAY, self.run_betting_round) # Reduced delay to 100ms
              return
        
        self.next_player()

    def place_bet_with_chips(self, player, amount):
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        self.player_contributions[self.players.index(player)] += actual

        # Use integer division to determine how many chips of each value to use
        denominations = sorted(CHIP_VALUES.values(), reverse=True)
        placed_chips = []
        remaining_amount = actual
        for denomination in denominations:
            while remaining_amount >= denomination:
                placed_chips.append(denomination)
                remaining_amount -= denomination
        
        player.placed_chips = placed_chips
        
        # if player added to the pot, was not already all in, and not human all-in, add player back to `players_to_act`
        if amount > 0 and amount < player.chips and player in self.players_to_act:
             self.players_to_act = [
                 p for p in self.players if not p.folded and p != player
             ]

        return actual
    def update_pot(self):
        self.pot = sum(self.player_contributions)

    def next_player(self):
        # Check if betting is complete before continuing
        if self.check_betting_complete():            
            self.create_side_pots()
            self.betting_completed = True
            self.root.after(UPDATE_DELAY, self.run_betting_round)  # Reduced delay to 100ms
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # Skip folded players
        while self.players[self.current_player_index].folded:
             self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # If the next player is not in players_to_act, we skip again
        if self.players[self.current_player_index] not in self.players_to_act:
           if not self.players_to_act:
                return # Exit if no players remain to act
           self.next_player()
           return
        
        self.root.after(UPDATE_DELAY, self.run_betting_round) # Reduced delay to 100ms

    def check_betting_complete(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            return True
        if not self.players_to_act:
            return True
        return False

    def create_side_pots(self):
        self.side_pots = []
        active_contribs = [
            (self.player_contributions[i], self.players[i]) 
            for i, p in enumerate(self.players)
            if not p.folded and self.player_contributions[i] > 0
        ]
        if not active_contribs:
            return

        active_contribs.sort(key=lambda x: x[0])
        previous_level = 0
        for contrib, player in active_contribs:
            if contrib > previous_level:
                pot_level = contrib - previous_level
                involved_players = [
                    p for j, p in enumerate(self.players)
                    if not p.folded and self.player_contributions[j] >= contrib
                ]
                pot_size = pot_level * len(involved_players)
                self.side_pots.append({
                    'players': involved_players,
                    'amount': pot_size
                })
                previous_level = contrib

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

        # Reset bets each round
        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.last_action = ""
        
        self.raise_count = 0

        self.betting_completed = False
        self.status_label.config(text=f"Dealing {self.stage.capitalize()}. Pot: {self.pot}")
        self.update_ui()

        # Post-flop: first to act is the seat after the dealer
        if self.stage in ["flop", "turn", "river"]:
            first_player_index = (self.dealer_index + 1) % len(self.players)
        else:
            first_player_index = (self.dealer_index + 3) % len(self.players)

        self.current_player_index = first_player_index
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # If preflop, players to act is everyone but the big blind. Otherwise, everyone who hasn't folded.
        if self.stage == "preflop":
             self.players_to_act = [p for p in self.players
                if not p.folded and p != self.players[(self.dealer_index + 2) % len(self.players)]]
        else:
             self.players_to_act = [p for p in self.players if not p.folded]

        self.root.after(UPDATE_DELAY, self.run_betting_round) # Reduced delay to 100ms

    def do_showdown(self):
        # Force stage to 'showdown' so that UI logic flips all cards face up
        self.stage = "showdown"
        active_players = [p for p in self.players if not p.folded]

        if len(active_players) == 1:
            self.single_player_win(active_players[0])
            return

        player_values = {}
        for p in active_players:
            val = best_five_from_seven(p.cards + self.community_cards)
            player_values[p] = val

        if not self.side_pots:
            self.side_pots = [{'players': active_players, 'amount': self.pot}]

        for side_pot in self.side_pots:
            contenders = [p for p in side_pot['players'] if p in active_players and p in player_values]
            if not contenders:
                continue
            best_value = None
            winners = []
            for p in contenders:
                val = player_values[p]
                if best_value is None or val > best_value:
                    best_value = val
                    winners = [p]
                elif val == best_value:
                    winners.append(p)

            winning_hand_description = hand_description(best_value)
            if len(winners) == 1:
                winner = winners[0]
                winner.chips += side_pot['amount']
                self.status_label.config(
                    text=f"{winner.name} wins {side_pot['amount']} chips with a {winning_hand_description}!"
                )
            else:
                share = side_pot['amount'] // len(winners)
                for w in winners:
                    w.chips += share
                winner_names = ", ".join([w.name for w in winners])
                self.status_label.config(
                    text=f"Split pot! {winner_names} each win {share} chips with a {winning_hand_description}!"
                )

        self.update_ui()
        self.show_continue_button()

    def single_player_win(self, player):
        player.chips += self.pot
        self.status_label.config(text=f"{player.name} wins {self.pot} chips!")
        self.stage = "showdown"  # reveal everyone's cards
        self.update_ui()
        self.show_continue_button()

    def show_continue_button(self):
        if self.continue_button is None:
            self.continue_button = tk.Button(
                self.action_frame, text="Continue",
                command=self.end_hand, bg="#C0C0C0", fg="black"
            )
            self.continue_button.pack(side=tk.LEFT, padx=10)

        self.root.bind('<space>', self.on_spacebar_end_hand)

        space_label = tk.Label(self.action_frame, text="", bg="#D0D0D0", fg="black")
        space_label.pack(side=tk.LEFT, padx=10)

    def on_spacebar_end_hand(self, event):
        self.end_hand()

    def end_hand(self):
        self.root.unbind('<space>')
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        self.start_hand()

    def update_ui(self):
        self.stage_label.config(text=f"Stage: {self.stage.capitalize()}")
        self.pot_label.config(text=f"Pot: {self.pot}")
        
        for frame, player in zip(self.player_frames, self.players):
            self.update_player_frame(frame, player)

        # Community cards
        self.update_community_cards()
        self.root.update_idletasks()


    def update_player_frame(self, frame, player):
        # Destroy previous widgets
        for widget in frame.winfo_children():
            widget.destroy()

        # Grey out folded player's frame
        if player.folded:
            frame_bg = "#BBBBBB"
        elif self.players[self.current_player_index] == player:
            frame_bg = "#FFEB99"
        else:
            frame_bg = "#FFFFFF"

        frame.config(bg=frame_bg)

        # Show player's name, chips, any last action
        action_display = ""
        action_color = "black"
        if player.last_action:
            action_display = f" ({player.last_action})"
            if "Fold" in player.last_action:
                action_color = "red"
            elif "Check" in player.last_action or "Call" in player.last_action:
                action_color = "blue"
            elif "Raise" in player.last_action or "All-In" in player.last_action:
                action_color = "green"

        dealer_button = " (D)" if (self.players.index(player) == self.dealer_index) else ""
        label_text = f"{player.name}: {player.chips} chips{dealer_button}{action_display}"

        lbl = tk.Label(frame, text=label_text, fg=action_color, bg=frame_bg, font=self.bold_font)
        lbl.pack()

        self.display_bet_this_round(frame, player, frame_bg)
        self.display_chips(frame, player, frame_bg)

        # Show hole cards face-up if human or showdown, else facedown
        for c in player.cards:
            if player.is_human or self.stage == "showdown":
                img = self.card_images.get((c.rank, c.suit), self.card_back_image)
            else:
                img = self.card_back_image
            lbl_card = tk.Label(frame, image=img, bg=frame_bg)
            lbl_card.image = img
            lbl_card.pack(side=tk.LEFT, padx=2, pady=2)

    def update_community_cards(self):
        for widget in self.community_frame.winfo_children():
            widget.destroy()
        tk.Label(
            self.community_frame, text="Community Cards", bg="#DDDDDD",
            fg="black", font=self.bold_font
        ).pack(side=tk.LEFT, padx=5)

        for c in self.community_cards:
            img = self.card_images.get((c.rank, c.suit), self.card_back_image)
            lbl = tk.Label(self.community_frame, image=img, bg="#DDDDDD")
            lbl.image = img
            lbl.pack(side=tk.LEFT, padx=2)

    def display_bet_this_round(self, frame, player, bg_color="#000000"):
        bet_this_round = player.current_bet
        bet_label = tk.Label(
            frame, text=f"Bet This Round: {bet_this_round}",
            bg=bg_color,fg="black"
        )
        bet_label.pack(side=tk.TOP, padx=2, pady=2)

    def display_chips(self, frame, player, bg_color="#FFFFFF"):
        chips_frame = tk.Frame(frame, bg=bg_color)
        chips_frame.pack(side=tk.TOP, pady=5)

        
        placed_chips = player.placed_chips
        sorted_chips = sorted(placed_chips, key=lambda x: CHIP_VALUES[next(k for k, v in CHIP_VALUES.items() if v == x)], reverse=True)

        num_stacks = 0
        chips_in_stack = 0
        x_offset_per_stack = 0
        stacks = []
        current_stack = []

        for chip_value in sorted_chips:
            current_stack.append(chip_value)
            chips_in_stack += 1
            if chips_in_stack >= CHIP_STACK_LIMIT:
                 stacks.append(current_stack)
                 current_stack = []
                 chips_in_stack = 0
                 num_stacks+=1

        if current_stack:
            stacks.append(current_stack)

        num_stacks = len(stacks)
        
        # If we have more stacks than allowed per player, we just truncate to the limit
        if num_stacks > MAX_STACKS_PER_PLAYER:
              num_stacks = MAX_STACKS_PER_PLAYER
              stacks = stacks[:MAX_STACKS_PER_PLAYER]


        for stack_index, stack in enumerate(stacks):
             chips_canvas = tk.Canvas(chips_frame, width=CHIP_STACK_WIDTH, height=CHIP_STACK_HEIGHT, bg=bg_color, highlightthickness=0)
             chips_canvas.pack(side=tk.LEFT, padx=5)

             max_display = 35
             visible_chips = stack[:max_display]
             extra_count = len(stack) - max_display if len(stack) > max_display else 0

             x_start, y_start = CHIP_STACK_WIDTH / 2, CHIP_STACK_HEIGHT - 30
             x_offset = 0
             y_offset = 9 # Chip vertical spacing

             # Stack them vertically
             for i, chip_value in enumerate(visible_chips):
                  chip_color = [k for k, v in CHIP_VALUES.items() if v == chip_value][0]
                  img = self.chip_images[chip_color]
                  x = x_start - i * x_offset
                  y = y_start - i * y_offset
                  chips_canvas.create_image(x, y, image=img, anchor=tk.CENTER)

             if extra_count > 0:
                 chips_canvas.create_text(
                     x_start, 20, text=f"+{extra_count} more",
                     fill="black", font=("Helvetica", 8)
                 )

    def enable_action_buttons(self):
        self.call_button.config(state=tk.NORMAL)
        self.fold_button.config(state=tk.NORMAL)
        self.bet_button.config(state=tk.NORMAL)
        self.all_in_button.config(state=tk.NORMAL)

    def disable_action_buttons(self):
        self.call_button.config(state=tk.DISABLED)
        self.fold_button.config(state=tk.DISABLED)
        self.bet_button.config(state=tk.DISABLED)
        self.all_in_button.config(state=tk.DISABLED)

    def human_call(self):
        if not self.human_turn:
            return
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            if required > 0:
                if player.chips < required:
                    all_in_amount = player.chips
                    self.place_bet_with_chips(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(text="You go all-in!")
                else:
                    added = self.place_bet_with_chips(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text="You call.")
            else:
                player.last_action = "Check"
                self.status_label.config(text="You check.")

            self.update_pot()
            self.update_ui()
            self.human_turn = False
            self.disable_action_buttons()

            if player in self.players_to_act:
                self.players_to_act.remove(player)

            # If only one remains, that player wins automatically
            active_players = [p for p in self.players if not p.folded]
            if len(active_players) == 1:
                self.single_player_win(active_players[0])
                return
            self.next_player()

    def human_fold(self):
        if not self.human_turn:
            return
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text="You fold.")
            self.update_ui()
            self.human_turn = False
            self.disable_action_buttons()

            if player in self.players_to_act:
                self.players_to_act.remove(player)

            active_players = [p for p in self.players if not p.folded]
            if len(active_players) == 1:
                self.single_player_win(active_players[0])
                return

            self.next_player()

    def human_bet(self):
        if not self.human_turn:
            return
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            if self.raise_count >= 2:
                 self.status_label.config(text="Maximum raises reached, choose call or fold.")
                 return
            bet_amount = simpledialog.askinteger(
                "Bet Amount", "Enter bet amount:",
                minvalue=1, maxvalue=player.chips
            )
            if bet_amount is not None:
                required = self.current_bet - player.current_bet
                if required > 0:
                    call_amount = min(required, player.chips)
                    self.place_bet_with_chips(player, call_amount)
                
                raise_amount = min(bet_amount, player.chips)
                if raise_amount > 0:
                    extra = self.place_bet_with_chips(player, raise_amount)
                    self.current_bet += extra
                    player.last_action = f"Raise {bet_amount}"
                    self.status_label.config(text=f"You raise by {bet_amount}.")
                    self.raise_count += 1
                    # Everyone else must act again, unless they're folded
                    self.players_to_act = [
                        p for p in self.players if not p.folded and p != player
                    ]
                else:
                    # If raise_amount == 0 but player has 0 chips, that's effectively All-In
                    if player.chips == 0:
                         player.last_action = "All-In"
                         self.status_label.config(text="You are all-in!")
                    else:
                        player.last_action = "Call"
                        self.status_label.config(text="You call.")

                self.update_pot()
                self.update_ui()
                self.human_turn = False
                self.disable_action_buttons()

                if player in self.players_to_act:
                    self.players_to_act.remove(player)

                active_players = [p for p in self.players if not p.folded]
                if len(active_players) == 1:
                    self.single_player_win(active_players[0])
                    return
                self.next_player()

    def human_all_in(self):
        if not self.human_turn:
            return
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            all_in_amount = player.chips
            if all_in_amount > 0:
                self.place_bet_with_chips(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(text=f"You go all-in with {all_in_amount}.")
                self.update_pot()
                self.update_ui()
                self.human_turn = False
                self.disable_action_buttons()

                if player in self.players_to_act:
                    self.players_to_act.remove(player)

                active_players = [p for p in self.players if not p.folded]
                if len(active_players) == 1:
                    self.single_player_win(active_players[0])
                    return
                self.players_to_act = [
                    p for p in self.players if not p.folded and p != player
                ]
                self.next_player()
            else:
                self.status_label.config(text="You have no chips to go all-in.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TexasHoldemGame(root)
    root.mainloop()