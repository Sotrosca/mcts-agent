import numpy as np

from Switcher.logic.board import Board
from Switcher.logic.figures import (
    BoardFigure,
    figures_deck,
    find_figure,
    find_figure_by_name,
    find_figures,
)
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
        self.winner = None

    def shuffle_deck(self, deck):
        np.random.shuffle(deck)
        return deck

    def draw_card(self, deck, qty=1, discard_deck=None):
        if len(deck) < qty:
            # print("Not enough cards to draw")
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
            player_figures_deck, self.figures_deck = self.draw_card(
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
        # print(f"Switching {cell_x, cell_y} with {cell2_x, cell2_y}")
        valid_move = self.board.switch_cells(cell_y, cell_x, cell2_y, cell2_x)
        return valid_move

    def find_board_figures(self) -> list[BoardFigure]:
        board_state_with_border = self.board.get_board_state_color(with_border=True)
        board_figures = []
        for color in range(1, self.color_quantity + 1):
            board_figures.extend(find_figures(board_state_with_border, color))
        return board_figures

    def find_board_figure(self, figure_name):
        board_state_with_border = self.board.get_board_state_color(with_border=True)
        board_figures = []
        for color in range(1, self.color_quantity + 1):
            board_figures.extend(
                find_figure_by_name(board_state_with_border, color, figure_name)
            )
        return board_figures

    def valid_board_figure(self, figure_name, x, y, figure_color):
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
            # print(f"Player {self.current_player.player_id} draws a move card")

        self.player_turn = (self.player_turn + 1) % self.players_quantity
        self.current_player = self.players[self.player_turn]
        self.turn += 1
        # print(f"Player {self.current_player.player_id} turn")

    def player_switch(self, player_move: SwitchMove):
        player = self.current_player
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

    def check_figure_board_move_is_valid(self, player_move: MatchFigureMove):
        player: Player = self.players[player_move.player_id]
        figure_name = player.show_figure(player_move.player_figure_slot)

        figure_x, figure_y, figure_color = (
            player_move.figure_board_x,
            player_move.figure_board_y,
            player_move.figure_board_color,
        )
        valid_board_figure = self.valid_board_figure(
            figure_name, figure_x, figure_y, figure_color
        )

        if not valid_board_figure:
            print(f"Invalid figure {figure_name} at {figure_x, figure_y}")
            # raise ValueError("Invalid figure")

    def play_current_player_figure(self, player_move: MatchFigureMove):
        player = self.current_player
        self.check_figure_board_move_is_valid(player_move)

        # print(
        #    f"Player {player.player_id} matches his figure {player_move.figure_name} from slot {player_move.player_figure_slot}"
        # )

        player.play_figure(player_move.player_figure_slot)
        self.last_color_played = player_move.figure_board_color

        # print(f"Total figures left: {player.total_figures_slots()}")

        if player.total_figures_slots() == 0:
            player.enable_player()

        if player.is_blocked and player.total_figures_slots() == 1:
            player.enable_all_figures()

        if not player.is_blocked and len(player.figures_deck) > 0:
            player.draw_figures_until_full()

    def play_opp_player_figure(self, player_move: MatchFigureMove):
        player: Player = self.players[player_move.player_id]

        if player.is_blocked:
            raise ValueError("Player is blocked")

        if player.total_figures_slots() <= 1:
            raise ValueError("Player has only one figure left")

        self.check_figure_board_move_is_valid(player_move)
        player.ban_figure(player_move.player_figure_slot)
        self.last_color_played = player_move.figure_board_color

    def player_match_figure(self, player_move: MatchFigureMove):
        if player_move.figure_board_color == self.last_color_played:
            raise ValueError("Invalid move, same color played")
        player = self.current_player
        figure_player: Player = self.players[player_move.player_id]
        if figure_player.player_id == player.player_id:
            self.play_current_player_figure(player_move)
        else:
            self.play_opp_player_figure(player_move)

    def check_current_player_winner(self):
        return (
            len(self.current_player.figures_deck) == 0
            and self.current_player.total_figures_slots() == 0
        )

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

    def do_move(self, player_move: PlayerMove):
        if player_move.type == "Pass":
            self.player_pass()
        elif player_move.type == "Switch":
            self.player_switch(player_move)
        elif player_move.type == "Match figure":
            self.player_match_figure(player_move)
        else:
            raise ValueError("Invalid move type")

        # print(f"Winner: {self.winner}")
        if self.check_current_player_winner():
            self.winner = self.player_turn
            # print(f"Winner winner: {self.winner}")
