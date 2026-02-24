import random

from container_depot.container_depot_simulation import Simulation
from container_depot.example_mcts_functions import ContainerDepotMCTSAdapter


def manhattan_distance(x_position, y_position):
    return abs(x_position[0] - y_position[0]) + abs(x_position[1] - y_position[1])


def build_adapter(board, pending):
    simulation = Simulation((0, 0), board, 0, manhattan_distance, pending)
    return ContainerDepotMCTSAdapter(simulation, rng=random.Random(0))


def test_clone_state_returns_independent_nested_data():
    adapter = build_adapter(
        [
            [[1, 0], [2, 0]],
            [[0, 0], [0, 0]],
        ],
        [1, 2],
    )

    state = adapter.get_initial_state()
    cloned = adapter.clone_state(state)

    cloned["board"][0][0][0] = 99
    cloned["board_size_cell"][0][0] = 0
    cloned["containers_to_extract_id"].append(100)

    assert state["board"][0][0][0] == 1
    assert state["board_size_cell"][0][0] == 1
    assert 100 not in state["containers_to_extract_id"]


def test_rollout_prioritizes_extract_when_available():
    adapter = build_adapter(
        [
            [[1, 0], [0, 0]],
            [[0, 0], [0, 0]],
        ],
        [1],
    )
    state = adapter.get_initial_state()

    reward = adapter.rollout(state, root_player=0, rng=random.Random(0))

    assert reward == 1 / (1 + 1 + 1)


def test_evaluate_finished_uses_time_and_epochs():
    adapter = build_adapter(
        [
            [[1, 0], [0, 0]],
            [[0, 0], [0, 0]],
        ],
        [1],
    )

    assert adapter._evaluate_finished(total_time=0, total_epochs=0) == 1.0
    assert adapter._evaluate_finished(total_time=4, total_epochs=2) == 1 / 7


def test_evaluate_finished_penalizes_non_terminal_rollout():
    adapter = build_adapter(
        [
            [[1, 0], [0, 0]],
            [[0, 0], [0, 0]],
        ],
        [1],
    )

    terminal_value = adapter._evaluate_finished(
        total_time=5,
        total_epochs=2,
        is_terminal=True,
    )
    non_terminal_value = adapter._evaluate_finished(
        total_time=5,
        total_epochs=2,
        is_terminal=False,
    )

    assert non_terminal_value < terminal_value


def test_rollout_returns_for_non_terminating_scenario():
    adapter = build_adapter(
        [
            [[2, 0], [0, 0]],
            [[0, 0], [0, 0]],
        ],
        [1],
    )
    state = adapter.get_initial_state()

    reward = adapter.rollout(state, root_player=0, rng=random.Random(0))

    assert reward > 0
    assert reward < 1 / 100
