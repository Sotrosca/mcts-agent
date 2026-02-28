import argparse
import random

from container_depot.benchmark_agent_quality import choose_greedy_action
from container_depot.agent import ContainerDepotMCTSAdapter
from container_depot.visualize_experiment_cli import (
    board_to_lines,
    build_simulation,
    format_action,
    get_mcts_top_candidates,
    get_tree_frontier_lines,
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
    ):
        self.scenario = scenario
        self.seed = seed
        self.rollouts = rollouts
        self.max_steps = max_steps
        self.top_k = top_k
        self.frontier_k = frontier_k
        self.frontier_depth = frontier_depth
        self.step = 0
        self.done = False
        self.last_mcts_action = None
        self.last_greedy_action = None
        self.last_tree_stats = None
        self.last_frontier_lines = []

        self.mcts_sim = build_simulation(scenario)
        self.greedy_sim = build_simulation(scenario)
        self.mcts_player = MonteCarloPlayer(
            ContainerDepotMCTSAdapter(self.mcts_sim, rng=random.Random(seed)),
            rng=random.Random(seed),
            enable_progressive_widening=enable_progressive_widening,
            exploration_constant=exploration_constant,
            progressive_widening_c=progressive_widening_c,
            progressive_widening_alpha=progressive_widening_alpha,
        )
        self.greedy_rng = random.Random(seed)

    def run_one_step(self):
        if self.done or self.step >= self.max_steps:
            self.done = True
            return

        mcts_done = self.mcts_sim.is_simulation_end()
        greedy_done = self.greedy_sim.is_simulation_end()
        if mcts_done and greedy_done:
            self.done = True
            return

        mcts_node = None
        if not mcts_done:
            mcts_node = self.mcts_player.search_best_move(rollouts=self.rollouts)
            self.last_mcts_action = mcts_node.action if mcts_node is not None else None
            tree_root = self.mcts_player.action_tree
            self.last_tree_stats = get_tree_stats(tree_root)
            self.last_frontier_lines = get_tree_frontier_lines(
                tree_root,
                top_k=self.frontier_k,
                max_depth=self.frontier_depth,
            )
        else:
            self.last_mcts_action = None

        if not greedy_done:
            greedy_actions = self.greedy_sim.get_possible_actions()
            self.last_greedy_action = choose_greedy_action(
                self.greedy_sim,
                greedy_actions,
                self.greedy_rng,
            )
        else:
            self.last_greedy_action = None

        if self.last_mcts_action is not None and not mcts_done:
            self.mcts_sim.execute_action(self.last_mcts_action)
            if mcts_node is not None:
                self.mcts_player.execute_action_on_simulation(mcts_node)

        if self.last_greedy_action is not None and not greedy_done:
            self.greedy_sim.execute_action(self.last_greedy_action)

        self.step += 1
        if self.step >= self.max_steps:
            self.done = True


class ContainerDepotTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #top { height: 7; }
    #content { height: 1fr; }
    #boards { width: 2fr; }
    #tables { width: 2fr; }
    #board_mcts, #board_greedy { border: solid gray; height: 1fr; }
    #candidates, #frontier { height: 1fr; border: solid gray; }
    """

    BINDINGS = [
        ("n", "next_step", "Next step"),
        ("f", "run_five", "Run 5 steps"),
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
                yield Static(id="board_mcts")
                yield Static(id="board_greedy")
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
        tree_summary = "tree=n/a"
        if tree:
            tree_summary = (
                f"nodes={tree['nodes']} leaves={tree['leaves']} depth={tree['max_depth']} "
                f"branch={tree['avg_branching']:.2f} root_std={tree['root_visit_std']:.2f}"
            )
        top.update(
            "\n".join(
                [
                    "Container Depot MCTS Interactive Visualizer",
                    f"scenario={self.state.scenario['name']} step={self.state.step}/{self.state.max_steps} rollouts={self.state.rollouts}",
                    f"last_mcts={format_action(self.state.last_mcts_action)} | last_greedy={format_action(self.state.last_greedy_action)}",
                    f"MCTS score={self.state.mcts_sim.time + self.state.mcts_sim.epochs} (t={self.state.mcts_sim.time}, e={self.state.mcts_sim.epochs})",
                    f"Greedy score={self.state.greedy_sim.time + self.state.greedy_sim.epochs} (t={self.state.greedy_sim.time}, e={self.state.greedy_sim.epochs})",
                    f"{tree_summary}",
                ]
            )
        )

        board_mcts = self.query_one("#board_mcts", Static)
        board_mcts.update("MCTS Board\n" + "\n".join(board_to_lines(self.state.mcts_sim)))
        board_greedy = self.query_one("#board_greedy", Static)
        board_greedy.update(
            "Greedy Board\n" + "\n".join(board_to_lines(self.state.greedy_sim))
        )

        candidates = self.query_one("#candidates", DataTable)
        candidates.clear()
        lines = get_mcts_top_candidates(self.state.mcts_player, self.state.top_k)
        for line in lines:
            parts = line.split(" ")
            index = parts[0].replace("#", "")
            visits = next((p.split("=")[1] for p in parts if p.startswith("visits=")), "0")
            value = next((p.split("=")[1] for p in parts if p.startswith("value=")), "0")
            avg = next((p.split("=")[1] for p in parts if p.startswith("avg=")), "0")
            action = line[line.find(" ") + 1 : line.find(" visits=")]
            candidates.add_row(index, action, visits, value, avg)

        frontier = self.query_one("#frontier", DataTable)
        frontier.clear()
        for line in self.state.last_frontier_lines:
            prefix, path = line.split(" path=", 1)
            index = prefix.split(" ")[0].replace("#", "")
            depth = next(
                (segment.split("=")[1] for segment in prefix.split(" ") if segment.startswith("depth=")),
                "0",
            )
            visits = next(
                (segment.split("=")[1] for segment in prefix.split(" ") if segment.startswith("visits=")),
                "0",
            )
            avg = next(
                (segment.split("=")[1] for segment in prefix.split(" ") if segment.startswith("avg=")),
                "0",
            )
            frontier.add_row(index, depth, visits, avg, path)

    def action_next_step(self) -> None:
        self.state.run_one_step()
        self._refresh_view()

    def action_run_five(self) -> None:
        for _ in range(5):
            if self.state.done:
                break
            self.state.run_one_step()
        self._refresh_view()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive TUI visualizer for Container Depot MCTS"
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
    args = parser.parse_args()

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
    )

    app = ContainerDepotTUI(session_state)
    app.run()


if __name__ == "__main__":
    main()