from __future__ import annotations

from typing import Any

from .action_types import ActionType

Cell = tuple[int, int]
Action = dict[str, Any]
Board = list[list[list[int]]]
BoardSizeCell = list[list[int]]


class ActionGenerator:
    @staticmethod
    def get_possible_actions(
        board: Board,
        board_size_cell: BoardSizeCell,
        board_height: int,
        board_width: int,
        board_length: int,
        pending_targets: list[int],
    ) -> list[Action]:
        actions: list[Action] = []

        if len(pending_targets) == 0:
            return [{"type": int(ActionType.END)}]

        current_target = pending_targets[0]
        for row in range(board_height):
            for col in range(board_width):
                cell_size = board_size_cell[row][col]
                if cell_size == 0:
                    continue

                top_container = board[row][col][cell_size - 1]
                if top_container == current_target:
                    actions.append(
                        {
                            "source_cell": (row, col),
                            "type": int(ActionType.EXTRACT),
                        }
                    )

                actions.extend(
                    ActionGenerator.get_all_move_actions_from_cell(
                        source_cell=(row, col),
                        board_size_cell=board_size_cell,
                        board_height=board_height,
                        board_width=board_width,
                        board_length=board_length,
                    )
                )

        return actions

    @staticmethod
    def get_all_move_actions_from_cell(
        source_cell: Cell,
        board_size_cell: BoardSizeCell,
        board_height: int,
        board_width: int,
        board_length: int,
    ) -> list[Action]:
        return [
            {
                "source_cell": source_cell,
                "target_cell": (row, col),
                "type": int(ActionType.MOVE),
            }
            for row in range(board_height)
            for col in range(board_width)
            if (source_cell[0] != row or source_cell[1] != col)
            and (board_size_cell[row][col] < board_length)
        ]

    @staticmethod
    def build_move_actions(board_height: int, board_width: int) -> list[Action]:
        actions: list[Action] = []
        for source_row in range(board_height):
            for source_col in range(board_width):
                actions.extend(
                    {
                        "source_cell": (source_row, source_col),
                        "target_cell": (target_row, target_col),
                        "type": int(ActionType.MOVE),
                    }
                    for target_row in range(board_height)
                    for target_col in range(board_width)
                    if source_row != target_row or source_col != target_col
                )
        return actions

    @staticmethod
    def is_valid_move_action(
        source_cell: Cell,
        target_cell: Cell,
        board_size_cell: BoardSizeCell,
        board_length: int,
    ) -> bool:
        if source_cell is None or target_cell is None:
            return False
        source_row, source_col = source_cell
        target_row, target_col = target_cell
        source_has_container = board_size_cell[source_row][source_col] > 0
        target_has_capacity = board_size_cell[target_row][target_col] < board_length
        different_cells = source_cell != target_cell
        return source_has_container and target_has_capacity and different_cells

    @staticmethod
    def is_valid_extract_action(
        source_cell: Cell,
        board: Board,
        board_size_cell: BoardSizeCell,
        pending_targets: list[int],
    ) -> bool:
        if source_cell is None or len(pending_targets) == 0:
            return False
        row, col = source_cell
        cell_size = board_size_cell[row][col]
        if cell_size == 0:
            return False
        top_container = board[row][col][cell_size - 1]
        return top_container == pending_targets[0]
