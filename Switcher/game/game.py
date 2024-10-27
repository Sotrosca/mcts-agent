from Switcher.logic.logic import Switcher
from Switcher.player.player_move import PassMove, SwitchMove


class Game:
    def __init__(self, players_qty=2):
        self.players_qty = players_qty
        self.logic = Switcher(players_qty)
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
