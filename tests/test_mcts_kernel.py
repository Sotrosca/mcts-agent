import random

from mcts_agent.core import MCTSAdapter, MonteCarloPlayer


class SimpleBanditAdapter(MCTSAdapter):
    """
    Root has two actions:
    - good -> reward 1.0
    - bad -> reward 0.0
    """

    def get_initial_state(self):
        return {"depth": 0, "root_player": 0}

    def clone_state(self, state):
        return dict(state)

    def get_possible_actions(self, state):
        if state["depth"] == 0:
            return ["good", "bad"]
        return []

    def apply_action(self, state, action):
        return {"depth": 1, "root_player": state["root_player"], "action": action}

    def is_terminal(self, state):
        return state.get("depth", 0) >= 1

    def get_player_turn(self, state):
        return state["root_player"]

    def rollout(self, state, root_player, rng):
        return 1.0 if state.get("action") == "good" else 0.0


class ChainAdapter(MCTSAdapter):
    """
    Deterministic chain of single actions to test backprop depth.
    """

    def __init__(self, max_depth=3, reward=2.0):
        self.max_depth = max_depth
        self.reward = reward

    def get_initial_state(self):
        return {"depth": 0, "root_player": 0}

    def clone_state(self, state):
        return dict(state)

    def get_possible_actions(self, state):
        return [] if state["depth"] >= self.max_depth else ["next"]

    def apply_action(self, state, action):
        return {"depth": state["depth"] + 1, "root_player": state["root_player"]}

    def is_terminal(self, state):
        return state["depth"] >= self.max_depth

    def get_player_turn(self, state):
        return state["root_player"]

    def rollout(self, state, root_player, rng):
        return self.reward


class TerminalRootAdapter(MCTSAdapter):
    def get_initial_state(self):
        return {"terminal": True, "root_player": 0}

    def clone_state(self, state):
        return dict(state)

    def get_possible_actions(self, state):
        return []

    def apply_action(self, state, action):
        return dict(state)

    def is_terminal(self, state):
        return True

    def get_player_turn(self, state):
        return state["root_player"]

    def rollout(self, state, root_player, rng):
        return 0.5


class MultiArmAdapter(MCTSAdapter):
    def get_initial_state(self):
        return {"depth": 0, "root_player": 0}

    def clone_state(self, state):
        return dict(state)

    def get_possible_actions(self, state):
        return ["bad", "good_1", "good_2"] if state["depth"] == 0 else []

    def apply_action(self, state, action):
        return {"depth": 1, "root_player": 0, "action": action}

    def is_terminal(self, state):
        return state["depth"] >= 1

    def get_player_turn(self, state):
        return state["root_player"]

    def rollout(self, state, root_player, rng):
        return 0.0 if state["action"] == "bad" else 1.0


class EqualRewardAdapter(MCTSAdapter):
    def get_initial_state(self):
        return {"depth": 0, "root_player": 0}

    def clone_state(self, state):
        return dict(state)

    def get_possible_actions(self, state):
        return ["a", "b"] if state["depth"] == 0 else []

    def apply_action(self, state, action):
        return {"depth": 1, "root_player": 0, "action": action}

    def is_terminal(self, state):
        return state["depth"] >= 1

    def get_player_turn(self, state):
        return state["root_player"]

    def rollout(self, state, root_player, rng):
        return 1.0


def test_search_best_move_prefers_higher_value_action():
    player = MonteCarloPlayer(
        SimpleBanditAdapter(),
        exploration_constant=0.0,
        rng=random.Random(0),
    )

    best = player.search_best_move(rollouts=200)

    assert best is not None
    assert best.action == "good"


def test_backprop_reaches_root():
    player = MonteCarloPlayer(ChainAdapter(max_depth=3, reward=2.0), rng=random.Random(0))

    player.explore_action_tree(epochs=1, log=False)

    assert player.action_tree.visits == 1
    assert player.action_tree.value == 2.0


def test_reset_root_rebuilds_tree_from_external_state():
    adapter = SimpleBanditAdapter()
    player = MonteCarloPlayer(adapter, rng=random.Random(0))

    progressed_state = adapter.apply_action(adapter.get_initial_state(), "bad")
    player.reset_root(progressed_state)

    assert player.action_tree.get_simulation_state()["depth"] == 1
    assert player.action_tree.parent is None
    assert player.action_tree.children == []


def test_get_child_by_id_returns_none_for_unknown_id():
    player = MonteCarloPlayer(SimpleBanditAdapter(), rng=random.Random(0))

    child = player.get_child_by_id(999999)

    assert child is None


def test_terminal_root_returns_no_move_and_still_updates_visits():
    player = MonteCarloPlayer(TerminalRootAdapter(), rng=random.Random(0))

    best = player.search_best_move(rollouts=5)

    assert best is None
    assert player.action_tree.visits == 5
    assert player.action_tree.value == 2.5


def test_execute_action_on_simulation_detaches_selected_node():
    player = MonteCarloPlayer(SimpleBanditAdapter(), rng=random.Random(0))
    child = player.expand_node(player.action_tree)

    assert child is not None
    assert child.parent is player.action_tree

    player.execute_action_on_simulation(child)

    assert player.action_tree is child
    assert player.action_tree.parent is None


def test_select_best_child_evaluates_all_children_regression():
    player = MonteCarloPlayer(
        MultiArmAdapter(),
        exploration_constant=0.0,
        rng=random.Random(0),
    )

    best = player.search_best_move(rollouts=300)

    assert best is not None
    assert best.action in {"good_1", "good_2"}


def test_tie_break_on_best_visits_can_choose_multiple_children():
    choices = set()
    for seed in range(10):
        player = MonteCarloPlayer(
            EqualRewardAdapter(),
            exploration_constant=0.0,
            rng=random.Random(seed),
        )
        player.search_best_move(rollouts=2)
        choices.add(player.get_best_move().action)

    assert choices == {"a", "b"}
