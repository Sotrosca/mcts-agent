import copy
import random
import statistics

from container_depot.container_depot_simulation import Simulation
from container_depot.example_mcts_functions import ContainerDepotMCTSAdapter
from container_depot.scenarios import get_container_depot_scenarios, manhattan_distance
from mcts_agent.core import MonteCarloPlayer


TEST_MAX_STEPS = 20
TEST_MAX_ROLLOUTS = 30


def _run_policy_episode(scenario, policy_name, seed):
    simulation = Simulation(
        (0, 0),
        copy.deepcopy(scenario["board"]),
        0,
        manhattan_distance,
        list(scenario["pending"]),
    )
    rng = random.Random(seed)

    if policy_name == "mcts":
        adapter = ContainerDepotMCTSAdapter(simulation, rng=random.Random(seed))
        player = MonteCarloPlayer(adapter, rng=random.Random(seed))
    else:
        player = None

    invalid_actions = 0
    steps = 0
    max_steps = min(TEST_MAX_STEPS, scenario["max_steps"])
    rollouts = min(TEST_MAX_ROLLOUTS, scenario["rollouts_per_move"])
    while not simulation.is_simulation_end() and steps < max_steps:
        actions = simulation.get_possible_actions()
        if not actions:
            break

        if policy_name == "mcts":
            action_node = player.search_best_move(rollouts=rollouts)
            if action_node is None:
                break
            action = action_node.action
        elif policy_name == "random":
            action = rng.choice(actions)
        else:
            action = _choose_greedy_action(simulation, actions, rng)

        try:
            simulation.execute_action(action)
        except ValueError:
            invalid_actions += 1
            break

        if policy_name == "mcts":
            player.execute_action_on_simulation(action_node)
        steps += 1

    score = simulation.time + simulation.epochs
    return {
        "solved": simulation.is_simulation_end(),
        "score": score,
        "invalid_actions": invalid_actions,
    }


def _choose_greedy_action(simulation, actions, rng):
    extract_actions = [action for action in actions if action.get("type") == 2]
    if extract_actions:
        return extract_actions[0]

    move_actions = [action for action in actions if action.get("type") == 1]
    if move_actions:
        best_cost = min(
            simulation.calculate_move_cost(action["source_cell"], action["target_cell"])
            for action in move_actions
        )
        best_actions = [
            action
            for action in move_actions
            if simulation.calculate_move_cost(action["source_cell"], action["target_cell"])
            == best_cost
        ]
        return rng.choice(best_actions)

    end_actions = [action for action in actions if action.get("type") == 3]
    if end_actions:
        return end_actions[0]

    return rng.choice(actions)


def _aggregate(results):
    completion_rate = sum(1 for result in results if result["solved"]) / len(results)
    avg_score = sum(result["score"] for result in results) / len(results)
    median_score = statistics.median(result["score"] for result in results)
    invalid_actions = sum(result["invalid_actions"] for result in results)
    return {
        "completion_rate": completion_rate,
        "avg_score": avg_score,
        "median_score": median_score,
        "invalid_actions": invalid_actions,
    }


def test_mcts_quality_is_not_worse_than_random_baseline():
    scenarios = get_container_depot_scenarios()[:2]
    seeds = [0, 1, 2]

    mcts_results = []
    random_results = []
    for scenario in scenarios:
        for seed in seeds:
            mcts_results.append(_run_policy_episode(scenario, "mcts", seed))
            random_results.append(_run_policy_episode(scenario, "random", seed))

    mcts_stats = _aggregate(mcts_results)
    random_stats = _aggregate(random_results)

    assert mcts_stats["invalid_actions"] == 0
    assert random_stats["invalid_actions"] == 0
    assert mcts_stats["avg_score"] < 1000
    assert random_stats["avg_score"] < 1000


def test_mcts_quality_stays_close_to_greedy_baseline():
    scenarios = get_container_depot_scenarios()[:2]
    seeds = [3, 4, 5]

    mcts_results = []
    greedy_results = []
    for scenario in scenarios:
        for seed in seeds:
            mcts_results.append(_run_policy_episode(scenario, "mcts", seed))
            greedy_results.append(_run_policy_episode(scenario, "greedy", seed))

    mcts_stats = _aggregate(mcts_results)
    greedy_stats = _aggregate(greedy_results)

    assert mcts_stats["invalid_actions"] == 0
    assert greedy_stats["invalid_actions"] == 0
    assert mcts_stats["avg_score"] < 1000
