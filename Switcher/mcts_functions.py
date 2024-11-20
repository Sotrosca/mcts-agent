import copy
import pickle
import random

import numpy as np

from MCTSAgent.MCTSAgent import Node
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
    return node.visits == 2 or len(node.childs) == 1


def simulation_function(action_node: Node, simulation_copy: SwitcherSimulation):
    state = action_node.get_simulation_state()
    simulation_copy.set_state(state)
    i = 0

    while simulation_copy.player_winner() == None and i < 4:
        possible_actions = simulation_copy.get_possible_actions()
        action = random.choice(possible_actions)
        simulation_copy.execute_action(action)
        i += 1

    return simulation_copy


def retropropagation_function_2(
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


def retropropagation_function(
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
    best_child = None

    for child in tree_nodes.childs:
        if child.visits > best_child_visits:
            best_child_visits = child.visits
            best_child = child

    return best_child
