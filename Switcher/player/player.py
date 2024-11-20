from Switcher.logic.moves import SwitchMovementCard


class Player:
    figures_slots = {}
    figures_played = []
    figures_deck = None

    def __init__(self, player_id, figures_slots_qty=4, move_cards_qty=3):
        self.player_id = player_id
        self.figures_slots_qty = figures_slots_qty
        self.figures_slots = {i: None for i in range(figures_slots_qty)}
        self.figures_blocked = {i: False for i in range(figures_slots_qty)}
        self.hand = {i: None for i in range(move_cards_qty)}
        self.hand_max_size = move_cards_qty
        self.hand_size = 0
        self.is_blocked = False

    def set_figures_deck(self, figures_deck):
        self.figures_deck = figures_deck

    def draw_figure(self):
        if len(self.figures_deck) == 0:
            return None
        figure = self.figures_deck.pop(0)

        for i, figure_to_play in self.figures_slots.items():
            if figure_to_play is None:
                self.figures_slots[i] = figure
                break

        return figure

    def draw_figures_until_full(self):
        for i, figure_to_play in self.figures_slots.items():

            if figure_to_play is None and len(self.figures_deck) > 0:
                figure = self.figures_deck.pop(0)
                self.figures_slots[i] = figure
                break

    def play_figure(self, figure_slot):
        figure = self.figures_slots[figure_slot]
        self.figures_played.append(figure)
        self.figures_slots[figure_slot] = None
        return figure

    def show_figure(self, figure_slot):
        # print(self.figures_slots[figure_slot])
        figure = self.figures_slots[figure_slot]
        return figure

    def play_move_card(self, move_card_slot) -> SwitchMovementCard:
        move_card = self.hand[move_card_slot]
        self.hand[move_card_slot] = None
        self.hand_size -= 1
        return move_card

    def draw_move_card(self, move_card):
        for i, move_card_to_play in self.hand.items():
            if move_card_to_play is None:
                self.hand[i] = move_card
                self.hand_size += 1
                break

    def total_figures_slots(self):
        ret = 0
        for figure in self.figures_slots.values():
            if figure is not None:
                ret += 1
        return ret

    def ban_figure(self, figure_slot):
        self.figures_blocked[figure_slot] = True
        self.is_blocked = True

    def enable_figure(self, figure_slot):
        self.figures_blocked[figure_slot] = False

    def enable_all_figures(self):
        for i in self.figures_blocked.keys():
            self.figures_blocked[i] = False

    def enable_player(self):
        self.is_blocked = False

    def has_blocked_figures(self):
        for is_ban in self.figures_blocked.values():
            if is_ban:
                return True
        return False
