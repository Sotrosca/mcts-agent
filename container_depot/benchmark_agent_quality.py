import argparse
import copy
import random
import statistics
import time
from collections import defaultdict

from container_depot.container_depot_simulation import Simulation
from container_depot.example_mcts_functions import ContainerDepotMCTSAdapter
from container_depot.scenarios import get_container_depot_scenarios, manhattan_distance
from mcts_agent.core import MonteCarloPlayer


def choose_greedy_action(simulation, actions, rng):
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


def run_episode(scenario, policy_name, seed, timeout_seconds=3):
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

    steps = 0
    invalid_actions = 0
    start = time.time()
    while not simulation.is_simulation_end() and steps < scenario["max_steps"]:
        if time.time() - start > timeout_seconds:
            break
        actions = simulation.get_possible_actions()
        if not actions:
            break

        if policy_name == "mcts":
            action_node = player.search_best_move(rollouts=scenario["rollouts_per_move"])
            if action_node is None:
                break
            action = action_node.action
        elif policy_name == "random":
            action = rng.choice(actions)
        else:
            action = choose_greedy_action(simulation, actions, rng)

        try:
            simulation.execute_action(action)
        except ValueError:
            invalid_actions += 1
            break

        if policy_name == "mcts":
            player.execute_action_on_simulation(action_node)
        steps += 1

    return {
        "solved": simulation.is_simulation_end(),
        "score": simulation.time + simulation.epochs,
        "invalid_actions": invalid_actions,
        "timed_out": (time.time() - start) > timeout_seconds,
    }


def summarize(results):
    return {
        "episodes": len(results),
        "completion_rate": sum(1 for result in results if result["solved"]) / len(results),
        "avg_score": sum(result["score"] for result in results) / len(results),
        "median_score": statistics.median(result["score"] for result in results),
        "invalid_actions": sum(result["invalid_actions"] for result in results),
        "timeouts": sum(1 for result in results if result["timed_out"]),
    }


def make_bar(value, max_value, width=24):
    if max_value <= 0:
        return "-" * width
    filled = int(round((value / max_value) * width))
    filled = max(0, min(width, filled))
    return "#" * filled + "." * (width - filled)


def print_policy_summary(all_results_by_policy):
    print("\n=== Global Summary ===")
    for policy, results in all_results_by_policy.items():
        summary = summarize(results)
        print(
            f"policy={policy:<7} episodes={summary['episodes']:<3} "
            f"completion={summary['completion_rate']:.2f} "
            f"avg_score={summary['avg_score']:.2f} "
            f"median_score={summary['median_score']:.2f} "
            f"invalid_actions={summary['invalid_actions']} "
            f"timeouts={summary['timeouts']}"
        )


def print_scenario_table(scenario_results):
    print("\n=== Per Scenario Comparison (lower avg_score is better) ===")
    header = (
        "scenario".ljust(18)
        + "policy".ljust(10)
        + "completion".ljust(12)
        + "avg_score".ljust(12)
        + "score_bar"
    )
    print(header)
    print("-" * len(header))

    all_avg_scores = []
    for scenario_name in scenario_results:
        for policy in scenario_results[scenario_name]:
            all_avg_scores.append(summarize(scenario_results[scenario_name][policy])["avg_score"])
    max_avg_score = max(all_avg_scores) if all_avg_scores else 1

    for scenario_name, policy_map in scenario_results.items():
        for policy, results in policy_map.items():
            summary = summarize(results)
            bar = make_bar(summary["avg_score"], max_avg_score)
            print(
                f"{scenario_name:<18}{policy:<10}{summary['completion_rate']:.2f}{'':<8}"
                f"{summary['avg_score']:<12.2f}{bar}"
            )


def print_episode_comparison(episode_records, left_policy, right_policy):
    print(
        f"\n=== Episode Detail: {left_policy} vs {right_policy} "
        f"(negative delta means {left_policy} better) ==="
    )
    print("scenario            episode   left_score   right_score  delta")
    print("---------------------------------------------------------------")

    left_better = 0
    right_better = 0
    ties = 0

    for (scenario_name, episode_idx), policy_results in sorted(episode_records.items()):
        if left_policy not in policy_results or right_policy not in policy_results:
            continue
        left = policy_results[left_policy]["score"]
        right = policy_results[right_policy]["score"]
        delta = left - right
        if delta < 0:
            left_better += 1
        elif delta > 0:
            right_better += 1
        else:
            ties += 1
        print(f"{scenario_name:<18}{episode_idx:<10}{left:<13}{right:<13}{delta:+}")

    total = left_better + right_better + ties
    if total > 0:
        print(
            f"wins {left_policy}={left_better}, {right_policy}={right_better}, ties={ties}"
        )


def main():
    parser = argparse.ArgumentParser(description="Benchmark ContainerDepot policies")
    parser.add_argument("--episodes-per-scenario", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    parser.add_argument(
        "--short-set-only",
        action="store_true",
        help="Run only short set scenarios (small_easy and medium_realistic)",
    )
    parser.add_argument(
        "--show-episode-detail",
        action="store_true",
        help="Print per-episode score comparison for mcts vs greedy",
    )
    args = parser.parse_args()

    scenarios = get_container_depot_scenarios()
    if args.short_set_only:
        scenarios = scenarios[:2]
    policies = ["mcts", "greedy", "random"]

    all_results_by_policy = {policy: [] for policy in policies}
    scenario_results = defaultdict(lambda: defaultdict(list))
    episode_records = defaultdict(dict)

    for policy in policies:
        for scenario in scenarios:
            for episode_idx in range(args.episodes_per_scenario):
                seed = episode_idx
                result = run_episode(scenario, policy, seed, args.timeout_seconds)
                all_results_by_policy[policy].append(result)
                scenario_results[scenario["name"]][policy].append(result)
                episode_records[(scenario["name"], episode_idx)][policy] = result

    print_policy_summary(all_results_by_policy)
    print_scenario_table(scenario_results)
    if args.show_episode_detail:
        print_episode_comparison(episode_records, "mcts", "greedy")


if __name__ == "__main__":
    main()
