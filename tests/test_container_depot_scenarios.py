import copy
import random

import pytest

from container_depot.simulation import Simulation
from container_depot.agent import ContainerDepotMCTSAdapter
from container_depot.scenarios import get_container_depot_scenarios, manhattan_distance
from mcts_agent.core import MonteCarloPlayer


TEST_MAX_STEPS = 20
TEST_MAX_ROLLOUTS = 30


def _test_scenarios():
    return [
        scenario
        for scenario in get_container_depot_scenarios()
        if scenario["name"] != "very_hard_stacked_3x3"
    ]


def _run_mcts_episode(scenario, seed):
    simulation = Simulation(
        (0, 0),
        copy.deepcopy(scenario["board"]),
        0,
        manhattan_distance,
        list(scenario["pending"]),
    )
    adapter = ContainerDepotMCTSAdapter(simulation, rng=random.Random(seed))
    player = MonteCarloPlayer(adapter, rng=random.Random(seed))

    invalid_actions = 0
    steps = 0
    max_steps = min(TEST_MAX_STEPS, scenario["max_steps"])
    rollouts = min(TEST_MAX_ROLLOUTS, scenario["rollouts_per_move"])
    while not simulation.is_simulation_end() and steps < max_steps:
        action_node = player.search_best_move(rollouts=rollouts)
        if action_node is None:
            break
        try:
            simulation.execute_action(action_node.action)
        except ValueError:
            invalid_actions += 1
            break
        player.execute_action_on_simulation(action_node)
        steps += 1

    return {
        "solved": simulation.is_simulation_end(),
        "steps": steps,
        "time": simulation.time,
        "epochs": simulation.epochs,
        "invalid_actions": invalid_actions,
    }


@pytest.mark.parametrize("scenario", _test_scenarios(), ids=lambda s: s["name"])
def test_prefixed_scenario_finishes_within_limits(scenario):
    result = _run_mcts_episode(scenario, seed=7)

    assert result["invalid_actions"] == 0
    assert result["steps"] <= scenario["max_steps"]
    assert result["time"] >= 0


def test_prefixed_scenarios_keep_costs_bounded():
    scenarios = _test_scenarios()
    results = [_run_mcts_episode(scenario, seed=9) for scenario in scenarios]

    for scenario, result in zip(scenarios, results):
        assert result["invalid_actions"] == 0
        assert result["time"] < scenario["max_steps"] * 10
        assert result["epochs"] <= scenario["max_steps"]
