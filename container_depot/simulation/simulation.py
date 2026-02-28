from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .action_types import ActionType
from .action_generator import ActionGenerator
from .board_model import BoardModel

Cell = tuple[int, int]
Action = dict[str, Any]
State = dict[str, Any]
Board = list[list[list[int]]]
BoardSizeCell = list[list[int]]
DistanceFunction = Callable[[Cell, Cell], int]


class Simulation:
    def __init__(
        self,
        crane_position: Cell,
        board: Board,
        time: int,
        distance_function: DistanceFunction,
        containers_to_extract_id: list[int],
    ):
        self.crane_position: Cell = crane_position
        self.board_model = BoardModel(board)
        self._sync_board_attributes()
        self.time: int = time
        self.distance_function: DistanceFunction = distance_function
        self.epochs: int = 0
        self.containers_to_extract_id: list[int] = containers_to_extract_id
        self.history: dict[int, Action] = {}

    def _sync_board_attributes(self) -> None:
        self.board = self.board_model.board
        self.board_height = self.board_model.height
        self.board_width = self.board_model.width
        self.board_length = self.board_model.length
        self.board_size_cell = self.board_model.board_size_cell

    def get_state(self) -> State:
        simulation_state_dict = {
            'crane_position': self.crane_position,
            'board': self.board,
            'board_size_cell': self.board_size_cell,
            'board_height': self.board_height,
            'board_width': self.board_width,
            'board_length': self.board_length,
            'time': self.time,
            'epochs': self.epochs,
            'containers_to_extract_id': self.containers_to_extract_id,
        }
        return simulation_state_dict

    def set_state(self, state_dict: State) -> None:
        self.crane_position = state_dict.get('crane_position')
        self.board_model = BoardModel(
            state_dict.get('board'),
            board_size_cell=state_dict.get('board_size_cell'),
            board_height=state_dict.get('board_height'),
            board_width=state_dict.get('board_width'),
            board_length=state_dict.get('board_length'),
        )
        self._sync_board_attributes()
        self.time = state_dict.get('time')
        self.epochs = state_dict.get('epochs')
        self.containers_to_extract_id = state_dict.get('containers_to_extract_id')

    def calculate_board_size_cell(self) -> BoardSizeCell:
        return BoardModel.calculate_board_size_cell(self.board)

    def move_container(self, source_cell: Cell, target_cell: Cell) -> None:
        self.board_model.move_container(source_cell, target_cell)
        self.crane_position = target_cell

    def extract_container(self, source_cell: Cell) -> None:
        container = self.board_model.top_container(source_cell)
        if container not in self.containers_to_extract_id:
            print("Error container: " + str(container))
        else:
            self.board_model.extract_top(source_cell)
            self.containers_to_extract_id.remove(container)
            self.crane_position = source_cell

    def run_one_epoch(self, action: Action) -> None:
        self.execute_action(action)
        self.history[self.epochs] = action

    def execute_action(self, action: Action) -> None:
        action_cost = 0
        if action.get('type') == int(ActionType.MOVE):
            source_cell = action.get('source_cell')
            target_cell = action.get('target_cell')
            if not self._is_valid_move_action(source_cell, target_cell):
                raise ValueError(f"Invalid move action: {action}")
            action_cost = self.calculate_move_cost(source_cell, target_cell)
            self.move_container(source_cell, target_cell)
        elif action.get('type') == int(ActionType.EXTRACT):
            source_cell = action.get('source_cell')
            if not self._is_valid_extract_action(source_cell):
                raise ValueError(f"Invalid extract action: {action}")
            action_cost = self.calculate_extract_cost(source_cell)
            self.extract_container(source_cell)
        elif action.get('type') == int(ActionType.END):
            if not self.is_simulation_end():
                raise ValueError("END action is only valid when simulation is finished")
        else:
            raise ValueError(f"Unknown action type: {action}")

        self.time += action_cost
        self.epochs += 1

    def calculate_move_cost(self, source_cell: Cell, target_cell: Cell) -> int:
        distance_crane_to_source = self.distance_function(self.crane_position, source_cell)
        distance_source_to_target = self.distance_function(source_cell, target_cell)
        return distance_crane_to_source + distance_source_to_target

    def calculate_extract_cost(self, source_cell: Cell) -> int:
        distance_crane_to_source = self.distance_function(self.crane_position, source_cell)
        return distance_crane_to_source + 1

    def get_possible_actions(self) -> list[Action]:
        return ActionGenerator.get_possible_actions(
            board=self.board,
            board_size_cell=self.board_size_cell,
            board_height=self.board_height,
            board_width=self.board_width,
            board_length=self.board_length,
            pending_targets=self.containers_to_extract_id,
        )

    def get_all_move_actions_from_cell(self, source_cell: Cell) -> list[Action]:
        return ActionGenerator.get_all_move_actions_from_cell(
            source_cell=source_cell,
            board_size_cell=self.board_size_cell,
            board_height=self.board_height,
            board_width=self.board_width,
            board_length=self.board_length,
        )

    def build_move_actions(self) -> list[Action]:
        return ActionGenerator.build_move_actions(
            board_height=self.board_height,
            board_width=self.board_width,
        )

    def is_simulation_end(self) -> bool:
        return len(self.containers_to_extract_id) == 0

    def _is_valid_move_action(self, source_cell: Cell, target_cell: Cell) -> bool:
        return ActionGenerator.is_valid_move_action(
            source_cell=source_cell,
            target_cell=target_cell,
            board_size_cell=self.board_size_cell,
            board_length=self.board_length,
        )

    def _is_valid_extract_action(self, source_cell: Cell) -> bool:
        return ActionGenerator.is_valid_extract_action(
            source_cell=source_cell,
            board=self.board,
            board_size_cell=self.board_size_cell,
            pending_targets=self.containers_to_extract_id,
        )
