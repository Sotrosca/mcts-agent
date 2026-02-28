from __future__ import annotations

Cell = tuple[int, int]
Board = list[list[list[int]]]
BoardSizeCell = list[list[int]]


class BoardModel:
    def __init__(
        self,
        board: Board,
        board_size_cell: BoardSizeCell | None = None,
        board_height: int | None = None,
        board_width: int | None = None,
        board_length: int | None = None,
    ):
        self.board = board
        self.height = board_height if board_height is not None else len(board)
        self.width = board_width if board_width is not None else len(board[0])
        self.length = board_length if board_length is not None else len(board[0][0])
        self.board_size_cell = (
            board_size_cell
            if board_size_cell is not None
            else self.calculate_board_size_cell(board)
        )

    @staticmethod
    def calculate_board_size_cell(board: Board) -> BoardSizeCell:
        board_size_cell: BoardSizeCell = []
        for i in range(len(board)):
            board_size_cell.append([])
            for j in range(len(board[0])):
                try:
                    last_index_with_container = board[i][j].index(0)
                except ValueError:
                    last_index_with_container = len(board[i][j])
                board_size_cell[i].append(last_index_with_container)
        return board_size_cell

    def top_container(self, cell: Cell) -> int:
        row, col = cell
        size = self.board_size_cell[row][col]
        if size == 0:
            return 0
        return self.board[row][col][size - 1]

    def move_container(self, source_cell: Cell, target_cell: Cell) -> int:
        source_size = self.board_size_cell[source_cell[0]][source_cell[1]]
        source_index = source_size - 1
        container = self.board[source_cell[0]][source_cell[1]][source_index]
        self.board[source_cell[0]][source_cell[1]][source_index] = 0

        target_index = self.board_size_cell[target_cell[0]][target_cell[1]]
        self.board[target_cell[0]][target_cell[1]][target_index] = container

        self.board_size_cell[source_cell[0]][source_cell[1]] -= 1
        self.board_size_cell[target_cell[0]][target_cell[1]] += 1

        return container

    def extract_top(self, source_cell: Cell) -> int:
        source_size = self.board_size_cell[source_cell[0]][source_cell[1]]
        source_index = source_size - 1
        container = self.board[source_cell[0]][source_cell[1]][source_index]
        self.board[source_cell[0]][source_cell[1]][source_index] = 0
        self.board_size_cell[source_cell[0]][source_cell[1]] -= 1
        return container
