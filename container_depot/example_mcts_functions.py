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
    def __init__(self, simulation, rng=None):
        self.simulation = copy.deepcopy(simulation)
        self.rng = rng or random.Random()

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
        self.simulation.set_state(self.clone_state(state))
        rollout_limit = self._compute_rollout_limit()
        steps = 0
        while not self.simulation.is_simulation_end() and steps < rollout_limit:
            actions = self.simulation.get_possible_actions()
            if not actions:
                break
            action = self._choose_rollout_action(actions, rng)
            self.simulation.run_one_epoch(action)
            steps += 1
        is_terminal = self.simulation.is_simulation_end()
        return self._evaluate_finished(
            total_time=self.simulation.time,
            total_epochs=self.simulation.epochs,
            is_terminal=is_terminal,
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
        extract_actions = [action for action in actions if action.get("type") == 2]
        if extract_actions:
            return extract_actions[0]

        move_actions = [action for action in actions if action.get("type") == 1]
        if move_actions:
            move_actions.sort(
                key=lambda action: self.simulation.calculate_move_cost(
                    action["source_cell"], action["target_cell"]
                )
            )
            cheapest_cost = self.simulation.calculate_move_cost(
                move_actions[0]["source_cell"], move_actions[0]["target_cell"]
            )
            cheapest_actions = [
                action
                for action in move_actions
                if self.simulation.calculate_move_cost(
                    action["source_cell"], action["target_cell"]
                )
                == cheapest_cost
            ]
            return rng.choice(cheapest_actions)

        end_actions = [action for action in actions if action.get("type") == 3]
        if end_actions:
            return end_actions[0]

        return rng.choice(actions)

    def _evaluate_finished(self, total_time, total_epochs, is_terminal=True):
        non_terminal_penalty = 1000 if not is_terminal else 0
        return 1 / (1 + total_time + total_epochs + non_terminal_penalty)