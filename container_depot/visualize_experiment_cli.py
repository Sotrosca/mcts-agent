import argparse
import copy
import random
import statistics
import time

from container_depot.benchmark_agent_quality import choose_greedy_action
from container_depot.simulation import Simulation
from container_depot.agent import ContainerDepotMCTSAdapter
from container_depot.scenarios import get_container_depot_scenarios, manhattan_distance
from mcts_agent.core import MonteCarloPlayer


def format_action(action):
    if action is None:
        return "None"
    action_type = action.get("type")
    if action_type == 1:
        return f"MOVE {action['source_cell']} -> {action['target_cell']}"
    if action_type == 2:
        return f"EXTRACT {action['source_cell']}"
    if action_type == 3:
        return "END"
    return str(action)


def board_to_lines(simulation):
    lines = []
    header = f"crane={simulation.crane_position} pending={simulation.containers_to_extract_id}"
    lines.append(header)
    for row_index in range(simulation.board_height):
        row_cells = []
        for col_index in range(simulation.board_width):
            stack = simulation.board[row_index][col_index]
            row_cells.append("[" + ",".join(str(value) for value in stack) + "]")
        lines.append(f"row{row_index}: " + " ".join(row_cells))
    return lines


def print_side_by_side(left_title, left_lines, right_title, right_lines, width=70):
    max_lines = max(len(left_lines), len(right_lines))
    padded_left = left_lines + [""] * (max_lines - len(left_lines))
    padded_right = right_lines + [""] * (max_lines - len(right_lines))

    print(f"{left_title:<{width}} | {right_title}")
    print("-" * width + "-+-" + "-" * width)
    for left, right in zip(padded_left, padded_right):
        print(f"{left:<{width}} | {right}")


def get_mcts_top_candidates(player, top_k):
    children = player.action_tree.children
    ranked = sorted(
        children,
        key=lambda child: (
            child.visits,
            (child.value / child.visits) if child.visits else 0.0,
        ),
        reverse=True,
    )
    lines = []
    for index, child in enumerate(ranked[:top_k], start=1):
        avg = (child.value / child.visits) if child.visits else 0.0
        lines.append(
            f"#{index} {format_action(child.action)} visits={child.visits} value={child.value:.4f} avg={avg:.4f}"
        )
    return lines


def get_tree_stats(root):
    stack = [(root, 0)]
    total_nodes = 0
    total_edges = 0
    leaf_nodes = 0
    nodes_with_untried = 0
    max_depth = 0
    while stack:
        node, depth = stack.pop()
        total_nodes += 1
        max_depth = max(max_depth, depth)
        children_count = len(node.children)
        total_edges += children_count
        if children_count == 0:
            leaf_nodes += 1
        if node.untried_actions:
            nodes_with_untried += 1
        for child in node.children:
            stack.append((child, depth + 1))

    avg_branching = (total_edges / total_nodes) if total_nodes else 0.0
    root_children_visits = [child.visits for child in root.children]
    root_visit_std = (
        statistics.pstdev(root_children_visits)
        if len(root_children_visits) > 1
        else 0.0
    )
    return {
        "nodes": total_nodes,
        "edges": total_edges,
        "leaves": leaf_nodes,
        "max_depth": max_depth,
        "avg_branching": avg_branching,
        "nodes_with_untried": nodes_with_untried,
        "root_children": len(root.children),
        "root_visits_total": sum(root_children_visits),
        "root_visit_std": root_visit_std,
    }


def _build_action_path(node):
    actions = []
    current = node
    while current is not None and current.action is not None:
        actions.append(format_action(current.action))
        current = current.parent
    actions.reverse()
    return actions


def get_tree_frontier_lines(root, top_k, max_depth):
    if top_k <= 0:
        return []

    frontier_nodes = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > 0:
            avg = (node.value / node.visits) if node.visits else 0.0
            frontier_nodes.append((node, depth, avg))
        if depth >= max_depth:
            continue
        for child in node.children:
            stack.append((child, depth + 1))

    ranked = sorted(
        frontier_nodes,
        key=lambda item: (item[0].visits, item[2]),
        reverse=True,
    )
    lines = []
    for index, (node, depth, avg) in enumerate(ranked[:top_k], start=1):
        path = " -> ".join(_build_action_path(node))
        lines.append(
            f"#{index} depth={depth} visits={node.visits} avg={avg:.4f} path={path}"
        )
    return lines


def select_scenario(name):
    scenarios = get_container_depot_scenarios()
    if name is None:
        return scenarios[0]
    for scenario in scenarios:
        if scenario["name"] == name:
            return scenario
    available = ", ".join(s["name"] for s in scenarios)
    raise ValueError(f"Unknown scenario '{name}'. Available: {available}")


def build_simulation(scenario):
    return Simulation(
        (0, 0),
        copy.deepcopy(scenario["board"]),
        0,
        manhattan_distance,
        list(scenario["pending"]),
    )


def run_visualizer(
    scenario,
    seed,
    agents,
    rollouts,
    max_steps,
    top_k,
    timeout_seconds,
    delay_seconds,
    interactive,
    enable_progressive_widening,
    exploration_constant,
    progressive_widening_c,
    progressive_widening_alpha,
    show_tree_stats,
    tree_frontier_k,
    tree_frontier_depth,
):
    agent_states = {}
    for index, agent_name in enumerate(agents):
        agent_seed = seed + (index * 101)
        simulation = build_simulation(scenario)
        state = {
            "name": agent_name,
            "simulation": simulation,
        }
        if agent_name == "mcts":
            state["player"] = MonteCarloPlayer(
                ContainerDepotMCTSAdapter(simulation, rng=random.Random(agent_seed)),
                rng=random.Random(agent_seed),
                enable_progressive_widening=enable_progressive_widening,
                exploration_constant=exploration_constant,
                progressive_widening_c=progressive_widening_c,
                progressive_widening_alpha=progressive_widening_alpha,
            )
        else:
            state["rng"] = random.Random(agent_seed)
        agent_states[agent_name] = state

    def all_agents_done():
        return all(
            state["simulation"].is_simulation_end() for state in agent_states.values()
        )

    def print_agent_boards():
        for agent_name in agents:
            simulation = agent_states[agent_name]["simulation"]
            print(f"\n{agent_name.upper()} Board")
            for line in board_to_lines(simulation):
                print(line)

    start = time.time()
    print("=== Container Depot Decision Visualizer ===")
    timeout_label = "disabled" if timeout_seconds <= 0 else f"{timeout_seconds}s"
    print(
        f"scenario={scenario['name']} seed={seed} agents={','.join(agents)} rollouts={rollouts} max_steps={max_steps} timeout={timeout_label}"
    )

    print("\n=== Initial State ===")
    for agent_name in agents:
        simulation = agent_states[agent_name]["simulation"]
        print(
            f"{agent_name.upper()} metrics: time={simulation.time}, epochs={simulation.epochs}, score={simulation.time + simulation.epochs}"
        )
    print_agent_boards()

    step = 0
    while step < max_steps:
        if timeout_seconds > 0 and (time.time() - start > timeout_seconds):
            print("\nStopped by timeout.")
            break

        if all_agents_done():
            break

        print(f"\n=== Step {step} ===")

        for agent_name in agents:
            state = agent_states[agent_name]
            simulation = state["simulation"]
            if simulation.is_simulation_end():
                print(f"{agent_name.upper()} action: {format_action(None)}")
                continue

            action = None
            mcts_node = None
            if agent_name == "mcts":
                player = state["player"]
                mcts_node = player.search_best_move(rollouts=rollouts)
                action = mcts_node.action if mcts_node is not None else None

                mcts_candidates = get_mcts_top_candidates(player, top_k)
                if mcts_candidates:
                    print("MCTS top candidates:")
                    for line in mcts_candidates:
                        print("  " + line)

                if show_tree_stats or tree_frontier_k > 0:
                    tree_root = player.action_tree
                    if show_tree_stats:
                        stats = get_tree_stats(tree_root)
                        print(
                            "MCTS tree stats: "
                            f"nodes={stats['nodes']} leaves={stats['leaves']} "
                            f"depth={stats['max_depth']} avg_branching={stats['avg_branching']:.2f} "
                            f"with_untried={stats['nodes_with_untried']} "
                            f"root_children={stats['root_children']} root_visits={stats['root_visits_total']} "
                            f"root_visit_std={stats['root_visit_std']:.2f}"
                        )

                    frontier_lines = get_tree_frontier_lines(
                        tree_root,
                        top_k=tree_frontier_k,
                        max_depth=tree_frontier_depth,
                    )
                    if frontier_lines:
                        print(
                            f"MCTS tree frontier (top {tree_frontier_k}, depth<={tree_frontier_depth}):"
                        )
                        for line in frontier_lines:
                            print("  " + line)

            elif agent_name == "greedy":
                rng = state["rng"]
                actions = simulation.get_possible_actions()
                action = choose_greedy_action(simulation, actions, rng)
            elif agent_name == "random":
                rng = state["rng"]
                actions = simulation.get_possible_actions()
                action = rng.choice(actions) if actions else None

            print(f"{agent_name.upper()} action: {format_action(action)}")
            if action is not None:
                previous_time = simulation.time
                simulation.execute_action(action)
                if agent_name == "mcts" and mcts_node is not None:
                    state["player"].execute_action_on_simulation(mcts_node)
                print(
                    f"{agent_name.upper()} metrics: time={simulation.time} (+{simulation.time - previous_time}), epochs={simulation.epochs}"
                )

        print_agent_boards()

        step += 1

        if interactive:
            input("Press Enter to continue...")
        elif delay_seconds > 0:
            time.sleep(delay_seconds)

    print("\n=== Final Summary ===")
    for agent_name in agents:
        simulation = agent_states[agent_name]["simulation"]
        print(
            f"{agent_name.upper()} solved={simulation.is_simulation_end()} score={simulation.time + simulation.epochs} time={simulation.time} epochs={simulation.epochs}"
        )


def main():
    parser = argparse.ArgumentParser(description="Visualize Container Depot agents step by step")
    parser.add_argument("--scenario", type=str, default="small_easy")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rollouts", type=int, default=25)
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=0.0,
        help="Set <= 0 to disable timeout",
    )
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument(
        "--agents",
        type=str,
        default="mcts,greedy",
        help="Comma-separated list: mcts,greedy,random",
    )
    parser.add_argument(
        "--enable-progressive-widening",
        action="store_true",
        help="Enable progressive widening in tree expansion",
    )
    parser.add_argument(
        "--exploration-constant",
        type=float,
        default=0.2,
        help="UCT exploration constant for MCTS",
    )
    parser.add_argument(
        "--progressive-widening-c",
        type=float,
        default=0.3,
        help="Progressive widening coefficient",
    )
    parser.add_argument(
        "--progressive-widening-alpha",
        type=float,
        default=0.5,
        help="Progressive widening exponent",
    )
    parser.add_argument(
        "--show-tree-stats",
        action="store_true",
        help="Print aggregate MCTS tree stats at each decision step",
    )
    parser.add_argument(
        "--tree-frontier-k",
        type=int,
        default=0,
        help="Show top-K most visited nodes in the tree frontier (0 disables)",
    )
    parser.add_argument(
        "--tree-frontier-depth",
        type=int,
        default=3,
        help="Maximum depth for tree frontier reporting",
    )
    args = parser.parse_args()

    parsed_agents = [part.strip().lower() for part in args.agents.split(",") if part.strip()]
    if not parsed_agents:
        raise ValueError("--agents must include at least one policy")
    supported_agents = {"mcts", "greedy", "random"}
    unsupported_agents = [name for name in parsed_agents if name not in supported_agents]
    if unsupported_agents:
        raise ValueError(
            f"Unsupported agents: {', '.join(unsupported_agents)}. Supported: mcts,greedy,random"
        )

    scenario = select_scenario(args.scenario)
    run_visualizer(
        scenario=scenario,
        seed=args.seed,
        agents=parsed_agents,
        rollouts=args.rollouts,
        max_steps=min(args.max_steps, scenario["max_steps"]),
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
        delay_seconds=args.delay_seconds,
        interactive=args.interactive,
        enable_progressive_widening=args.enable_progressive_widening,
        exploration_constant=args.exploration_constant,
        progressive_widening_c=args.progressive_widening_c,
        progressive_widening_alpha=args.progressive_widening_alpha,
        show_tree_stats=args.show_tree_stats,
        tree_frontier_k=args.tree_frontier_k,
        tree_frontier_depth=max(1, args.tree_frontier_depth),
    )


if __name__ == "__main__":
    main()
