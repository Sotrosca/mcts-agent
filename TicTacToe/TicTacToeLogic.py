class TicTacToe():
    def __init__(self):
        self.board = [[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']]
        self.player_one_move = True
        self.history = {}
        self.turn = 0
        self.rows_indices = self.build_rows_indices()
        self.columns_indices = self.build_columns_indices()
        self.diagonals_indices = [[(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]]
        self.line_indices = self.rows_indices + self.columns_indices + self.diagonals_indices
        self.player_one_figure = 'X'
        self.player_two_figure = 'O'

    def get_state(self):
        state_dict = {
            'board' : self.board,
            'player_one_move' : self.player_one_move,
            'turn' : self.turn,
            'player_turn_figure' : self.get_player_turn_figure()
        }
        return state_dict

    def set_state(self, state_dict):
        self.board = state_dict.get('board')
        self.player_one_move = state_dict.get('player_one_move')
        self.turn = state_dict.get('turn')

    def execute_action(self, action):
        if self.player_one_move:
            self.board[action[0]][action[1]] = 'X'
        else:
            self.board[action[0]][action[1]] = 'O'
        self.player_one_move = not self.player_one_move
        self.turn += 1

    def run_one_epoch(self, action):
        self.execute_action(action)
        self.history[self.turn] = action

    def get_possible_actions(self):
        if self.player_winner() != None:
            return []
        possible_actions = []
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    possible_actions.append((i, j))
        return possible_actions

    def print_board(self):
        for row in self.board:
            print('| ' + ' | '.join(row) + ' |')

    def build_rows_indices(self):
        rows = []

        for i in range(3):
            row = []
            for j in range(3):
                row.append((i, j))
            rows.append(row)
        return rows

    def build_columns_indices(self):
        columns = []

        for i in range(3):
            column = []
            for j in range(3):
                column.append((j, i))
            columns.append(column)
        return columns

    def player_winner(self):
        for line_index in self.line_indices:
            player_winner = self.get_player_line_winner(line_index)
            if player_winner != None:
                return player_winner
        if self.turn == 9:
            return '-'
        return None

    def get_player_line_winner(self, line_indices):
        first_element = self.board[line_indices[0][0]][line_indices[0][1]]

        if first_element != ' ' and all(first_element == self.board[line_indices[j][0]][line_indices[j][1]] for j in range(3)):
            return first_element
        else:
            return None

    def get_player_turn_figure(self):
        return self.player_one_figure if self.player_one_move else self.player_two_figure
