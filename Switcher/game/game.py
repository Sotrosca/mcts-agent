from Switcher.logic.logic import Switcher


class Game:
    def __init__(self, players_qty=2):
        self.players_qty = players_qty
        self.logic = Switcher(players_qty)
        self.logic.deal_figures()
        self.logic.deal_moves()
        self.board = self.logic.board
        self.selected_cells = []
        self.selected_move = None

    def switch_colors(self):
        if len(self.selected_cells) == 2 and self.selected_move is not None:
            cell1_x, cell1_y = self.selected_cells[0]
            cell2_x, cell2_y = self.selected_cells[1]
            print(f"Switching {cell1_x}, {cell1_y} with {cell2_x}, {cell2_y}")
            valid_move = self.board.switch_cells(cell1_y, cell1_x, cell2_y, cell2_x)
            self.selected_cells.clear()
