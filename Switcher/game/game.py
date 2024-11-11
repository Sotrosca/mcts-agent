from Switcher.logic.figures import BoardFigure
from Switcher.logic.logic import Switcher
from Switcher.player.player import Player
from Switcher.player.player_move import MatchFigureMove, PassMove, SwitchMove


class Game:
    def __init__(self, players_qty=2):
        self.players_qty = players_qty
        self.logic = Switcher(players_qty, figures_deck_by_player=2)
        self.logic.deal_figures()
        self.logic.deal_moves()
        self.board = self.logic.board

    def get_current_player_card(self, idx):
        return self.logic.current_player.hand[idx]

    def switch_colors(self, selected_cells, selected_move_idx):
        if len(selected_cells) == 2 and selected_move_idx is not None:
            cell1_x, cell1_y = selected_cells[0]
            cell2_x, cell2_y = selected_cells[1]
            steps_x = cell2_x - cell1_x
            steps_y = cell2_y - cell1_y
            move = SwitchMove(selected_move_idx, cell1_x, cell1_y, steps_x, steps_y)
            self.logic.do_move(move)

    def possible_switches(self, selected_cell, selected_move_idx):
        switch_move = self.get_current_player_card(selected_move_idx)
        x, y = selected_cell
        return self.logic.switch_possible_moves(switch_move, x, y)

    def pass_turn(self):
        move = PassMove()
        self.logic.do_move(move)

    def get_player_figures(self, player_idx):
        player: Player = self.logic.players[player_idx]
        return player.figures_slots

    def get_banned_player_figures(self, player_idx):
        player: Player = self.logic.players[player_idx]
        return player.figures_blocked

    def player_is_blocked(self, player_idx):
        player: Player = self.logic.players[player_idx]
        return player.is_blocked

    def get_all_player_figure_names(self):
        figures = []
        for player in self.logic.players:
            figures_slots = player.figures_slots
            figures.extend(
                list(map(lambda figure_name: figure_name, figures_slots.values()))
            )
        return figures

    def find_board_figures(self):
        # We convert the cells in the board with the border to the cells without the border
        figures_in_board_with_border = self.logic.find_board_figures()
        for figure in figures_in_board_with_border:
            figure: BoardFigure = figure
            cells = []
            for cell in figure.cells:
                cell_x, cell_y = cell[0] - 1, cell[1] - 1  # We remove the border
                cells.append((cell_x, cell_y))
            figure.cells = cells
        return figures_in_board_with_border

    def figure_cell(self, x, y, board_figures) -> BoardFigure:
        for figure in board_figures:
            if (x, y) in figure.cells:
                return figure
        return None

    def match_figure(self, player_idx, figure_idx, x, y, board_figures):
        figure = self.figure_cell(x, y, board_figures)

        move = MatchFigureMove(
            figure_name=figure.name,
            figure_board_x=figure.x,
            figure_board_y=figure.y,
            figure_board_color=figure.color,
            player_id=player_idx,
            player_figure_slot=figure_idx,
        )
        self.logic.do_move(move)

    def last_color_played(self):
        return self.logic.last_color_played

    def player_figures_deck_qty(self, player_idx):
        player: Player = self.logic.players[player_idx]
        return len(player.figures_deck)

    def check_player_winner(self):
        return self.logic.winner
