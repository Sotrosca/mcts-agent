import numpy as np

from Switcher.logic.board import Board
from Switcher.logic.figures import figures_deck, find_figure, find_figures
from Switcher.logic.moves import SwitchMovementCard, moves_deck
from Switcher.player.player import Player
from Switcher.player.player_move import (
    MatchFigureMove,
    PassMove,
    PlayerMove,
    SwitchMove,
)


class Switcher:
    def __init__(
        self,
        players_quantity,
        figures_deck_by_player=12,
        figures_slots_qty=4,
        figures_deck=figures_deck,
        moves_deck=moves_deck,
    ):
        self.board_size = (8, 8)
        self.color_quantity = 4
        self.board = Board(self.board_size, self.color_quantity)
        self.players_quantity = players_quantity
        self.players = [
            Player(i, figures_slots_qty=figures_slots_qty)
            for i in range(players_quantity)
        ]
        self.figures_deck = self.shuffle_deck(figures_deck)
        self.figures_deck_by_player = figures_deck_by_player
        self.moves_deck = self.shuffle_deck(moves_deck)
        self.moves_discard = []
        self.last_color_played = None
        self.player_turn = np.random.randint(0, players_quantity)
        self.current_player: Player = self.players[self.player_turn]
        self.turn = 0

    def shuffle_deck(self, deck):
        np.random.shuffle(deck)
        return deck

    def draw_card(self, deck, qty=1, discard_deck=None):
        if len(deck) < qty:
            print("Not enough cards to draw")
            if discard_deck is not None:
                deck.extend(self.shuffle_deck(discard_deck))
                discard_deck.clear()
            else:
                raise ValueError("Not enough cards to draw")
        cards_drawn = deck[:qty]
        deck = deck[qty:]
        return cards_drawn, deck

    def deal_figures(self):
        for player in self.players:
            player_figures_deck, _ = self.draw_card(
                self.figures_deck, self.figures_deck_by_player
            )
            player.set_figures_deck(player_figures_deck)  # Set the deck for the player
            for i in range(player.figures_slots_qty):
                player.draw_figure()

    def deal_moves(self):
        for player in self.players:
            hand, self.moves_deck = self.draw_card(
                self.moves_deck, 3, self.moves_discard
            )
            for move_card in hand:
                player.draw_move_card(move_card)

    def switch_cells(self, cell_x, cell_y, move_x, move_y):
        # The game knows about axis x and y, but the board knows about rows and columns
        cell2_x = cell_x + move_x
        cell2_y = cell_y + move_y
        print(f"Switching {cell_x, cell_y} with {cell2_x, cell2_y}")
        valid_move = self.board.switch_cells(cell_y, cell_x, cell2_y, cell2_x)
        return valid_move

    def find_figures(self):
        board_state_with_border = self.board.get_board_state_color(with_border=True)
        for color in range(1, self.color_quantity + 1):
            find_figures(board_state_with_border, color)

    def valid_figure(self, figure_name, x, y, figure_color):
        board_state_with_border = self.board.get_board_state_color(with_border=True)
        figure = find_figure(board_state_with_border, figure_name, x, y, figure_color)
        return figure is not None

    def player_pass(self):
        hand_size = self.current_player.hand_size
        hand_max_size = self.current_player.hand_max_size

        while hand_size < hand_max_size:
            move_card, self.moves_deck = self.draw_card(
                self.moves_deck, 1, self.moves_discard
            )
            self.current_player.draw_move_card(move_card[0])
            hand_size += 1

        self.player_turn = (self.player_turn + 1) % self.players_quantity
        self.current_player = self.players[self.player_turn]

    def player_switch(self, player: Player, player_move: SwitchMove):
        move_card = player.play_move_card(player_move.move_card_slot)
        if not (player_move.steps_x, player_move.steps_y) in move_card.moves:
            raise ValueError("Invalid move")
        self.switch_cells(
            player_move.cell_x_target,
            player_move.cell_y_target,
            player_move.steps_x,
            player_move.steps_y,
        )
        self.moves_discard.append(move_card)

    def player_match_figure(self, player: Player, player_move: MatchFigureMove):
        figure_name = player.show_figure(player_move.move_card_slot)
        figure_x, figure_y, figure_color = (
            player_move.figure_board_x,
            player_move.figure_board_y,
            player_move.figure_board_color,
        )
        valid_figure = self.valid_figure(figure_name, figure_x, figure_y, figure_color)

        if not valid_figure:
            raise ValueError("Invalid figure")

        player.play_figure(player_move.player_figure_slot)
        self.last_color_played = figure_color

        if len(player.figures_deck) > 0:
            player.draw_figure()

    def do_move(self, player_move: PlayerMove):
        if player_move.type == "Pass":
            self.player_pass()
        elif player_move.type == "Switch":
            self.player_switch(self.current_player, player_move)
        elif player_move.type == "Match figure":
            self.player_match_figure(self.current_player, player_move)
        else:
            raise ValueError("Invalid move type")

    def check_player_win(self, player: Player):
        return len(player.figures_deck) == 0 and len(player.total_figures_slots()) == 0

    def switch_possible_moves(self, switch_move: SwitchMovementCard, x, y):
        moves = switch_move.possible_moves(x, y)

        valid_moves = []
        for move in moves:
            if (
                move[0] >= 0
                and move[0] < self.board.size[0]
                and move[1] >= 0
                and move[1] < self.board.size[1]
            ):
                valid_moves.append(move)
        return valid_moves


if __name__ == "__main__":
    game = Switcher(1)

    game.deal_figures()
    game.deal_moves()

    print("Figures Deck")
    for key, figure_name in game.current_player.figures_slots.items():
        print(key, figure_name)
    for key, figure_name in game.current_player.hand.items():
        print(key, figure_name)

    continue_game = True

    while continue_game:

        print("Board")
        state = game.board.state
        for row in state:
            # switch -1 to X
            row = [str(cell.color) for cell in row]
            print(" ".join(row))

        print("Moves")
        for key, figure_name in game.current_player.hand.items():
            print(key, figure_name)
        print("9. Exit")

        move_number = int(input("Select a move: "))

        if move_number == 9:
            continue_game = False
            continue

        if move_number not in game.current_player.hand.keys():
            print("Invalid move")
            continue

        selected_cell_x = int(input("Select cell x coordinate: "))

        if (
            selected_cell_x < 0
            or selected_cell_x >= game.board.size[0] * game.board.size[1]
        ):
            print("Invalid cell row")
            continue

        selected_cell_y = int(input("Select cell y coordinate: "))
        if (
            selected_cell_y < 0
            or selected_cell_y >= game.board.size[0] * game.board.size[1]
        ):
            print("Invalid cell column")
            continue

        selected_cell = game.board.state[selected_cell_x][selected_cell_y]

        possible_moves = [
            (selected_cell_x + move[0], selected_cell_y + move[1])
            for move in game.current_player.hand[move_number].moves
        ]

        for i, move in enumerate(possible_moves):
            print(i, move)

        selected_move = int(input("Select a move: "))

        move = possible_moves[selected_move]

        valid_move = game.switch_cells(
            selected_cell_x,
            selected_cell_y,
            move[0] - selected_cell_x,
            move[1] - selected_cell_y,
        )

        if not valid_move:
            print("Error switching")
            continue
