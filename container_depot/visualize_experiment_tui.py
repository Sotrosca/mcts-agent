import argparse
import copy
import pickle
import random
from pathlib import Path

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
        session_file,
    ):
        self.scenario = scenario
        self.seed = seed
        self.rollouts = rollouts
        self.max_steps = max_steps
        self.top_k = top_k
        self.frontier_k = frontier_k
        self.frontier_depth = frontier_depth
        self.agents = agents
        self.session_file = session_file
        self.step = 0
        self.done = False
        self.last_actions = {agent_name: None for agent_name in agents}
        self.last_tree_stats = None
        self.last_frontier_lines = []
        self.mcts_agent_name = next((name for name in agents if name == "mcts"), None)
        self.mcts_navigation_root = None
        self.selected_node_path_ids = []
        self.selected_child_index = 0
        self.history = []

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

        self._push_snapshot()

    def save_to_file(self):
        payload = {
            "scenario_name": self.scenario["name"],
            "seed": self.seed,
            "rollouts": self.rollouts,
            "max_steps": self.max_steps,
            "top_k": self.top_k,
            "frontier_k": self.frontier_k,
            "frontier_depth": self.frontier_depth,
            "agents": list(self.agents),
            "history": self.history,
        }
        session_path = Path(self.session_file)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with session_path.open("wb") as handle:
            pickle.dump(payload, handle)

    def load_from_file(self):
        session_path = Path(self.session_file)
        if not session_path.exists():
            return False

        with session_path.open("rb") as handle:
            payload = pickle.load(handle)

        expected_agents = list(self.agents)
        if payload.get("scenario_name") != self.scenario["name"]:
            return False
        if payload.get("agents") != expected_agents:
            return False

        history = payload.get("history")
        if not history:
            return False

        self.history = history
        self._restore_snapshot(self.history[-1])
        return True

    def _capture_snapshot(self):
        return {
            "step": self.step,
            "done": self.done,
            "last_actions": copy.deepcopy(self.last_actions),
            "last_tree_stats": copy.deepcopy(self.last_tree_stats),
            "last_frontier_lines": copy.deepcopy(self.last_frontier_lines),
            "selected_node_path_ids": list(self.selected_node_path_ids),
            "selected_child_index": self.selected_child_index,
            "mcts_navigation_root": copy.deepcopy(self.mcts_navigation_root),
            "agent_states": copy.deepcopy(self.agent_states),
        }

    def _restore_snapshot(self, snapshot):
        self.step = snapshot["step"]
        self.done = snapshot["done"]
        self.last_actions = copy.deepcopy(snapshot["last_actions"])
        self.last_tree_stats = copy.deepcopy(snapshot["last_tree_stats"])
        self.last_frontier_lines = copy.deepcopy(snapshot["last_frontier_lines"])
        self.selected_node_path_ids = list(snapshot["selected_node_path_ids"])
        self.selected_child_index = snapshot["selected_child_index"]
        self.mcts_navigation_root = copy.deepcopy(snapshot["mcts_navigation_root"])
        self.agent_states = copy.deepcopy(snapshot["agent_states"])

    def _push_snapshot(self):
        self.history.append(self._capture_snapshot())

    def back_one_step(self):
        if len(self.history) <= 1:
            return False
        self.history.pop()
        self._restore_snapshot(self.history[-1])
        return True

    def _get_mcts_root(self):
        if self.mcts_agent_name is None:
            return None
        if self.mcts_navigation_root is not None:
            return self.mcts_navigation_root
        return self.agent_states[self.mcts_agent_name]["player"].action_tree

    def get_selected_node(self):
        root = self._get_mcts_root()
        if root is None:
            return None

        node = root
        normalized_path = []
        for node_id in self.selected_node_path_ids:
            match = next((child for child in node.children if child.id == node_id), None)
            if match is None:
                break
            normalized_path.append(node_id)
            node = match

        if normalized_path != self.selected_node_path_ids:
            self.selected_node_path_ids = normalized_path

        return node

    def get_selected_node_children(self):
        node = self.get_selected_node()
        if node is None:
            return []
        return sorted(
            node.children,
            key=lambda child: (
                child.visits,
                (child.value / child.visits) if child.visits else 0.0,
            ),
            reverse=True,
        )

    def move_child_selection(self, delta):
        children = self.get_selected_node_children()
        if not children:
            self.selected_child_index = 0
            return
        self.selected_child_index = max(
            0,
            min(len(children) - 1, self.selected_child_index + delta),
        )

    def descend_selected_child(self):
        children = self.get_selected_node_children()
        if not children:
            return False
        selected_child = children[self.selected_child_index]
        self.selected_node_path_ids.append(selected_child.id)
        self.selected_child_index = 0
        return True

    def ascend_to_parent(self):
        if not self.selected_node_path_ids:
            return False
        self.selected_node_path_ids.pop()
        self.selected_child_index = 0
        return True

    def reset_tree_cursor(self):
        self.selected_node_path_ids = []
        self.selected_child_index = 0

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
                self.mcts_navigation_root = player.action_tree
                action = mcts_node.action if mcts_node is not None else None
                self.last_actions[agent_name] = action
                if action is not None:
                    simulation.execute_action(action)
                    if mcts_node is not None:
                        player.execute_action_on_simulation(mcts_node)

                tree_root = self.mcts_navigation_root or player.action_tree
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
        self.reset_tree_cursor()
        self._push_snapshot()


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
    #top { height: 11; }
    #content { height: 1fr; }
    #boards { width: 2fr; }
    #tables { width: 2fr; }
    #board_agents { border: solid gray; height: 1fr; }
    #node_panel { height: 7; border: solid gray; }
    #candidates, #frontier { height: 1fr; border: solid gray; }
    """

    BINDINGS = [
        ("n", "next_step", "Next step"),
        ("b", "back_step", "Back step"),
        ("f", "run_five", "Run 5 steps"),
        ("e", "run_to_end", "Run to end"),
        ("s", "save_session", "Save session"),
        ("l", "load_session", "Load session"),
        ("j", "cursor_down", "Child down"),
        ("k", "cursor_up", "Child up"),
        ("enter", "enter_child", "Enter child"),
        ("d", "enter_child", "Descend child"),
        ("u", "go_parent", "Go parent"),
        ("r", "go_root", "Go root"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, session_state: SessionState):
        super().__init__()
        self.state = session_state
        self.status_message = ""

    def _persist(self):
        try:
            self.state.save_to_file()
            self.status_message = f"session saved: {self.state.session_file}"
        except Exception as exc:
            self.status_message = f"save failed: {exc}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="top")
        with Horizontal(id="content"):
            with Vertical(id="boards"):
                yield Static(id="board_agents")
            with Vertical(id="tables"):
                yield Static(id="node_panel")
                yield DataTable(id="candidates")
                yield DataTable(id="frontier")
        yield Footer()

    def on_mount(self) -> None:
        candidates = self.query_one("#candidates", DataTable)
        candidates.add_columns("Sel", "#", "NodeId", "Action", "Visits", "Value", "Avg")
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
                    f"status={self.status_message or 'ready'}",
                ]
            )
        )

        board_agents = self.query_one("#board_agents", Static)
        board_sections = []
        for agent_name in self.state.agents:
            simulation = self.state.agent_states[agent_name]["simulation"]
            board_sections.extend([f"{agent_name.upper()} Board", *board_to_lines(simulation), ""])
        board_agents.update("\n".join(board_sections).strip())

        node_panel = self.query_one("#node_panel", Static)
        selected_node = self.state.get_selected_node()
        if selected_node is None:
            node_panel.update("Node Inspector\nMCTS agent not selected")
        else:
            node_avg = (
                selected_node.value / selected_node.visits if selected_node.visits else 0.0
            )
            node_panel.update(
                "\n".join(
                    [
                        "Node Inspector",
                        f"selected_node_id={selected_node.id} depth={selected_node.level} children={len(selected_node.children)}",
                        f"action={format_action(selected_node.action)}",
                        f"visits={selected_node.visits} value={selected_node.value:.4f} avg={node_avg:.4f}",
                        f"untried_actions={len(selected_node.untried_actions)}",
                        f"path={' -> '.join(_build_action_path(selected_node)) if selected_node.action is not None else 'ROOT'}",
                    ]
                )
            )

        candidates = self.query_one("#candidates", DataTable)
        candidates.clear()
        if self.state.mcts_agent_name is None:
            candidates.add_row("", "-", "-", "No MCTS agent selected", "0", "0.0000", "0.0000")
        else:
            all_children = self.state.get_selected_node_children()
            total_children = len(all_children)
            if not all_children:
                candidates.add_row("", "-", "-", "No child nodes", "0", "0.0000", "0.0000")
            else:
                selected_index = self.state.selected_child_index
                window_size = max(1, self.state.top_k)
                half_window = window_size // 2
                start = max(0, selected_index - half_window)
                end = min(total_children, start + window_size)
                start = max(0, end - window_size)

                visible_children = all_children[start:end]
                for absolute_index, child in enumerate(visible_children, start=start):
                    row_index = absolute_index + 1
                    avg = (child.value / child.visits) if child.visits else 0.0
                    marker = ">" if absolute_index == selected_index else ""
                    candidates.add_row(
                        marker,
                        str(row_index),
                        str(child.id),
                        format_action(child.action),
                        str(child.visits),
                        f"{child.value:.4f}",
                        f"{avg:.4f}",
                    )

                self.status_message = (
                    f"selected child {selected_index + 1}/{total_children}"
                )

        frontier = self.query_one("#frontier", DataTable)
        frontier.clear()
        if not self.state.last_frontier_lines:
            frontier.add_row("-", "-", "0", "0.0000", "No frontier nodes yet")
        for index, depth, visits, avg, path in self.state.last_frontier_lines:
            frontier.add_row(str(index), str(depth), str(visits), f"{avg:.4f}", path)

    def action_next_step(self) -> None:
        self.state.run_one_step()
        self._persist()
        self._refresh_view()

    def action_back_step(self) -> None:
        if self.state.back_one_step():
            self._persist()
            self.status_message = f"back to step={self.state.step}"
        else:
            self.status_message = "already at first snapshot"
        self._refresh_view()

    def action_run_five(self) -> None:
        for _ in range(5):
            if self.state.done:
                break
            self.state.run_one_step()
        self._persist()
        self._refresh_view()

    def action_run_to_end(self) -> None:
        while not self.state.done:
            self.state.run_one_step()
        self._persist()
        self._refresh_view()

    def action_save_session(self) -> None:
        self._persist()
        self._refresh_view()

    def action_load_session(self) -> None:
        try:
            if self.state.load_from_file():
                self.status_message = f"session loaded: {self.state.session_file}"
            else:
                self.status_message = "no compatible session to load"
        except Exception as exc:
            self.status_message = f"load failed: {exc}"
        self._refresh_view()

    def action_cursor_down(self) -> None:
        self.state.move_child_selection(1)
        children = self.state.get_selected_node_children()
        if children:
            self.status_message = (
                f"selected child {self.state.selected_child_index + 1}/{len(children)}"
            )
        else:
            self.status_message = "no child nodes to select"
        self._refresh_view()

    def action_cursor_up(self) -> None:
        self.state.move_child_selection(-1)
        children = self.state.get_selected_node_children()
        if children:
            self.status_message = (
                f"selected child {self.state.selected_child_index + 1}/{len(children)}"
            )
        else:
            self.status_message = "no child nodes to select"
        self._refresh_view()

    def action_enter_child(self) -> None:
        if self.state.descend_selected_child():
            selected = self.state.get_selected_node()
            self.status_message = (
                f"entered node id={selected.id}" if selected is not None else "entered child"
            )
        else:
            self.status_message = "cannot enter: selected node has no children"
        self._refresh_view()

    def action_go_parent(self) -> None:
        if self.state.ascend_to_parent():
            selected = self.state.get_selected_node()
            self.status_message = (
                f"up to node id={selected.id}" if selected is not None else "up to parent"
            )
        else:
            self.status_message = "already at root"
        self._refresh_view()

    def action_go_root(self) -> None:
        self.state.reset_tree_cursor()
        selected = self.state.get_selected_node()
        self.status_message = (
            f"cursor reset to root id={selected.id}" if selected is not None else "cursor reset"
        )
        self._refresh_view()

    def action_quit(self) -> None:
        self._persist()
        self.exit()


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
    parser.add_argument(
        "--session-file",
        type=str,
        default=".container_depot_tui_session.pkl",
        help="Path for persisted TUI session",
    )
    parser.add_argument(
        "--no-resume-session",
        action="store_true",
        help="Do not auto-load existing session file on startup",
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
        session_file=args.session_file,
    )

    if not args.no_resume_session:
        try:
            session_state.load_from_file()
        except Exception:
            pass
    try:
        session_state.save_to_file()
    except Exception:
        pass

    app = ContainerDepotTUI(session_state)
    app.run()


if __name__ == "__main__":
    main()