import pickle
import time

class NaturalNumbersIterator():
    def __iter__(self):
        self.a = 0
        return self

    def __next__(self):
        x = self.a
        self.a += 1
        return x

class MontecarloPlayer():
    def __init__(self, original_simulation, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function):
        self.ids_nodes = iter(NaturalNumbersIterator())
        self.original_simulation = pickle.loads(pickle.dumps(original_simulation, -1))
        self.copy_simulation = pickle.loads(pickle.dumps(original_simulation, -1))
        self.action_tree = Node(None, [], None, self.copy_simulation.get_state(), 0, 0)
        self.action_tree_depth = 0
        self.init_tree_nodes()
        self.selection_function = selection_function
        self.expansion_function = expansion_function
        self.simulation_function = simulation_function
        self.retropropagation_function = retropropagation_function
        self.movement_choice_function = movement_choice_function

    def init_tree_nodes(self):
        self.expand_node(self.action_tree)

    def get_child_by_id(self, id_child):
        for child in self.action_tree.childs:
            if child.id == id_child:
                return child
        return None

    def get_child_by_id(self, id_child, parent):
        for child in parent.childs:
            if child.id == id_child:
                return child
        return None

    def search_best_move(self, time_to_search=1, log=False):
        start_time = time.time()
        num_rollouts = 0

        while time.time() - start_time < time_to_search:
            self.explore_action_tree(epochs=1 , log=False)
            num_rollouts += 1
        if log:
            run_time = time.time() - start_time
            print(run_time)
            print(num_rollouts)
        return self.get_best_move()

    def execute_action_on_simulation(self, action_node):
        self.original_simulation.set_state(action_node.get_simulation_state())
        self.copy_simulation.set_state(action_node.get_simulation_state())
        self.action_tree = action_node
        self.action_tree_depth -= 1

    def explore_action_tree(self, epochs = 1000, log=True, log_frecuency=100):
        for epoch in range(epochs):
            if log and epoch % log_frecuency == 0:
                print(epoch)
            action_node = self.selection_function(self.action_tree)
            if (self.expansion_function(action_node)):
                self.expand_node(action_node)
                action_node = self.selection_function(action_node)

            simulation_finished = self.simulation_function(action_node, self.copy_simulation)
            self.retropropagation_function(self.original_simulation, simulation_finished, action_node)

    def get_best_move(self):
        return self.movement_choice_function(self.action_tree)

    def set_action_tree_depth(self, level):
        if level > self.action_tree_depth:
            self.action_tree_depth = level

    def get_best_move_sequence(self):
        move_sequence = []
        node = self.action_tree

        while node.has_childs():
            best_child = self.movement_choice_function(node)
            move_sequence.append(best_child)
            node = best_child

        return move_sequence

    def expand_node(self, action_node):
        new_level = action_node.level + 1
        self.copy_simulation.set_state(pickle.loads(pickle.dumps(action_node.get_simulation_state(), -1)))
        possible_actions = self.copy_simulation.get_possible_actions()

        for action in possible_actions:
            self.copy_simulation.set_state(pickle.loads(pickle.dumps(action_node.get_simulation_state(), -1)))
            self.copy_simulation.execute_action(action)
            new_simulation_state = pickle.loads(pickle.dumps(self.copy_simulation.get_state(), -1))
            action_node.childs.append(Node(action_node, [], action, new_simulation_state, self.ids_nodes.__next__(), new_level))
        self.set_action_tree_depth(new_level)


class Node():
    def __init__(self, parent, childs, action, simulation_state, id_node, level):
        self.parent = parent #Node
        self.childs = childs #Node[]
        self.action = action # Accion realizada para llegar al estado representado en simulation_state
        self.simulation_state = simulation_state # Estado de la simulacion con la action ya realizada
        self.visits = 0
        self.value = 0
        self.id = id_node
        self.level = level

    def __str__(self):
        return "Id: " + str(self.id) + " - " + "visits: " + str(self.visits) + " - " + "value: " + str(self.value)

    def has_childs(self):
        return self.childs != None and len(self.childs) > 0

    def get_childs_without_visits(self):
        childs_without_love = []
        for child in self.childs:
            if child.visits == 0:
                childs_without_love.append(child)

        return childs_without_love

    def has_parent(self):
        return self.parent != None

    def get_simulation_state(self):
        return self.simulation_state
