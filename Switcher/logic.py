import numpy as np

from Switcher.figures import figures, find_figures


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


class MovementCard:
    moves = None

    def __init__(self, cells_to_switch_row, cells_to_switch_column):
        self.calculate_moves(cells_to_switch_row, cells_to_switch_column)

    def calculate_moves(self, cells_to_switch_row, cells_to_switch_column):
        moves = []

        moves.append((cells_to_switch_row, cells_to_switch_column))
        moves.append((-cells_to_switch_row, -cells_to_switch_column))
        moves.append((cells_to_switch_column, -cells_to_switch_row))  # Symmetric move
        moves.append((-cells_to_switch_column, cells_to_switch_row))  # Symmetric move
        self.moves = moves

    def __eq__(self, other):
        """
        Moves are equal if almost one of the moves is equal
        """
        for move in self.moves:
            for other_move in other.moves:
                apply_both_moves = (move[0] + other_move[0], move[1] + other_move[1])
                if apply_both_moves == (0, 0):
                    return True
        return False


class Switcher:
    def __init__(self, players_quantity):
        self.board_size = (8, 8)
        self.color_quantity = 4
        self.board = Board(self.board_size, self.color_quantity)
        self.players_quantity = players_quantity

    def move(self, cell_x, cell_y, move_x, move_y):
        # The game knows about axis x and y, but the board knows about rows and columns
        cell2_x = cell_x + move_x
        cell2_y = cell_y + move_y
        print(f"Switching {cell_x, cell_y} with {cell2_x, cell2_y}")
        valid_move = self.board.switch_cells(cell_y, cell_x, cell2_y, cell2_x)
        return valid_move


if __name__ == "__main__":
    move_1 = MovementCard(1, 0)

    game = Switcher(1)

    moves = [*move_1.moves]

    continue_game = True

    while continue_game:

        print("Board")
        state = game.board.state
        for row in state:
            # switch -1 to X
            row = [str(cell.color) for cell in row]
            print(" ".join(row))

        print("Moves")
        for i, move in enumerate(moves):
            print(
                f"{i + 1}. X {'+' if move[0] > 0 else '-'} {abs(int(move[0]))} Y {'+' if move[1] > 0 else '-'} {abs(int(move[1]))}"
            )
        print("0. Exit")

        move_number = int(input("Select a move: "))

        if move_number == 0:
            continue_game = False
            continue

        move_number -= 1
        if move_number < 0 or move_number >= len(moves):
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

        valid_move = game.move(selected_cell_x, selected_cell_y, *moves[move_number])

        if not valid_move:
            print("Error switching")
            continue
