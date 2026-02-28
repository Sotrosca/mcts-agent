import pytest

from container_depot.simulation import Simulation


def manhattan_distance(x_position, y_position):
    return abs(x_position[0] - y_position[0]) + abs(x_position[1] - y_position[1])


def build_simulation(board, pending):
    return Simulation((0, 0), board, 0, manhattan_distance, pending)


def test_get_possible_actions_generates_only_valid_moves():
    board = [
        [[1, 0], [2, 3]],
        [[0, 0], [4, 0]],
    ]
    simulation = build_simulation(board, [1])

    actions = simulation.get_possible_actions()
    move_actions = [action for action in actions if action["type"] == 1]

    assert move_actions
    for action in move_actions:
        source = action["source_cell"]
        target = action["target_cell"]
        assert source != target
        assert simulation.board_size_cell[source[0]][source[1]] > 0
        assert simulation.board_size_cell[target[0]][target[1]] < simulation.board_length


def test_get_possible_actions_includes_extract_for_top_target_container():
    board = [
        [[1, 0], [2, 0]],
        [[0, 0], [0, 0]],
    ]
    simulation = build_simulation(board, [1, 2])

    actions = simulation.get_possible_actions()

    assert {"source_cell": (0, 0), "type": 2} in actions


def test_execute_action_rejects_invalid_move_action():
    board = [
        [[1, 0], [2, 3]],
        [[0, 0], [4, 0]],
    ]
    simulation = build_simulation(board, [1])

    with pytest.raises(ValueError, match="Invalid move action"):
        simulation.execute_action({"source_cell": (1, 0), "target_cell": (0, 0), "type": 1})


def test_execute_action_rejects_invalid_extract_action():
    board = [
        [[2, 0], [1, 0]],
        [[0, 0], [0, 0]],
    ]
    simulation = build_simulation(board, [1])

    with pytest.raises(ValueError, match="Invalid extract action"):
        simulation.execute_action({"source_cell": (0, 0), "type": 2})
