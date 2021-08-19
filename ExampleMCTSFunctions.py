import random
import numpy as np
import pickle

def selection_function(tree_nodes):
    UCT_constant = 0.000000000001
    selected_node = tree_nodes

    while selected_node.has_childs():
        selection_value_UCT = -1
        winner_node = None
        best_childs = selected_node.childs
        best_childs_without_love = list(filter(lambda x: x.visits == 0, best_childs))

        if len(best_childs_without_love) > 0:
            selected_node = random.choice(best_childs_without_love)

        else:
            for child in best_childs:
                child_success_ratio = (child.value + 1) / (child.visits + 1)
                log_ratio = (np.log(selected_node.visits) / child.visits) ** 0.5
                child_value_UCT = child_success_ratio + UCT_constant * log_ratio

                if child_value_UCT > selection_value_UCT:
                    selection_value_UCT = child_value_UCT
                    winner_node = child

            selected_node = winner_node

    return selected_node


def expansion_function(node):
    return node.visits == 1 or len(node.childs) == 1

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
    value_node = 1 / simulation_finished.time
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

    for child in tree_nodes.childs:
        if child.visits > best_child_visits:
            best_child_visits = child.visits
            best_child = child

    return best_child