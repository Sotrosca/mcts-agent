from Switcher.logic.moves import SwitchMovementCard


class Player:
    figures_slots = {}
    figures_blocked = []
    figures_played = []
    hand = {}
    figures_deck = None

    def __init__(self, player_id, figures_slots_qty=3, move_cards_qty=3):
        self.player_id = player_id
        self.figures_slots_qty = figures_slots_qty
        self.figures_slots = {i: None for i in range(figures_slots_qty)}
        self.hand = {i: None for i in range(move_cards_qty)}
        self.hand_max_size = move_cards_qty
        self.hand_size = 0

    def set_figures_deck(self, figures_deck):
        self.figures_deck = figures_deck

    def draw_figure(self):
        figure = self.figures_deck.pop(0)

        for i, figure_to_play in self.figures_slots.items():
            if figure_to_play is None:
                self.figures_slots[i] = figure
                break

        return figure

    def play_figure(self, figure_slot):
        figure = self.figures_slots[figure_slot]
        self.figures_played.append(figure)
        self.figures_slots[figure_slot] = None
        return figure

    def show_figure(self, figure_slot):
        print(self.figures_slots[figure_slot])
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
        for figure in self.figures_slots:
            if figure is not None:
                ret += 1
        return ret
