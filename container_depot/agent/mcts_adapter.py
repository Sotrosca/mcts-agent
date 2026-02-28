import copy
import random
from collections.abc import Callable
from typing import Any

Cell = tuple[int, int]
Action = dict[str, Any]
State = dict[str, Any]
Board = list[list[list[int]]]
DistanceFunction = Callable[[Cell, Cell], int]


class ContainerDepotMCTSAdapter:
    def __init__(
        self,
        simulation: Any,
        rng: random.Random | None = None,
        blockage_weight: float = 1.0,
        initial_target_blockage_weight: float = 1.0,
    ):
        self.simulation = copy.deepcopy(simulation)
        self.rng = rng or random.Random()
        self.blockage_weight: float = blockage_weight
        self.initial_target_blockage_weight: float = initial_target_blockage_weight
        self._distance_cache: dict[tuple[Cell, Cell], int] = self._build_distance_cache()

    def get_initial_state(self) -> State:
        return self.clone_state(self.simulation.get_state())

    def clone_state(self, state: State) -> State:
        return {
            "crane_position": tuple(state["crane_position"]),
            "board": [[list(stack) for stack in row] for row in state["board"]],
            "board_size_cell": [list(row) for row in state["board_size_cell"]],
            "board_height": state["board_height"],
            "board_width": state["board_width"],
            "board_length": state["board_length"],
            "time": state["time"],
            "epochs": state["epochs"],
            "containers_to_extract_id": list(state["containers_to_extract_id"]),
        }

    def get_possible_actions(self, state: State) -> list[Action]:
        self.simulation.set_state(self.clone_state(state))
        return self.simulation.get_possible_actions()

    def apply_action(self, state: State, action: Action) -> State:
        self.simulation.set_state(self.clone_state(state))
        self.simulation.execute_action(action)
        return self.clone_state(self.simulation.get_state())

    def is_terminal(self, state: State) -> bool:
        self.simulation.set_state(self.clone_state(state))
        return self.simulation.is_simulation_end()

    def get_player_turn(self, state: State) -> int:
        return 0

    def rollout(self, state: State, root_player: int, rng: random.Random | None) -> float:
        rng = rng or self.rng
        rollout_start_state = self.clone_state(state)
        self.simulation.set_state(self.clone_state(rollout_start_state))
        rollout_limit = self._compute_rollout_limit()
        steps = 0
        while not self.simulation.is_simulation_end() and steps < rollout_limit:
            action = self._select_rollout_action(rng)
            if action is None:
                break
            self.simulation.run_one_epoch(action)
            steps += 1
        return self._evaluate_rollout_result(
            rollout_start_state=rollout_start_state,
        )

    def simulation_function(self, rollout_start_state: State) -> float:
        return self._evaluate_rollout_result(rollout_start_state)

    def _evaluate_rollout_result(self, rollout_start_state: State) -> float:
        is_terminal = self.simulation.is_simulation_end()
        weighted_blockage = 0.0 if is_terminal else self._compute_weighted_blockage()
        initial_weighted_blockage = self._compute_weighted_blockage_in_state(
            rollout_start_state
        )
        return self._evaluate_finished(
            total_time=self.simulation.time,
            total_epochs=self.simulation.epochs,
            is_terminal=is_terminal,
            weighted_blockage=weighted_blockage,
            initial_weighted_blockage=initial_weighted_blockage,
        )

    def _compute_rollout_limit(self) -> int:
        board_cells = (
            self.simulation.board_height
            * self.simulation.board_width
            * self.simulation.board_length
        )
        extraction_budget = max(1, len(self.simulation.containers_to_extract_id))
        return max(40, board_cells * 6 + extraction_budget * 10)

    def movement_choice_function(self, rng: random.Random) -> Action | None:
        return self._select_rollout_action(rng)

    def _select_rollout_action(self, rng: random.Random) -> Action | None:
        if self.simulation.is_simulation_end():
            return {"type": 3}

        target_to_extract = self.simulation.containers_to_extract_id[0]
        pending_set = set(self.simulation.containers_to_extract_id)
        board_size_cell = self.simulation.board_size_cell
        board = self.simulation.board
        board_height = self.simulation.board_height
        board_width = self.simulation.board_width
        board_length = self.simulation.board_length
        crane_position = self.simulation.crane_position

        best_move_rank = None
        best_move_actions = []

        for source_row in range(board_height):
            for source_col in range(board_width):
                source_size = board_size_cell[source_row][source_col]
                if source_size == 0:
                    continue

                top_container = board[source_row][source_col][source_size - 1]
                if top_container == target_to_extract:
                    return {"source_cell": (source_row, source_col), "type": 2}

                source_stack = board[source_row][source_col]
                source_unblocks_current_target = (
                    target_to_extract in source_stack[:source_size]
                    and top_container != target_to_extract
                )

                source_cell = (source_row, source_col)
                crane_to_source_cost = self._distance(crane_position, source_cell)

                for target_row in range(board_height):
                    for target_col in range(board_width):
                        if source_row == target_row and source_col == target_col:
                            continue
                        if board_size_cell[target_row][target_col] >= board_length:
                            continue

                        target_cell = (target_row, target_col)
                        move_cost = crane_to_source_cost + self._distance(
                            source_cell, target_cell
                        )

                        target_size = board_size_cell[target_row][target_col]
                        target_stack = board[target_row][target_col]
                        target_has_pending = any(
                            container_id in pending_set
                            for container_id in target_stack[:target_size]
                        )

                        move_rank = (
                            1 if source_unblocks_current_target else 0,
                            1 if not target_has_pending else 0,
                            -move_cost,
                        )

                        if best_move_rank is None or move_rank > best_move_rank:
                            best_move_rank = move_rank
                            best_move_actions = [
                                {
                                    "source_cell": source_cell,
                                    "target_cell": target_cell,
                                    "type": 1,
                                }
                            ]
                        elif move_rank == best_move_rank:
                            best_move_actions.append(
                                {
                                    "source_cell": source_cell,
                                    "target_cell": target_cell,
                                    "type": 1,
                                }
                            )

        if best_move_actions:
            return rng.choice(best_move_actions)
        return None

    def _evaluate_finished(
        self,
        total_time: int,
        total_epochs: int,
        is_terminal: bool = True,
        weighted_blockage: float = 0.0,
        initial_weighted_blockage: float = 0.0,
    ) -> float:
        non_terminal_penalty = 1000 if not is_terminal else 0
        blockage_penalty = self.blockage_weight * weighted_blockage
        initial_target_penalty = (
            self.initial_target_blockage_weight * initial_weighted_blockage
        )
        total_cost = (
            total_time
            + total_epochs
            + non_terminal_penalty
            + blockage_penalty
            + initial_target_penalty
        )
        return -float(total_cost)

    def _compute_weighted_blockage(self) -> float:
        pending_targets = self.simulation.containers_to_extract_id
        if not pending_targets:
            return 0.0

        target_blocks_above = self._build_blocks_above_index_in_state(
            self.simulation.get_state(),
            pending_targets,
        )
        weighted_blockage = 0.0
        for target_order, target_id in enumerate(pending_targets, start=1):
            weighted_blockage += target_blocks_above.get(target_id, 0) / target_order
        return weighted_blockage

    def _compute_weighted_blockage_in_state(self, state: State | None) -> float:
        if not state:
            return 0.0
        pending_targets = state["containers_to_extract_id"]
        if not pending_targets:
            return 0.0

        target_blocks_above = self._build_blocks_above_index_in_state(
            state,
            pending_targets,
        )
        weighted_blockage = 0.0
        for target_order, target_id in enumerate(pending_targets, start=1):
            weighted_blockage += target_blocks_above.get(target_id, 0) / target_order
        return weighted_blockage

    def _build_distance_cache(self) -> dict[tuple[Cell, Cell], int]:
        positions = [
            (row, col)
            for row in range(self.simulation.board_height)
            for col in range(self.simulation.board_width)
        ]
        distance_cache = {}
        for source in positions:
            for target in positions:
                distance_cache[(source, target)] = self.simulation.distance_function(
                    source, target
                )
        return distance_cache

    def _distance(self, source_cell: Cell, target_cell: Cell) -> int:
        return self._distance_cache[(source_cell, target_cell)]

    def _build_blocks_above_index_in_state(
        self,
        state: State,
        target_ids: list[int],
    ) -> dict[int, int]:
        remaining_targets = set(target_ids)
        blocks_above_by_target = {}

        board = state["board"]
        board_size_cell = state["board_size_cell"]
        board_height = state["board_height"]
        board_width = state["board_width"]

        for row in range(board_height):
            for col in range(board_width):
                stack_size = board_size_cell[row][col]
                if stack_size == 0:
                    continue
                stack = board[row][col]
                for depth in range(stack_size):
                    container_id = stack[depth]
                    if container_id in remaining_targets:
                        blocks_above_by_target[container_id] = stack_size - depth - 1
                        remaining_targets.remove(container_id)
                        if not remaining_targets:
                            return blocks_above_by_target

        return blocks_above_by_target
