import pickle
import random

import numpy as np

import numpy as np

from MCTSAgent.MCTSAgent import Node
from Switcher.logic.board import Cell
from Switcher.mcts_simulation import SwitcherSimulation


def selection_function(tree_nodes: Node):
    UCT_constant = 1
    selected_node = tree_nodes

    while selected_node.has_childs():
        selection_value_UCT = -100000000
        winner_node = None
        best_childs = selected_node.childs
        best_childs_without_love = list(filter(lambda x: x.visits == 0, best_childs))

        if len(best_childs_without_love) > 0:
            selected_node = random.choice(best_childs_without_love)

        else:
            for child in best_childs:
                child_success_ratio = (child.value) / (child.visits)
                log_ratio = (np.log(selected_node.visits) / child.visits) ** 0.5
                child_value_UCT = child_success_ratio + UCT_constant * log_ratio

                if child_value_UCT > selection_value_UCT:
                    selection_value_UCT = child_value_UCT
                    winner_node = child

            selected_node = winner_node

    return selected_node


def expansion_function(node):
    return node.visits == 1 or len(node.childs) == 1


def simulation_function(action_node: Node, simulation_copy: SwitcherSimulation):
    state = action_node.get_simulation_state()
    simulation_copy.set_state(state)
    i = 0

    while simulation_copy.player_winner() == None and i < 10:
        possible_actions = simulation_copy.get_possible_actions()
        action = random.choice(possible_actions)
        simulation_copy.execute_action(action)
        i += 1

    return simulation_copy


def retropropagation_function(
    original_simulation: SwitcherSimulation,
    simulation_finished: SwitcherSimulation,
    action_node: Node,
):

    player_turn = original_simulation.logic.player_turn
    player_winner = simulation_finished.player_winner()
    if player_winner == player_turn:
        value_node = 10
    elif player_winner is not None and player_winner != player_turn:
        value_node = -10
    else:
        value_node = 1 * len(
            simulation_finished.logic.players[player_turn].figures_played
        ) - len(original_simulation.logic.players[player_turn].figures_played)

    actual_node = action_node
    actual_node.visits += 1
    actual_node.value += value_node

    while actual_node.has_parent():
        actual_node = actual_node.parent
        actual_node.visits += 1
        if actual_node.simulation_state["player_turn"] == player_turn:
            actual_node.value += value_node
        else:
            actual_node.value += value_node * -1


def retropropagation_function_2(
    original_simulation: SwitcherSimulation,
    simulation_finished: SwitcherSimulation,
    action_node: Node,
):

    player_turn = original_simulation.logic.player_turn
    player_winner = simulation_finished.player_winner()
    original_simulation_state = original_simulation.get_state()
    simulation_finished_state = simulation_finished.get_state()

    player_str = "player" + str(player_turn + 1) + "_state"
    opp_player_str = "player" + str((player_turn + 1) % 2 + 1) + "_state"

    if player_winner == player_turn:
        value_node = 10
    elif player_winner is not None and player_winner != player_turn:
        value_node = -10
    else:
        value_node = len(simulation_finished_state[player_str]["figures_played"]) - len(
            original_simulation_state[player_str]["figures_played"]
        )

        value_node -= (
            len(simulation_finished_state[opp_player_str]["figures_played"])
            - len(original_simulation_state[opp_player_str]["figures_played"])
        ) * 0.8

    actual_node = action_node
    actual_node.visits += 1
    actual_node.value += value_node

    while actual_node.has_parent():
        actual_node = actual_node.parent
        actual_node.visits += 1
        if actual_node.simulation_state["player_turn"] == player_turn:
            actual_node.value += value_node
        else:
            actual_node.value += value_node * -1


def movement_choice_function(tree_nodes: Node):
    best_child_visits = -1
    best_childs = None

    for child in tree_nodes.childs:
        if child.visits > best_child_visits:
            best_child_visits = child.visits
            best_childs = [child]
        elif child.visits == best_child_visits:
            best_childs.append(child)

    return random.choice(best_childs)


class SwitcherMCTSAdapter:
    def __init__(self, simulation: SwitcherSimulation, rollout_limit=10, rng=None):
        self.simulation = pickle.loads(pickle.dumps(simulation, -1))
        self.rollout_limit = rollout_limit
        self.rng = rng or random.Random()

    def get_initial_state(self):
        return self.clone_state(self.simulation.get_state())

    def clone_state(self, state):
        board_state = state.get("board_state")
        board_copy = np.empty(board_state.shape, dtype=Cell)
        for y in range(board_state.shape[0]):
            for x in range(board_state.shape[1]):
                cell = board_state[y][x]
                new_cell = Cell(cell.color)
                new_cell.selected = cell.selected
                new_cell.set_position(y, x)
                board_copy[y][x] = new_cell

        return {
            "board_state": board_copy,
            "moves_deck": list(state.get("moves_deck")),
            "moves_discard": list(state.get("moves_discard")),
            "last_color_played": state.get("last_color_played"),
            "player_turn": state.get("player_turn"),
            "turn": state.get("turn"),
            "winner": state.get("winner"),
            "player1_state": {
                "figures_slots": dict(state["player1_state"]["figures_slots"]),
                "figures_played": list(state["player1_state"]["figures_played"]),
                "figures_blocked": dict(state["player1_state"]["figures_blocked"]),
                "figures_deck": list(state["player1_state"]["figures_deck"]),
                "hand": dict(state["player1_state"]["hand"]),
                "hand_size": state["player1_state"]["hand_size"],
                "is_blocked": state["player1_state"]["is_blocked"],
            },
            "player2_state": {
                "figures_slots": dict(state["player2_state"]["figures_slots"]),
                "figures_played": list(state["player2_state"]["figures_played"]),
                "figures_blocked": dict(state["player2_state"]["figures_blocked"]),
                "figures_deck": list(state["player2_state"]["figures_deck"]),
                "hand": dict(state["player2_state"]["hand"]),
                "hand_size": state["player2_state"]["hand_size"],
                "is_blocked": state["player2_state"]["is_blocked"],
            },
        }

    def get_possible_actions(self, state):
        self.simulation.set_state(self.clone_state(state), copy_state=False)
        return self.simulation.get_possible_actions()

    def apply_action(self, state, action):
        self.simulation.set_state(self.clone_state(state), copy_state=False)
        self.simulation.execute_action(action)
        return self.clone_state(self.simulation.get_state())

    def is_terminal(self, state):
        self.simulation.set_state(self.clone_state(state), copy_state=False)
        return self.simulation.player_winner() is not None

    def get_player_turn(self, state):
        return state.get("player_turn")

    def rollout(self, state, root_player, rng):
        rng = rng or self.rng
        self.simulation.set_state(self.clone_state(state), copy_state=False)
        steps = 0
        while self.simulation.player_winner() is None and steps < self.rollout_limit:
            actions = self.simulation.get_possible_actions()
            if not actions:
                break
            action = rng.choice(actions)
            self.simulation.execute_action(action)
            steps += 1
        return self._evaluate_finished(state, root_player)

    def _evaluate_finished(self, base_state, root_player):
        player_winner = self.simulation.player_winner()
        if player_winner == root_player:
            return 10
        if player_winner is not None and player_winner != root_player:
            return -10
        player_state_key = f"player{root_player + 1}_state"
        base_figures = len(base_state[player_state_key]["figures_played"])
        finished_figures = len(
            self.simulation.logic.players[root_player].figures_played
        )
        return finished_figures - base_figures
