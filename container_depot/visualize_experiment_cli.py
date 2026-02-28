import argparse
import copy
import random
import statistics
import time

from container_depot.benchmark_agent_quality import choose_greedy_action
from container_depot.container_depot_simulation import Simulation
from container_depot.example_mcts_functions import ContainerDepotMCTSAdapter
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
    mcts_sim = build_simulation(scenario)
    greedy_sim = build_simulation(scenario)

    mcts_player = MonteCarloPlayer(
        ContainerDepotMCTSAdapter(mcts_sim, rng=random.Random(seed)),
        rng=random.Random(seed),
        enable_progressive_widening=enable_progressive_widening,
        exploration_constant=exploration_constant,
        progressive_widening_c=progressive_widening_c,
        progressive_widening_alpha=progressive_widening_alpha,
    )
    greedy_rng = random.Random(seed)

    start = time.time()
    print("=== Container Depot Decision Visualizer ===")
    timeout_label = "disabled" if timeout_seconds <= 0 else f"{timeout_seconds}s"
    print(
        f"scenario={scenario['name']} seed={seed} rollouts={rollouts} max_steps={max_steps} timeout={timeout_label}"
    )

    print("\n=== Initial State ===")
    print(
        f"MCTS metrics: time={mcts_sim.time}, epochs={mcts_sim.epochs}, score={mcts_sim.time + mcts_sim.epochs}"
    )
    print(
        f"Greedy metrics: time={greedy_sim.time}, epochs={greedy_sim.epochs}, score={greedy_sim.time + greedy_sim.epochs}"
    )
    print_side_by_side(
        "MCTS Board",
        board_to_lines(mcts_sim),
        "Greedy Board",
        board_to_lines(greedy_sim),
    )

    step = 0
    while step < max_steps:
        if timeout_seconds > 0 and (time.time() - start > timeout_seconds):
            print("\nStopped by timeout.")
            break

        mcts_done = mcts_sim.is_simulation_end()
        greedy_done = greedy_sim.is_simulation_end()
        if mcts_done and greedy_done:
            break

        print(f"\n=== Step {step} ===")

        mcts_action = None
        mcts_candidates = []
        if not mcts_done:
            mcts_node = mcts_player.search_best_move(rollouts=rollouts)
            mcts_action = mcts_node.action if mcts_node is not None else None
            mcts_candidates = get_mcts_top_candidates(mcts_player, top_k)
        else:
            mcts_node = None

        greedy_action = None
        if not greedy_done:
            greedy_actions = greedy_sim.get_possible_actions()
            greedy_action = choose_greedy_action(greedy_sim, greedy_actions, greedy_rng)

        print(f"MCTS action:   {format_action(mcts_action)}")
        print(f"Greedy action: {format_action(greedy_action)}")

        if mcts_candidates:
            print("MCTS top candidates:")
            for line in mcts_candidates:
                print("  " + line)

        if not mcts_done and (show_tree_stats or tree_frontier_k > 0):
            tree_root = mcts_player.action_tree
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

        if mcts_action is not None and not mcts_done:
            previous_time = mcts_sim.time
            mcts_sim.execute_action(mcts_action)
            if mcts_node is not None:
                mcts_player.execute_action_on_simulation(mcts_node)
            print(
                f"MCTS metrics: time={mcts_sim.time} (+{mcts_sim.time - previous_time}), epochs={mcts_sim.epochs}"
            )

        if greedy_action is not None and not greedy_done:
            previous_time = greedy_sim.time
            greedy_sim.execute_action(greedy_action)
            print(
                f"Greedy metrics: time={greedy_sim.time} (+{greedy_sim.time - previous_time}), epochs={greedy_sim.epochs}"
            )

        print_side_by_side(
            "MCTS Board",
            board_to_lines(mcts_sim),
            "Greedy Board",
            board_to_lines(greedy_sim),
        )

        step += 1

        if interactive:
            input("Press Enter to continue...")
        elif delay_seconds > 0:
            time.sleep(delay_seconds)

    print("\n=== Final Summary ===")
    print(
        f"MCTS solved={mcts_sim.is_simulation_end()} score={mcts_sim.time + mcts_sim.epochs} time={mcts_sim.time} epochs={mcts_sim.epochs}"
    )
    print(
        f"Greedy solved={greedy_sim.is_simulation_end()} score={greedy_sim.time + greedy_sim.epochs} time={greedy_sim.time} epochs={greedy_sim.epochs}"
    )


def main():
    parser = argparse.ArgumentParser(description="Visualize MCTS vs Greedy decisions step by step")
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

    scenario = select_scenario(args.scenario)
    run_visualizer(
        scenario=scenario,
        seed=args.seed,
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
