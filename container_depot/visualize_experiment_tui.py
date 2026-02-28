import argparse
import random

from container_depot.benchmark_agent_quality import choose_greedy_action
from container_depot.agent import ContainerDepotMCTSAdapter
from container_depot.visualize_experiment_cli import (
    board_to_lines,
    build_simulation,
    format_action,
    get_tree_stats,
    select_scenario,
)
from mcts_agent.core import MonteCarloPlayer

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import DataTable, Footer, Header, Static
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'textual'. Install with: pip install textual"
    ) from exc


class SessionState:
    def __init__(
        self,
        scenario,
        seed,
        rollouts,
        max_steps,
        top_k,
        enable_progressive_widening,
        exploration_constant,
        progressive_widening_c,
        progressive_widening_alpha,
        frontier_k,
        frontier_depth,
        agents,
    ):
        self.scenario = scenario
        self.seed = seed
        self.rollouts = rollouts
        self.max_steps = max_steps
        self.top_k = top_k
        self.frontier_k = frontier_k
        self.frontier_depth = frontier_depth
        self.agents = agents
        self.step = 0
        self.done = False
        self.last_actions = {agent_name: None for agent_name in agents}
        self.last_tree_stats = None
        self.last_frontier_lines = []
        self.mcts_agent_name = next((name for name in agents if name == "mcts"), None)

        self.agent_states = {}
        for index, agent_name in enumerate(agents):
            agent_seed = seed + (index * 101)
            simulation = build_simulation(scenario)
            agent_state = {
                "name": agent_name,
                "simulation": simulation,
            }
            if agent_name == "mcts":
                agent_state["player"] = MonteCarloPlayer(
                    ContainerDepotMCTSAdapter(simulation, rng=random.Random(agent_seed)),
                    rng=random.Random(agent_seed),
                    enable_progressive_widening=enable_progressive_widening,
                    exploration_constant=exploration_constant,
                    progressive_widening_c=progressive_widening_c,
                    progressive_widening_alpha=progressive_widening_alpha,
                )
            else:
                agent_state["rng"] = random.Random(agent_seed)
            self.agent_states[agent_name] = agent_state

    def _all_agents_done(self):
        return all(
            agent_state["simulation"].is_simulation_end()
            for agent_state in self.agent_states.values()
        )

    def run_one_step(self):
        if self.done or self.step >= self.max_steps:
            self.done = True
            return

        if self._all_agents_done():
            self.done = True
            return

        for agent_name in self.agents:
            agent_state = self.agent_states[agent_name]
            simulation = agent_state["simulation"]
            if simulation.is_simulation_end():
                self.last_actions[agent_name] = None
                continue

            if agent_name == "mcts":
                player = agent_state["player"]
                mcts_node = player.search_best_move(rollouts=self.rollouts)
                action = mcts_node.action if mcts_node is not None else None
                self.last_actions[agent_name] = action
                if action is not None:
                    simulation.execute_action(action)
                    if mcts_node is not None:
                        player.execute_action_on_simulation(mcts_node)

                tree_root = player.action_tree
                self.last_tree_stats = get_tree_stats(tree_root)
                self.last_frontier_lines = _get_tree_frontier_rows(
                    tree_root,
                    top_k=self.frontier_k,
                    max_depth=self.frontier_depth,
                )
            elif agent_name == "greedy":
                rng = agent_state["rng"]
                actions = simulation.get_possible_actions()
                action = choose_greedy_action(simulation, actions, rng)
                self.last_actions[agent_name] = action
                if action is not None:
                    simulation.execute_action(action)
            elif agent_name == "random":
                rng = agent_state["rng"]
                actions = simulation.get_possible_actions()
                action = rng.choice(actions) if actions else None
                self.last_actions[agent_name] = action
                if action is not None:
                    simulation.execute_action(action)

        self.step += 1
        if self.step >= self.max_steps or self._all_agents_done():
            self.done = True


def _build_action_path(node):
    actions = []
    current = node
    while current is not None and current.action is not None:
        actions.append(format_action(current.action))
        current = current.parent
    actions.reverse()
    return actions


def _get_candidate_rows(player, top_k):
    children = player.action_tree.children
    ranked = sorted(
        children,
        key=lambda child: (
            child.visits,
            (child.value / child.visits) if child.visits else 0.0,
        ),
        reverse=True,
    )

    rows = []
    for index, child in enumerate(ranked[:top_k], start=1):
        avg = (child.value / child.visits) if child.visits else 0.0
        rows.append((index, format_action(child.action), child.visits, child.value, avg))
    return rows


def _get_tree_frontier_rows(root, top_k, max_depth):
    if top_k <= 0:
        return []

    frontier_nodes = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > 0:
            avg = (node.value / node.visits) if node.visits else 0.0
            path = " -> ".join(_build_action_path(node))
            frontier_nodes.append((node.visits, avg, depth, path))
        if depth >= max_depth:
            continue
        for child in node.children:
            stack.append((child, depth + 1))

    ranked = sorted(frontier_nodes, key=lambda item: (item[0], item[1]), reverse=True)
    rows = []
    for index, (visits, avg, depth, path) in enumerate(ranked[:top_k], start=1):
        rows.append((index, depth, visits, avg, path))
    return rows


class ContainerDepotTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #top { height: 10; }
    #content { height: 1fr; }
    #boards { width: 2fr; }
    #tables { width: 2fr; }
    #board_agents { border: solid gray; height: 1fr; }
    #candidates, #frontier { height: 1fr; border: solid gray; }
    """

    BINDINGS = [
        ("n", "next_step", "Next step"),
        ("f", "run_five", "Run 5 steps"),
        ("e", "run_to_end", "Run to end"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, session_state: SessionState):
        super().__init__()
        self.state = session_state

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="top")
        with Horizontal(id="content"):
            with Vertical(id="boards"):
                yield Static(id="board_agents")
            with Vertical(id="tables"):
                yield DataTable(id="candidates")
                yield DataTable(id="frontier")
        yield Footer()

    def on_mount(self) -> None:
        candidates = self.query_one("#candidates", DataTable)
        candidates.add_columns("#", "Action", "Visits", "Value", "Avg")
        frontier = self.query_one("#frontier", DataTable)
        frontier.add_columns("#", "Depth", "Visits", "Avg", "Path")
        self._refresh_view()

    def _refresh_view(self) -> None:
        top = self.query_one("#top", Static)
        tree = self.state.last_tree_stats
        tree_summary = "mcts_tree=n/a"
        if tree:
            tree_summary = (
                f"nodes={tree['nodes']} leaves={tree['leaves']} depth={tree['max_depth']} "
                f"branch={tree['avg_branching']:.2f} root_std={tree['root_visit_std']:.2f}"
            )

        action_summary = " | ".join(
            f"{agent}={format_action(self.state.last_actions.get(agent))}"
            for agent in self.state.agents
        )

        score_summary = " | ".join(
            (
                f"{agent}: score="
                f"{self.state.agent_states[agent]['simulation'].time + self.state.agent_states[agent]['simulation'].epochs} "
                f"(t={self.state.agent_states[agent]['simulation'].time}, "
                f"e={self.state.agent_states[agent]['simulation'].epochs}, "
                f"solved={self.state.agent_states[agent]['simulation'].is_simulation_end()})"
            )
            for agent in self.state.agents
        )

        top.update(
            "\n".join(
                [
                    "Container Depot Interactive Visualizer",
                    f"scenario={self.state.scenario['name']} step={self.state.step}/{self.state.max_steps} rollouts={self.state.rollouts} done={self.state.done}",
                    f"agents={','.join(self.state.agents)}",
                    f"last_actions: {action_summary}",
                    score_summary,
                    f"{tree_summary}",
                ]
            )
        )

        board_agents = self.query_one("#board_agents", Static)
        board_sections = []
        for agent_name in self.state.agents:
            simulation = self.state.agent_states[agent_name]["simulation"]
            board_sections.extend([f"{agent_name.upper()} Board", *board_to_lines(simulation), ""])
        board_agents.update("\n".join(board_sections).strip())

        candidates = self.query_one("#candidates", DataTable)
        candidates.clear()
        if self.state.mcts_agent_name is None:
            candidates.add_row("-", "No MCTS agent selected", "0", "0.0000", "0.0000")
        else:
            mcts_player = self.state.agent_states[self.state.mcts_agent_name]["player"]
            rows = _get_candidate_rows(mcts_player, self.state.top_k)
            if not rows:
                candidates.add_row("-", "No candidates yet", "0", "0.0000", "0.0000")
            for index, action, visits, value, avg in rows:
                candidates.add_row(
                    str(index),
                    action,
                    str(visits),
                    f"{value:.4f}",
                    f"{avg:.4f}",
                )

        frontier = self.query_one("#frontier", DataTable)
        frontier.clear()
        if not self.state.last_frontier_lines:
            frontier.add_row("-", "-", "0", "0.0000", "No frontier nodes yet")
        for index, depth, visits, avg, path in self.state.last_frontier_lines:
            frontier.add_row(str(index), str(depth), str(visits), f"{avg:.4f}", path)

    def action_next_step(self) -> None:
        self.state.run_one_step()
        self._refresh_view()

    def action_run_five(self) -> None:
        for _ in range(5):
            if self.state.done:
                break
            self.state.run_one_step()
        self._refresh_view()

    def action_run_to_end(self) -> None:
        while not self.state.done:
            self.state.run_one_step()
        self._refresh_view()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive TUI visualizer for Container Depot agents"
    )
    parser.add_argument("--scenario", type=str, default="very_hard_stacked_3x3")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rollouts", type=int, default=300)
    parser.add_argument("--max-steps", type=int, default=40)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--tree-frontier-k", type=int, default=10)
    parser.add_argument("--tree-frontier-depth", type=int, default=4)
    parser.add_argument("--enable-progressive-widening", action="store_true")
    parser.add_argument("--exploration-constant", type=float, default=0.2)
    parser.add_argument("--progressive-widening-c", type=float, default=0.3)
    parser.add_argument("--progressive-widening-alpha", type=float, default=0.5)
    parser.add_argument(
        "--agents",
        type=str,
        default="mcts",
        help="Comma-separated list: mcts,greedy,random",
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
    session_state = SessionState(
        scenario=scenario,
        seed=args.seed,
        rollouts=args.rollouts,
        max_steps=min(args.max_steps, scenario["max_steps"]),
        top_k=max(1, args.top_k),
        enable_progressive_widening=args.enable_progressive_widening,
        exploration_constant=args.exploration_constant,
        progressive_widening_c=args.progressive_widening_c,
        progressive_widening_alpha=args.progressive_widening_alpha,
        frontier_k=max(0, args.tree_frontier_k),
        frontier_depth=max(1, args.tree_frontier_depth),
        agents=parsed_agents,
    )

    app = ContainerDepotTUI(session_state)
    app.run()


if __name__ == "__main__":
    main()