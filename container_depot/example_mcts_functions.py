import copy
import pickle
import random

import numpy as np

def selection_function(tree_nodes):
    uct_constant = 110
    selected_node = tree_nodes

    while selected_node.has_children():
        selection_value_uct = -1
        winner_node = None
        best_children = selected_node.children
        unvisited_children = [child for child in best_children if child.visits == 0]

        if len(unvisited_children) > 0:
            selected_node = random.choice(unvisited_children)

        else:
            for child in best_children:
                child_success_ratio = (child.value) / (child.visits)
                log_ratio = (np.log(selected_node.visits) / child.visits) ** 0.5
                child_value_uct = child_success_ratio + uct_constant * log_ratio

                if child_value_uct > selection_value_uct:
                    selection_value_uct = child_value_uct
                    winner_node = child

            selected_node = winner_node

    return selected_node


def expansion_function(node):
    return node.visits == 1 or len(node.children) == 1

def simulation_function(action_node, simulation_copy):
    simulation_copy.set_state(pickle.loads(pickle.dumps(action_node.get_simulation_state(), -1)))
    i = 1

    while not simulation_copy.is_simulation_end():

        possible_actions = simulation_copy.get_possible_actions()
        action = random.choice(possible_actions)
        simulation_copy.run_one_epoch(action)
        i += 1

    return simulation_copy

def retropropagation_function(original_simulation, simulation_finished, action_node):

    value_node = 1 / simulation_finished.epochs
    actual_node = action_node

    actual_node.visits += 1
    actual_node.value += value_node

    while actual_node.has_parent():
        actual_node = actual_node.parent
        actual_node.visits += 1
        actual_node.value += value_node

def movement_choice_function(tree_nodes):
    best_child_visits = -1
    best_child = None

    for child in tree_nodes.children:
        if child.visits > best_child_visits:
            best_child_visits = child.visits
            best_child = child

    return best_child


class ContainerDepotMCTSAdapter:
    def __init__(
        self,
        simulation,
        rng=None,
        blockage_weight=1.0,
        initial_target_blockage_weight=1.0,
    ):
        self.simulation = copy.deepcopy(simulation)
        self.rng = rng or random.Random()
        self.blockage_weight = blockage_weight
        self.initial_target_blockage_weight = initial_target_blockage_weight
        self._distance_cache = self._build_distance_cache()

    def get_initial_state(self):
        return self.clone_state(self.simulation.get_state())

    def clone_state(self, state):
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

    def get_possible_actions(self, state):
        self.simulation.set_state(self.clone_state(state))
        return self.simulation.get_possible_actions()

    def apply_action(self, state, action):
        self.simulation.set_state(self.clone_state(state))
        self.simulation.execute_action(action)
        return self.clone_state(self.simulation.get_state())

    def is_terminal(self, state):
        self.simulation.set_state(self.clone_state(state))
        return self.simulation.is_simulation_end()

    def get_player_turn(self, state):
        return 0

    def rollout(self, state, root_player, rng):
        rng = rng or self.rng
        rollout_start_state = self.clone_state(state)
        self.simulation.set_state(self.clone_state(rollout_start_state))
        rollout_limit = self._compute_rollout_limit()
        steps = 0
        while not self.simulation.is_simulation_end() and steps < rollout_limit:
            action = self._choose_rollout_action_fast(rng)
            if action is None:
                break
            self.simulation.run_one_epoch(action)
            steps += 1
        return self._evaluate_simulation_state(
            rollout_start_state=rollout_start_state,
        )

    def _evaluate_simulation_state(self, rollout_start_state):
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

    def _compute_rollout_limit(self):
        board_cells = (
            self.simulation.board_height
            * self.simulation.board_width
            * self.simulation.board_length
        )
        extraction_budget = max(1, len(self.simulation.containers_to_extract_id))
        return max(40, board_cells * 6 + extraction_budget * 10)

    def _choose_rollout_action(self, actions, rng):
        best_move_cost = None
        best_move_actions = []
        fallback_end_action = None

        for action in actions:
            action_type = action.get("type")
            if action_type == 2:
                return action
            if action_type == 1:
                move_cost = self.simulation.calculate_move_cost(
                    action["source_cell"], action["target_cell"]
                )
                if best_move_cost is None or move_cost < best_move_cost:
                    best_move_cost = move_cost
                    best_move_actions = [action]
                elif move_cost == best_move_cost:
                    best_move_actions.append(action)
            elif action_type == 3 and fallback_end_action is None:
                fallback_end_action = action

        if best_move_actions:
            return rng.choice(best_move_actions)
        if fallback_end_action is not None:
            return fallback_end_action
        return rng.choice(actions)

    def _choose_rollout_action_fast(self, rng):
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
        total_time,
        total_epochs,
        is_terminal=True,
        weighted_blockage=0.0,
        initial_weighted_blockage=0.0,
    ):
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

    def _compute_weighted_blockage(self):
        pending_targets = self.simulation.containers_to_extract_id
        if not pending_targets:
            return 0.0

        target_blocks_above = self._build_blocks_above_index(pending_targets)
        weighted_blockage = 0.0
        for target_order, target_id in enumerate(pending_targets, start=1):
            weighted_blockage += target_blocks_above.get(target_id, 0) / target_order
        return weighted_blockage

    def _compute_weighted_blockage_in_state(self, state):
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

    def _build_distance_cache(self):
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

    def _distance(self, source_cell, target_cell):
        return self._distance_cache[(source_cell, target_cell)]

    def _build_blocks_above_index(self, target_ids):
        return self._build_blocks_above_index_in_state(
            self.simulation.get_state(),
            target_ids,
        )

    def _build_blocks_above_index_in_state(self, state, target_ids):
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

    def _count_blocks_above(self, target_id):
        return self._count_blocks_above_in_state(self.simulation.get_state(), target_id)

    def _count_blocks_above_in_state(self, state, target_id):
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
                    if stack[depth] == target_id:
                        return stack_size - depth - 1
        return 0