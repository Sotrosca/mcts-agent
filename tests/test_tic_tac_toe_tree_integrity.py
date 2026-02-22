import random

from mcts_agent.core import MonteCarloPlayer
from tic_tac_toe.tic_tac_toe_logic import TicTacToe
from tic_tac_toe.tic_tac_toe_mcts_functions import TicTacToeMCTSAdapter


def _build_player():
    game = TicTacToe()
    adapter = TicTacToeMCTSAdapter(game, rng=random.Random(123))
    return MonteCarloPlayer(adapter, exploration_constant=0.0, rng=random.Random(123))


def test_sibling_nodes_keep_independent_states():
    player = _build_player()

    first_child = player.expand_node(player.action_tree)
    second_child = player.expand_node(player.action_tree)

    assert first_child is not None
    assert second_child is not None

    first_board = first_child.get_simulation_state()["board"]
    second_board = second_child.get_simulation_state()["board"]

    first_board[0][0] = "Z"

    assert second_board[0][0] == " "
    assert player.action_tree.get_simulation_state()["board"][0][0] == " "


def test_backpropagation_updates_only_selected_branch_and_ancestors():
    player = _build_player()

    first_child = player.expand_node(player.action_tree)
    second_child = player.expand_node(player.action_tree)

    assert first_child is not None
    assert second_child is not None

    player._backpropagate(first_child, 1)

    assert first_child.visits == 1
    assert first_child.value == 1
    assert second_child.visits == 0
    assert second_child.value == 0
    assert player.action_tree.visits == 1
    assert player.action_tree.value == 1


def test_tree_evaluates_winning_move_in_controlled_state():
    player = _build_player()

    winning_state = {
        "board": [["X", "X", " "], ["O", "O", " "], [" ", " ", " "]],
        "player_one_move": True,
        "turn": 4,
        "player_turn_figure": "X",
    }

    player.reset_root(winning_state)
    best_move = player.search_best_move(rollouts=120)

    assert best_move is not None
    assert best_move.action == (0, 2)