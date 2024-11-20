import numpy as np


class Cell:
    def __init__(self, color):
        self.color = color
        self.selected = False
        self.row = None
        self.column = None

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def change_color(self, new_color):
        self.color = new_color

    def set_position(self, row, column):
        self.row = row
        self.column = column

    def __str__(self):
        return f"({self.row}, {self.column}) - {self.color}, selected: {self.selected}"

    def __repr__(self):
        return self.__str__()


class Board:
    state = None

    def __init__(self, size, color_quantity):
        self.size = size
        self.color_quantity = color_quantity
        self.build_board_state()

    def build_board_state(self):
        """
        Builds the board for the game with random colors in each cell
        """
        self.state = np.zeros(self.size, dtype=Cell)
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                self.state[i][j] = Cell(np.random.randint(1, self.color_quantity + 1))
                self.state[i][j].set_position(i, j)

    def select_cell(self, cell_row, cell_column):
        cell: Cell = self.state[cell_row][cell_column]
        cell.select()

    def deselect_cell(self, cell_row, cell_column):
        cell: Cell = self.state[cell_row][cell_column]
        cell.deselect()

    def switch_cells(self, cell1_row, cell1_column, cell2_row, cell2_column):

        if self.invalid_cell(cell1_row, cell1_column) or self.invalid_cell(
            cell2_row, cell2_column
        ):
            return False
        cell1: Cell = self.state[cell1_row][cell1_column]
        cell2: Cell = self.state[cell2_row][cell2_column]

        cell1_color = cell1.color
        cell2_color = cell2.color

        cell1.change_color(cell2_color)
        cell2.change_color(cell1_color)
        return True

    def invalid_cell(self, cell_row, cell_column):
        return (
            cell_row < 0
            or cell_row >= self.size[0]
            or cell_column < 0
            or cell_column >= self.size[1]
        )

    def get_state_with_border(self, border_value=-1):
        """
        Adds a border to the board with the given value
        """
        board = self.state.tolist()
        for i in range(len(board)):
            board[i].insert(0, Cell(border_value))
            board[i].append(Cell(border_value))
        board.insert(0, [Cell(border_value)] * len(board[0]))
        board.append([Cell(border_value)] * len(board[0]))
        return board

    def get_board_state_color(self, with_border=False):
        if with_border:
            board = self.get_state_with_border()
        else:
            board = self.state
        return [[cell.color for cell in row] for row in board]
