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
        return copy.deepcopy(state)

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
        while not self.simulation.is_simulation_end():
            actions = self.simulation.get_possible_actions()
            if not actions:
                break
            action = rng.choice(actions)
            self.simulation.run_one_epoch(action)
        return self._evaluate_finished()

    def _evaluate_finished(self):
        return 1 / max(1, self.simulation.epochs)