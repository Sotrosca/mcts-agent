import copy
import random
import time

from container_depot.container_depot_simulation import Simulation
from container_depot.example_mcts_functions import ContainerDepotMCTSAdapter
from container_depot.scenarios import get_container_depot_scenarios, manhattan_distance
from mcts_agent.core import MonteCarloPlayer


def _build_player_for_scenario(scenario, seed=0):
    simulation = Simulation(
        (0, 0),
        copy.deepcopy(scenario["board"]),
        0,
        manhattan_distance,
        list(scenario["pending"]),
    )
    adapter = ContainerDepotMCTSAdapter(simulation, rng=random.Random(seed))
    player = MonteCarloPlayer(adapter, rng=random.Random(seed), exploration_constant=1.2)
    return simulation, player


def _is_action_valid(simulation, action):
    action_type = action.get("type")
    if action_type == 1:
        return simulation._is_valid_move_action(action.get("source_cell"), action.get("target_cell"))
    if action_type == 2:
        return simulation._is_valid_extract_action(action.get("source_cell"))
    if action_type == 3:
        return simulation.is_simulation_end()
    return False


def test_search_best_move_returns_valid_action_in_non_terminal_state():
    scenario = get_container_depot_scenarios()[0]
    simulation, player = _build_player_for_scenario(scenario, seed=11)

    action_node = player.search_best_move(rollouts=20)

    assert action_node is not None
    assert _is_action_valid(simulation, action_node.action)


def test_mcts_short_episode_runs_without_invalid_actions_or_hangs():
    scenario = get_container_depot_scenarios()[1]
    simulation, player = _build_player_for_scenario(scenario, seed=22)

    start = time.time()
    max_steps = 20
    steps = 0
    while not simulation.is_simulation_end() and steps < max_steps:
        action_node = player.search_best_move(rollouts=20)
        assert action_node is not None
        assert _is_action_valid(simulation, action_node.action)
        simulation.execute_action(action_node.action)
        player.execute_action_on_simulation(action_node)
        steps += 1

    assert time.time() - start < 5
    assert steps > 0


def test_mcts_continues_search_after_tree_rebase():
    scenario = get_container_depot_scenarios()[0]
    simulation, player = _build_player_for_scenario(scenario, seed=33)

    first = player.search_best_move(rollouts=15)
    assert first is not None
    simulation.execute_action(first.action)
    player.execute_action_on_simulation(first)

    second = player.search_best_move(rollouts=15)
    assert second is not None
    assert _is_action_valid(simulation, second.action)
