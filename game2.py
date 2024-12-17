import tkinter as tk
from tkinter import font as tkFont, scrolledtext
import random
import os
from collections import defaultdict, Counter
from itertools import combinations

# Constants for suits and ranks
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

# Thresholds for strategic decisions
STRONG_HAND_THRESHOLD = 6  # Flush or better
MEDIUM_HAND_THRESHOLD = 4  # Three of a Kind or better
RAISE_THRESHOLD = 6        # For strategic player
CALL_THRESHOLD = 3         # For strategic player

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
                best_high = temp[i]
        elif temp[i] != temp[i+1]:
            current_len = 1
    if best_high is not None:
        return True, best_high
    return False, None

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
        self.play_style = play_style  # New attribute

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

def ai_decision_straightforward(player, community_cards, current_bet, pot, stage):
    hand_strength = evaluate_hand(player.cards, community_cards)
    
    if hand_strength >= STRONG_HAND_THRESHOLD:
        if player.chips > current_bet:
            return "raise"
        else:
            return "call"
    elif hand_strength >= MEDIUM_HAND_THRESHOLD:
        return "call"
    else:
        return "fold"

def ai_decision_risk_taker(player, community_cards, current_bet, pot, stage):
    bluff_probability = 0.5  # 50% chance to bluff
    
    if random.random() < bluff_probability:
        if player.chips > current_bet + 50:
            return "raise"
        else:
            return "all-in"
    else:
        if current_bet > 0 and player.chips > current_bet:
            return "call"
        else:
            return "fold"

def ai_decision_strategic(player, community_cards, current_bet, pot, stage):
    hand_strength = evaluate_hand(player.cards, community_cards)
    position_factor = evaluate_position(player)  # e.g., early, middle, late
    pot_odds = calculate_pot_odds(current_bet, pot)
    
    decision_score = (hand_strength * 0.6) + (position_factor * 0.2) + (pot_odds * 0.2)
    
    if decision_score > RAISE_THRESHOLD:
        if player.chips > current_bet + 50:
            return "raise"
        else:
            return "all-in"
    elif decision_score > CALL_THRESHOLD:
        return "call"
    else:
        return "fold"

def ai_decision_chaos(player, community_cards, current_bet, pot, stage):
    actions = ["fold", "call", "raise", "all-in"]
    probabilities = [0.2, 0.3, 0.3, 0.2]  # Adjust probabilities for unpredictability
    
    action = random.choices(actions, probabilities)[0]
    
    # Ensure actions are valid based on chips
    if action == "raise" and player.chips <= current_bet + 50:
        action = "call" if player.chips > current_bet else "fold"
    elif action == "all-in" and player.chips < current_bet:
        action = "fold"
    
    return action

def ai_decision(player, community_cards, current_bet, pot, stage):
    if player.play_style == "straightforward":
        return ai_decision_straightforward(player, community_cards, current_bet, pot, stage)
    elif player.play_style == "risk_taker":
        return ai_decision_risk_taker(player, community_cards, current_bet, pot, stage)
    elif player.play_style == "strategic":
        return ai_decision_strategic(player, community_cards, current_bet, pot, stage)
    elif player.play_style == "chaos":
        return ai_decision_chaos(player, community_cards, current_bet, pot, stage)
    else:
        return "call"  # Default action

def evaluate_hand(cards, community_cards):
    # Utilize your existing hand evaluation logic
    best_hand = best_five_from_seven(cards + community_cards)
    return best_hand[0] if best_hand else 0  # Assuming higher value is stronger

def evaluate_position(player):
    # Assign scores based on player's position
    # Example: Early position = 1, Middle = 2, Late = 3
    position_scores = {
        "You": 3,    # Assuming the human player is in a late position
        "AI1": 1,
        "AI2": 2,
        "AI3": 1,
        "AI4": 2,
    }
    return position_scores.get(player.name, 1)  # Default to early position

def calculate_pot_odds(current_bet, pot):
    return current_bet / (pot + current_bet) if (pot + current_bet) > 0 else 0

class TexasHoldemGame:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x600")  # Wider window for horizontal layout

        self.deck = Deck()
        self.players = [
            Player("You", 1000, is_human=True, play_style="strategic"),  # Human player with strategic label
            Player("AI1", 1000, play_style="straightforward"),
            Player("AI2", 1000, play_style="risk_taker"),
            Player("AI3", 1000, play_style="strategic"),
            Player("AI4", 1000, play_style="chaos"),
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

        # Track each player's contributions to handle side pots and all-ins
        self.player_contributions = [0 for _ in self.players]
        self.side_pots = []

        # Flag to indicate if it's currently the human's turn
        self.human_turn = False  # <-- Added Flag

        # List of players who need to act in the current betting round
        self.players_to_act = []

        self.card_images = {}
        self.card_back_image = None
        self.load_images("cards_polished")

        self.setup_ui()
        self.bind_keys()  # Bind keystrokes after setting up UI
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

    def setup_ui(self):
        self.root.title("Texas Hold'em v1.14")  # Incremented version for updates

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

        # Action Buttons with Keystroke Indicators
        self.call_button = tk.Button(self.action_frame, text="Call/Check (C)", command=self.human_call, bg="#C0C0C0", fg="black", state=tk.DISABLED)
        self.call_button.pack(side=tk.LEFT, padx=5)
        self.fold_button = tk.Button(self.action_frame, text="Fold (F)", command=self.human_fold, bg="#C0C0C0", fg="black", state=tk.DISABLED)
        self.fold_button.pack(side=tk.LEFT, padx=5)
        self.bet_button = tk.Button(self.action_frame, text="Bet/Raise 50 (B)", command=self.human_bet, bg="#C0C0C0", fg="black", state=tk.DISABLED)
        self.bet_button.pack(side=tk.LEFT, padx=5)
        self.all_in_button = tk.Button(self.action_frame, text="All-In (A)", command=self.human_all_in, bg="#C0C0C0", fg="black", state=tk.DISABLED)
        self.all_in_button.pack(side=tk.LEFT, padx=5)

        # Main game area
        self.game_frame = tk.Frame(self.root, bg=bg_game)
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # On the right side, a log
        self.log_frame = tk.Frame(self.root, bg=bg_main)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.log_frame, text="Game Log:", bg=bg_main, fg="black", font=self.bold_font).pack(anchor='w')
        self.log_text = scrolledtext.ScrolledText(self.log_frame, width=40, height=35, bg="#FFFFFF")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Community cards & Pot/Stage at top center
        top_area = tk.Frame(self.game_frame, bg=bg_game)
        top_area.pack(side=tk.TOP, pady=10)

        self.stage_label = tk.Label(top_area, text="Stage: Preflop", font=self.bold_font, fg="black", bg=bg_game)
        self.stage_label.pack(side=tk.TOP, pady=5)

        self.pot_label = tk.Label(top_area, text="Pot: 0", font=self.bold_font, fg="black", bg=bg_game)
        self.pot_label.pack(side=tk.TOP, pady=5)

        self.community_frame = tk.Frame(top_area, bd=2, relief=tk.RIDGE, bg=bg_community_frame, padx=5, pady=5)
        self.community_frame.pack(side=tk.TOP, pady=10)

        # Players arranged horizontally at bottom
        self.players_frame = tk.Frame(self.game_frame, bg=bg_game)
        self.players_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.player_frames = []
        for p in self.players:
            f = tk.Frame(self.players_frame, bd=2, relief=tk.GROOVE, bg=bg_player_frame, padx=5, pady=5)
            f.pack(side=tk.LEFT, padx=5)
            self.player_frames.append(f)

    def bind_keys(self):
        # Bind lowercase and uppercase keys to their respective actions
        self.root.bind('<c>', lambda event: self.human_call())
        self.root.bind('<C>', lambda event: self.human_call())
        self.root.bind('<f>', lambda event: self.human_fold())
        self.root.bind('<F>', lambda event: self.human_fold())
        self.root.bind('<b>', lambda event: self.human_bet())
        self.root.bind('<B>', lambda event: self.human_bet())
        self.root.bind('<a>', lambda event: self.human_all_in())
        self.root.bind('<A>', lambda event: self.human_all_in())

        # Ensure the root window has focus to capture keystrokes
        self.root.focus_set()

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)

    def reset_for_new_hand(self):
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.betting_completed = False
        self.player_contributions = [0 for _ in self.players]
        self.side_pots = []
        self.players_to_act = []  # Reset players to act

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

        # Log start of a new hand
        self.log("---- New Hand Started ----")
        self.log(f"Dealer: {self.players[self.dealer_index].name}")

        # Determine first player to act preflop (player left of BB)
        self.current_player_index = (self.dealer_index + 3) % len(self.players)
        self.players_to_act = [p for p in self.players if not p.folded and p != self.players[(self.dealer_index + 2) % len(self.players)]]
        self.human_turn = False  # Ensure flag is reset
        self.root.after(1000, self.run_betting_round)

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

        self.status_label.config(text=f"{sb_player.name} posts SB {sb_amount}, {bb_player.name} posts BB {bb_amount}")
        self.log(f"{sb_player.name} posts SB {sb_amount}")
        self.log(f"{bb_player.name} posts BB {bb_amount}")

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
            # No players left to act, betting round complete
            self.betting_completed = True
            self.root.after(1000, self.run_betting_round)
            return

        current_player = self.players[self.current_player_index]
        if current_player.folded:
            self.next_player()
            return

        if current_player.is_human:
            # Indicate it's the human's turn and wait for action
            self.status_label.config(text=f"{current_player.name}'s turn. Choose an action.")
            self.human_turn = True  # Set flag to True
            self.enable_action_buttons()  # Enable buttons for human
            return
        else:
            # AI decision and action based on play_style
            action = ai_decision(current_player, self.community_cards, self.current_bet, self.pot, self.stage)
            self.process_ai_action(current_player, action)

    def process_ai_action(self, player, action):
        required = self.current_bet - player.current_bet
        if action == "fold":
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text=f"{player.name} folds.")
            self.log(f"{player.name} folds.")
        elif action == "call":
            if required > 0:
                if player.chips < required:
                    # Player all-in
                    all_in_amount = player.chips
                    self.take_bet_from_player(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(text=f"{player.name} goes all-in with {all_in_amount}.")
                    self.log(f"{player.name} all-in {all_in_amount}")
                else:
                    added = self.take_bet_from_player(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text=f"{player.name} calls {required}.")
                    self.log(f"{player.name} calls {required}")
            else:
                player.last_action = "Check"
                self.status_label.config(text=f"{player.name} checks.")
                self.log(f"{player.name} checks")
        elif action == "raise":
            if player.chips > required + 50:
                call_amount = min(required, player.chips)
                added_call = self.take_bet_from_player(player, call_amount)
                raise_amount = min(50, player.chips)
                if raise_amount > 0:
                    extra = self.take_bet_from_player(player, raise_amount)
                    self.current_bet += extra
                    player.last_action = "Raise 50"
                    self.status_label.config(text=f"{player.name} raises by 50.")
                    self.log(f"{player.name} raises by 50")
                    # Reset players_to_act since a raise has occurred
                    self.players_to_act = [p for p in self.players if not p.folded and p != player]
            else:
                # All-in due to lack of chips to raise
                all_in_amount = player.chips
                self.take_bet_from_player(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(text=f"{player.name} all-in with {all_in_amount}.")
                self.log(f"{player.name} all-in {all_in_amount}")
        elif action == "all-in":
            all_in_amount = player.chips
            self.take_bet_from_player(player, all_in_amount)
            player.last_action = f"All-In {all_in_amount}"
            self.status_label.config(text=f"{player.name} all-in with {all_in_amount}.")
            self.log(f"{player.name} all-in {all_in_amount}")

        self.update_pot()
        self.update_ui()

        # Remove current player from players_to_act
        if player in self.players_to_act:
            self.players_to_act.remove(player)

        self.next_player()

    def update_pot(self):
        self.pot = sum(self.player_contributions)

    def next_player(self):
        if self.check_betting_complete():
            self.create_side_pots()
            self.betting_completed = True
            self.root.after(1000, self.run_betting_round)
            return

        # Advance to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # Skip folded players
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # Check if the player needs to act
        if self.players[self.current_player_index] in self.players_to_act:
            # It's their turn to act
            pass
        else:
            # They have already acted, move to next player
            self.next_player()
            return

        self.root.after(1000, self.run_betting_round)

    def check_betting_complete(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            return True
        if not self.players_to_act:
            return True
        return False

    def create_side_pots(self):
        # Reset side_pots
        self.side_pots = []
        active_contribs = [(self.player_contributions[i], self.players[i]) 
                           for i, p in enumerate(self.players) if not p.folded and self.player_contributions[i] > 0]

        if not active_contribs:
            return

        active_contribs.sort(key=lambda x: x[0])
        previous_level = 0
        # Layer pots based on contribution levels
        for i, (contrib, player) in enumerate(active_contribs):
            if contrib > previous_level:
                pot_level = contrib - previous_level
                # Players who contributed at least this level
                involved_players = [p for j,p in enumerate(self.players) 
                                    if not p.folded and self.player_contributions[j] >= contrib]
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

        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.last_action = ""

        self.betting_completed = False
        self.status_label.config(text=f"Dealing {self.stage.capitalize()}. Pot: {self.pot}")
        self.log(f"Dealing {self.stage.capitalize()}, Pot: {self.pot}")
        self.update_ui()

        # Determine first player to act in new stage
        if self.stage in ["flop", "turn", "river"]:
            # First to act is the player left of dealer
            first_player_index = (self.dealer_index + 1) % len(self.players)
        else:
            # Preflop: first to act is player left of big blind
            first_player_index = (self.dealer_index + 3) % len(self.players)

        # Set current_player_index to first active player
        self.current_player_index = first_player_index
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # Initialize players_to_act list for the new betting round
        if self.stage == "preflop":
            # In preflop, players left of big blind have to act
            self.players_to_act = [p for p in self.players if not p.folded and p != self.players[(self.dealer_index + 2) % len(self.players)]]
        else:
            # Postflop, all active players left of dealer act
            self.players_to_act = [p for p in self.players if not p.folded]

        self.root.after(1000, self.run_betting_round)

    def do_showdown(self):
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
            # If no side pots were created, it's a single pot scenario
            self.side_pots = [{'players': active_players, 'amount': self.pot}]

        # Award each pot
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
                self.status_label.config(text=f"{winner.name} wins {side_pot['amount']} chips with a {winning_hand_description}!")
                self.log(f"{winner.name} wins {side_pot['amount']} chips with {winning_hand_description}")
            else:
                share = side_pot['amount'] // len(winners)
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
                elif "Raise" in player.last_action or "All-In" in player.last_action:
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
                    img = self.card_images.get((c.rank, c.suit), self.card_back_image)
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
            img = self.card_images.get((c.rank, c.suit), self.card_back_image)
            lbl = tk.Label(self.community_frame, image=img, bg="#DDDDDD")
            lbl.image = img
            lbl.pack(side=tk.LEFT, padx=2)

        self.root.update_idletasks()

    def enable_action_buttons(self):
        # Enable action buttons for human
        self.call_button.config(state=tk.NORMAL)
        self.fold_button.config(state=tk.NORMAL)
        self.bet_button.config(state=tk.NORMAL)
        self.all_in_button.config(state=tk.NORMAL)

    def disable_action_buttons(self):
        # Disable action buttons when not human's turn
        self.call_button.config(state=tk.DISABLED)
        self.fold_button.config(state=tk.DISABLED)
        self.bet_button.config(state=tk.DISABLED)
        self.all_in_button.config(state=tk.DISABLED)

    # Human Actions
    def human_call(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            if required > 0:
                if player.chips < required:
                    # Player all-in
                    all_in_amount = player.chips
                    self.take_bet_from_player(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(text="You go all-in!")
                    self.log(f"You all-in {all_in_amount}")
                else:
                    added = self.take_bet_from_player(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text="You call.")
                    self.log(f"You call {added}")
            else:
                player.last_action = "Check"
                self.status_label.config(text="You check.")
                self.log("You check")
            self.update_pot()
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_fold(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text="You fold.")
            self.log("You fold")
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_bet(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            # Attempt a raise by 50
            if required > 0:
                call_amount = min(required, player.chips)
                self.take_bet_from_player(player, call_amount)
            raise_amount = min(50, player.chips)
            if raise_amount > 0:
                self.take_bet_from_player(player, raise_amount)
                self.current_bet += raise_amount
                player.last_action = "Raise 50"
                self.status_label.config(text="You raise by 50.")
                self.log("You raise by 50")
                # Reset players_to_act since a raise has occurred
                self.players_to_act = [p for p in self.players if not p.folded and p != player]
            else:
                # Just call if can't raise
                if player.chips == 0:
                    player.last_action = "All-In"
                    self.status_label.config(text="You are all-in!")
                    self.log("You all-in")
                else:
                    player.last_action = "Call"
                    self.status_label.config(text="You call.")
                    self.log("You call")
            self.update_pot()
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_all_in(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            all_in_amount = player.chips
            if all_in_amount > 0:
                self.take_bet_from_player(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(text=f"You go all-in with {all_in_amount}.")
                self.log(f"You all-in with {all_in_amount}")
                self.update_pot()
                self.update_ui()
                self.human_turn = False  # <-- Reset flag
                self.disable_action_buttons()  # <-- Disable buttons
                # Remove player from players_to_act
                if player in self.players_to_act:
                    self.players_to_act.remove(player)
                # If a raise occurred, reset players_to_act
                self.players_to_act = [p for p in self.players if not p.folded and p != player]
                self.next_player()
            else:
                self.status_label.config(text="You have no chips to go all-in.")
                self.log("All-In failed: No chips left.")

    def process_ai_action(self, player, action):
        required = self.current_bet - player.current_bet
        if action == "fold":
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text=f"{player.name} folds.")
            self.log(f"{player.name} folds.")
        elif action == "call":
            if required > 0:
                if player.chips < required:
                    # Player all-in
                    all_in_amount = player.chips
                    self.take_bet_from_player(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(text=f"{player.name} goes all-in with {all_in_amount}.")
                    self.log(f"{player.name} all-in {all_in_amount}")
                else:
                    added = self.take_bet_from_player(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text=f"{player.name} calls {required}.")
                    self.log(f"{player.name} calls {required}")
            else:
                player.last_action = "Check"
                self.status_label.config(text=f"{player.name} checks.")
                self.log(f"{player.name} checks")
        elif action == "raise":
            if player.chips > required + 50:
                call_amount = min(required, player.chips)
                added_call = self.take_bet_from_player(player, call_amount)
                raise_amount = min(50, player.chips)
                if raise_amount > 0:
                    extra = self.take_bet_from_player(player, raise_amount)
                    self.current_bet += extra
                    player.last_action = "Raise 50"
                    self.status_label.config(text=f"{player.name} raises by 50.")
                    self.log(f"{player.name} raises by 50")
                    # Reset players_to_act since a raise has occurred
                    self.players_to_act = [p for p in self.players if not p.folded and p != player]
            else:
                # All-in due to lack of chips to raise
                all_in_amount = player.chips
                self.take_bet_from_player(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(text=f"{player.name} all-in with {all_in_amount}.")
                self.log(f"{player.name} all-in {all_in_amount}")
        elif action == "all-in":
            all_in_amount = player.chips
            self.take_bet_from_player(player, all_in_amount)
            player.last_action = f"All-In {all_in_amount}"
            self.status_label.config(text=f"{player.name} all-in with {all_in_amount}.")
            self.log(f"{player.name} all-in {all_in_amount}")

        self.update_pot()
        self.update_ui()

        # Remove current player from players_to_act
        if player in self.players_to_act:
            self.players_to_act.remove(player)

        self.next_player()

    def update_pot(self):
        self.pot = sum(self.player_contributions)

    def next_player(self):
        if self.check_betting_complete():
            self.create_side_pots()
            self.betting_completed = True
            self.root.after(1000, self.run_betting_round)
            return

        # Advance to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # Skip folded players
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # Check if the player needs to act
        if self.players[self.current_player_index] in self.players_to_act:
            # It's their turn to act
            pass
        else:
            # They have already acted, move to next player
            self.next_player()
            return

        self.root.after(1000, self.run_betting_round)

    def check_betting_complete(self):
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            return True
        if not self.players_to_act:
            return True
        return False

    def create_side_pots(self):
        # Reset side_pots
        self.side_pots = []
        active_contribs = [(self.player_contributions[i], self.players[i]) 
                           for i, p in enumerate(self.players) if not p.folded and self.player_contributions[i] > 0]

        if not active_contribs:
            return

        active_contribs.sort(key=lambda x: x[0])
        previous_level = 0
        # Layer pots based on contribution levels
        for i, (contrib, player) in enumerate(active_contribs):
            if contrib > previous_level:
                pot_level = contrib - previous_level
                # Players who contributed at least this level
                involved_players = [p for j,p in enumerate(self.players) 
                                    if not p.folded and self.player_contributions[j] >= contrib]
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

        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.last_action = ""

        self.betting_completed = False
        self.status_label.config(text=f"Dealing {self.stage.capitalize()}. Pot: {self.pot}")
        self.log(f"Dealing {self.stage.capitalize()}, Pot: {self.pot}")
        self.update_ui()

        # Determine first player to act in new stage
        if self.stage in ["flop", "turn", "river"]:
            # First to act is the player left of dealer
            first_player_index = (self.dealer_index + 1) % len(self.players)
        else:
            # Preflop: first to act is player left of big blind
            first_player_index = (self.dealer_index + 3) % len(self.players)

        # Set current_player_index to first active player
        self.current_player_index = first_player_index
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # Initialize players_to_act list for the new betting round
        if self.stage == "preflop":
            # In preflop, players left of big blind have to act
            self.players_to_act = [p for p in self.players if not p.folded and p != self.players[(self.dealer_index + 2) % len(self.players)]]
        else:
            # Postflop, all active players left of dealer act
            self.players_to_act = [p for p in self.players if not p.folded]

        self.root.after(1000, self.run_betting_round)

    def do_showdown(self):
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
            # If no side pots were created, it's a single pot scenario
            self.side_pots = [{'players': active_players, 'amount': self.pot}]

        # Award each pot
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
                self.status_label.config(text=f"{winner.name} wins {side_pot['amount']} chips with a {winning_hand_description}!")
                self.log(f"{winner.name} wins {side_pot['amount']} chips with {winning_hand_description}")
            else:
                share = side_pot['amount'] // len(winners)
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
                elif "Raise" in player.last_action or "All-In" in player.last_action:
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
                    img = self.card_images.get((c.rank, c.suit), self.card_back_image)
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
            img = self.card_images.get((c.rank, c.suit), self.card_back_image)
            lbl = tk.Label(self.community_frame, image=img, bg="#DDDDDD")
            lbl.image = img
            lbl.pack(side=tk.LEFT, padx=2)

        self.root.update_idletasks()

    def enable_action_buttons(self):
        # Enable action buttons for human
        self.call_button.config(state=tk.NORMAL)
        self.fold_button.config(state=tk.NORMAL)
        self.bet_button.config(state=tk.NORMAL)
        self.all_in_button.config(state=tk.NORMAL)

    def disable_action_buttons(self):
        # Disable action buttons when not human's turn
        self.call_button.config(state=tk.DISABLED)
        self.fold_button.config(state=tk.DISABLED)
        self.bet_button.config(state=tk.DISABLED)
        self.all_in_button.config(state=tk.DISABLED)

    # Human Actions
    def human_call(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            if required > 0:
                if player.chips < required:
                    # Player all-in
                    all_in_amount = player.chips
                    self.take_bet_from_player(player, all_in_amount)
                    player.last_action = f"All-In {all_in_amount}"
                    self.status_label.config(text="You go all-in!")
                    self.log(f"You all-in {all_in_amount}")
                else:
                    added = self.take_bet_from_player(player, required)
                    player.last_action = "Call"
                    self.status_label.config(text="You call.")
                    self.log(f"You call {added}")
            else:
                player.last_action = "Check"
                self.status_label.config(text="You check.")
                self.log("You check")
            self.update_pot()
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_fold(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            player.fold()
            player.last_action = "Fold"
            self.status_label.config(text="You fold.")
            self.log("You fold")
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_bet(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            required = self.current_bet - player.current_bet
            # Attempt a raise by 50
            if required > 0:
                call_amount = min(required, player.chips)
                self.take_bet_from_player(player, call_amount)
            raise_amount = min(50, player.chips)
            if raise_amount > 0:
                self.take_bet_from_player(player, raise_amount)
                self.current_bet += raise_amount
                player.last_action = "Raise 50"
                self.status_label.config(text="You raise by 50.")
                self.log("You raise by 50")
                # Reset players_to_act since a raise has occurred
                self.players_to_act = [p for p in self.players if not p.folded and p != player]
            else:
                # Just call if can't raise
                if player.chips == 0:
                    player.last_action = "All-In"
                    self.status_label.config(text="You are all-in!")
                    self.log("You all-in")
                else:
                    player.last_action = "Call"
                    self.status_label.config(text="You call.")
                    self.log("You call")
            self.update_pot()
            self.update_ui()
            self.human_turn = False  # <-- Reset flag
            self.disable_action_buttons()  # <-- Disable buttons
            # Remove player from players_to_act
            if player in self.players_to_act:
                self.players_to_act.remove(player)
            self.next_player()

    def human_all_in(self):
        if not self.human_turn:
            return  # Prevent action if not human's turn
        player = self.players[self.current_player_index]
        if player.is_human and not player.folded:
            all_in_amount = player.chips
            if all_in_amount > 0:
                self.take_bet_from_player(player, all_in_amount)
                player.last_action = f"All-In {all_in_amount}"
                self.status_label.config(text=f"You go all-in with {all_in_amount}.")
                self.log(f"You all-in with {all_in_amount}")
                self.update_pot()
                self.update_ui()
                self.human_turn = False  # <-- Reset flag
                self.disable_action_buttons()  # <-- Disable buttons
                # Remove player from players_to_act
                if player in self.players_to_act:
                    self.players_to_act.remove(player)
                # If a raise occurred, reset players_to_act
                self.players_to_act = [p for p in self.players if not p.folded and p != player]
                self.next_player()
            else:
                self.status_label.config(text="You have no chips to go all-in.")
                self.log("All-In failed: No chips left.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TexasHoldemGame(root)
    root.mainloop()