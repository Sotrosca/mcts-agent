import math
import random
import time


class NaturalNumbersIterator:
    def __iter__(self):
        self.a = 0
        return self

    def __next__(self):
        x = self.a
        self.a += 1
        return x


class MCTSAdapter:
    def get_initial_state(self):
        raise NotImplementedError()

    def clone_state(self, state):
        raise NotImplementedError()

    def get_possible_actions(self, state):
        raise NotImplementedError()

    def apply_action(self, state, action):
        raise NotImplementedError()

    def is_terminal(self, state):
        raise NotImplementedError()

    def get_player_turn(self, state):
        raise NotImplementedError()

    def rollout(self, state, root_player, rng):
        raise NotImplementedError()


class MonteCarloPlayer:
    def __init__(
        self,
        adapter,
        exploration_constant=1.4,
        rollout_limit=None,
        rng=None,
    ):
        self.ids_nodes = iter(NaturalNumbersIterator())
        self.adapter = adapter
        self.exploration_constant = exploration_constant
        self.rollout_limit = rollout_limit
        self.rng = rng or random.Random()
        initial_state = self.adapter.clone_state(self.adapter.get_initial_state())
        self.action_tree = self._build_root(initial_state)
        self.action_tree_depth = 0
        self.init_tree_nodes()
        self.root_player = None

    def init_tree_nodes(self):
        if self.action_tree.untried_actions is None:
            self.action_tree.untried_actions = self.adapter.get_possible_actions(
                self.action_tree.get_simulation_state()
            )

    def reset_root(self, state):
        self.ids_nodes = iter(NaturalNumbersIterator())
        self.action_tree = self._build_root(self.adapter.clone_state(state))
        self.action_tree_depth = 0
        self.root_player = None
        self.init_tree_nodes()
        while self.action_tree.untried_actions:
            self.expand_node(self.action_tree)

    def get_child_by_id(self, id_child, parent=None):
        parent = parent or self.action_tree
        for child in parent.childs:
            if child.id == id_child:
                return child
        return None

    def search_best_move(self, time_to_search=None, rollouts=None, log=False):
        if time_to_search is None and rollouts is None:
            rollouts = 1000
        start_time = time.time()
        num_rollouts = 0
        self.root_player = self.adapter.get_player_turn(
            self.action_tree.get_simulation_state()
        )

        while True:
            if rollouts is not None and num_rollouts >= rollouts:
                break
            if time_to_search is not None and time.time() - start_time >= time_to_search:
                break
            self.explore_action_tree(epochs=1, log=False)
            num_rollouts += 1
        if log:
            run_time = time.time() - start_time
            print(run_time)
            print(num_rollouts)
        return self.get_best_move()

    def execute_action_on_simulation(self, action_node):
        self.action_tree = action_node
        self.action_tree.parent = None

    def explore_action_tree(self, epochs=1000, log=True, log_frecuency=100):
        if self.root_player is None:
            self.root_player = self.adapter.get_player_turn(
                self.action_tree.get_simulation_state()
            )
        for epoch in range(epochs):
            if log and epoch % log_frecuency == 0:
                print(epoch)
            action_node = self._select(self.action_tree)
            if action_node is None:
                return
            reward = self.adapter.rollout(
                action_node.get_simulation_state(),
                self.root_player,
                self.rng,
            )
            self._backpropagate(action_node, reward)

    def get_best_move(self):
        if not self.action_tree.has_childs():
            return None
        best_visits = max(child.visits for child in self.action_tree.childs)
        best_childs = [
            child for child in self.action_tree.childs if child.visits == best_visits
        ]
        return self.rng.choice(best_childs)

    def set_action_tree_depth(self, level):
        if level > self.action_tree_depth:
            self.action_tree_depth = level

    def get_best_move_sequence(self):
        move_sequence = []
        node = self.action_tree

        while node.has_childs():
            best_child = self._best_child_by_visits(node)
            move_sequence.append(best_child)
            node = best_child

        return move_sequence

    def expand_node(self, action_node):
        if action_node.untried_actions is None:
            action_node.untried_actions = self.adapter.get_possible_actions(
                action_node.get_simulation_state()
            )
        if len(action_node.untried_actions) == 0:
            return None
        action = action_node.untried_actions.pop()
        new_state = self.adapter.apply_action(
            action_node.get_simulation_state(), action
        )
        new_level = action_node.level + 1
        child = Node(
            action_node,
            [],
            action,
            new_state,
            self.ids_nodes.__next__(),
            new_level,
            untried_actions=self.adapter.get_possible_actions(new_state),
        )
        action_node.childs.append(child)
        self.set_action_tree_depth(new_level)
        return child

    def _build_root(self, state):
        return Node(
            None,
            [],
            None,
            state,
            self.ids_nodes.__next__(),
            0,
            untried_actions=self.adapter.get_possible_actions(state),
        )

    def _select(self, node):
        current = node
        while not self.adapter.is_terminal(current.get_simulation_state()):
            if current.untried_actions:
                child = self.expand_node(current)
                return child if child is not None else current
            if not current.childs:
                return current
            current = self._select_best_child(current)
        return current

    def _uct_score(self, parent, child):
        if child.visits == 0:
            return float("inf")
        exploitation = child.value / child.visits
        exploration = self.exploration_constant * math.sqrt(
            math.log(max(1, parent.visits)) / child.visits
        )
        return exploitation + exploration

    def _select_best_child(self, node):
        parent_visits = node.visits
        log_parent = math.log(parent_visits) if parent_visits > 1 else 0.0
        exploration_constant = self.exploration_constant

        best_score = None
        best_childs = []
        for child in node.childs:
            if child.visits == 0:
                score = float("inf")
            else:
                exploitation = child.value / child.visits
                exploration = exploration_constant * math.sqrt(
                    log_parent / child.visits
                )
                score = exploitation + exploration
            if best_score is None or score > best_score:
                best_score = score
                best_childs = [child]
            elif score == best_score:
                best_childs.append(child)
        return self.rng.choice(best_childs)

    def _best_child_by_visits(self, node):
        best_visits = max(child.visits for child in node.childs)
        best_childs = [child for child in node.childs if child.visits == best_visits]
        return self.rng.choice(best_childs)

    def _backpropagate(self, node, reward):
        current = node
        while current is not None:
            current.visits += 1
            current.value += reward
            current = current.parent


class Node:
    def __init__(
        self,
        parent,
        childs,
        action,
        simulation_state,
        id_node,
        level,
        untried_actions=None,
    ):
        self.parent = parent  # Node
        self.childs = childs  # Node[]
        self.action = action  # Accion realizada para llegar al estado representado en simulation_state
        self.simulation_state = (
            simulation_state  # Estado de la simulacion con la action ya realizada
        )
        self.visits = 0
        self.value = 0
        self.id = id_node
        self.level = level
        self.untried_actions = untried_actions if untried_actions is not None else []

    def __str__(self):
        return (
            "Id: "
            + str(self.id)
            + " - "
            + "visits: "
            + str(self.visits)
            + " - "
            + "value: "
            + str(self.value)
        )

    def has_childs(self):
        return self.childs is not None and len(self.childs) > 0

    def get_childs_without_visits(self):
        childs_without_love = []
        for child in self.childs:
            if child.visits == 0:
                childs_without_love.append(child)

        return childs_without_love

    def has_parent(self):
        return self.parent is not None

    def get_simulation_state(self):
        return self.simulation_state


# Backward compatibility alias
MontecarloPlayer = MonteCarloPlayer
