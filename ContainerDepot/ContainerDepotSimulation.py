from enum import Enum

class ActionType(Enum):
    MOVE = 1
    EXTRACT = 2
    END = 3

class Action():
    def __init__(self, source_cell, target_cell, action_type):
        self.source_cell = source_cell
        self.target_cell = target_cell
        self.type = action_type

    def __str__(self):
        if self.type == ActionType.MOVE:
            return str((self.source_cell.get_position(), self.target_cell.get_position(), self.type))
        elif self.type == ActionType.EXTRACT:
            return str((self.source_cell.get_position(), self.type))
        elif self.type == ActionType.END:
            return "Simulation is end"


class Simulation():
    def __init__(self, crane_position, board, time, distance_function, containers_to_extract_id):
        self.crane_position = crane_position
        self.board = board #dict[row][column][z]
        self.board_height = len(board)
        self.board_width = len(board[0])
        self.board_length = len(board[0][0])
        self.board_size_cell = self.calculate_board_size_cell()
        self.time = time
        self.distance_function = distance_function
        self.epochs = 0
        self.containers_to_extract_id = containers_to_extract_id
        self.move_actions = self.build_move_actions()
        self.history = {}

    def get_state(self):
        simulation_state_dict = {
            'crane_position' : self.crane_position,
            'board' : self.board,
            'board_size_cell' : self.board_size_cell,
            'board_height' : self.board_height,
            'board_width' : self.board_width,
            'board_length' : self.board_length,
            'time' : self.time,
            'epochs' : self.epochs,
            'containers_to_extract_id' : self.containers_to_extract_id,
            'move_actions' : self.move_actions
        }
        return simulation_state_dict

    def set_state(self, state_dict):
        self.crane_position = state_dict.get('crane_position')
        self.board = state_dict.get('board')
        self.board_size_cell = state_dict.get('board_size_cell')
        self.board_width = state_dict.get('board_width')
        self.board_height = state_dict.get('board_height')
        self.board_length = state_dict.get('board_length')
        self.time = state_dict.get('time')
        self.epochs = state_dict.get('epochs')
        self.containers_to_extract_id = state_dict.get('containers_to_extract_id')
        self.move_actions = state_dict.get('move_actions')

    def calculate_board_size_cell(self):
        board_size_cell = []
        for i in range(len(self.board)):
            board_size_cell.append([])
            for j in range(len(self.board[0])):
                try:
                    last_index_with_container = self.board[i][j].index(0)
                except ValueError:
                    last_index_with_container = len(self.board[i][j])
                board_size_cell[i].append(last_index_with_container)
        return board_size_cell


    def move_container(self, source_cell, target_cell):
        cell_size = self.board_size_cell[source_cell[0]][source_cell[1]]
        container_index = cell_size - 1
        container = self.board[source_cell[0]][source_cell[1]][container_index]
        self.board[source_cell[0]][source_cell[1]][container_index] = 0
        target_index = self.board_size_cell[target_cell[0]][target_cell[1]]
        self.board[target_cell[0]][target_cell[1]][target_index] = container
        self.board_size_cell[source_cell[0]][source_cell[1]] -= 1
        self.board_size_cell[target_cell[0]][target_cell[1]] += 1

        self.crane_position = target_cell

    def extract_container(self, source_cell):
        cell_size = self.board_size_cell[source_cell[0]][source_cell[1]]
        container_index = cell_size - 1
        container = self.board[source_cell[0]][source_cell[1]][container_index]
        if not container in self.containers_to_extract_id:
            print("Error container: " + str(container))
        else:
            self.board[source_cell[0]][source_cell[1]][container_index] = 0
            self.containers_to_extract_id.remove(container)
            self.crane_position = source_cell

    def run_one_epoch(self, action):
        self.execute_action(action)
        self.history[self.epochs] = action

    def execute_action(self, action):
        action_cost = 0
        if action.get('type') == 1:
            source_cell = action.get('source_cell')
            target_cell = action.get('target_cell')
            if self.board_size_cell[source_cell[0]][source_cell[1]] != 0 and self.board_size_cell[target_cell[0]][target_cell[1]] != self.board_length:
                action_cost = self.calculate_move_cost(source_cell, target_cell)
                self.move_container(source_cell, target_cell)
            else:
                self.time = 100000
        elif action.get('type') == 2:
            source_cell = action.get('source_cell')
            action_cost = self.calculate_extract_cost(source_cell)
            self.extract_container(source_cell)

        self.time += action_cost
        self.epochs += 1


    # Funciones de calculo de coste
    def calculate_move_cost(self, source_cell, target_cell):
        distance_crane_to_source = self.distance_function(self.crane_position, source_cell)
        distance_source_to_target = self.distance_function(source_cell, target_cell)
        return distance_crane_to_source + distance_source_to_target

    def calculate_extract_cost(self, source_cell):
        distance_crane_to_source = self.distance_function(self.crane_position, source_cell)
        return distance_crane_to_source + 1

    def get_possible_actions(self):
        actions = []

        if self.is_simulation_end():
            actions.append({'type' : 3})
            return actions
        else:
            for i in range(self.board_height):
                for j in range(self.board_width):
                    cell_size = self.board_size_cell[i][j]
                    if cell_size != 0:
                        first_container = self.board[i][j][cell_size - 1]
                        if first_container == self.containers_to_extract_id[0]:
                            actions.append({'source_cell' : (i, j), 'type' : 2})
                        else:
                            pass
#                            actions.extend(self.get_all_move_actions_from_cell((i, j)))
            actions.extend(self.move_actions)
        return actions

    def get_all_move_actions_from_cell(self, source_cell):
        actions = [{'source_cell' : source_cell, 'target_cell' : (i, j), 'type' : 1} for i in range(self.board_height) for j in range(self.board_width) if (source_cell[0] != i or source_cell[1] != j) and (self.board_size_cell[i][j] < self.board_length)]

        return actions


    def build_move_actions(self):
        actions = []
        for i in range(self.board_height):
            for j in range(self.board_width):
                cell_move_actions = [{'source_cell' : (i, j), 'target_cell' : (k, l), 'type' : 1} for k in range(self.board_height) for l in range(self.board_width) if i != k or j != l]
                actions.extend(cell_move_actions)

        return actions

    def get_cell(self, x, y):
        return self.board.cell_matrix[x][y]

    def is_simulation_end(self):
        return len(self.containers_to_extract_id) == 0

