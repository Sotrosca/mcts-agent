from TicTacToeLogic import TicTacToe
from MCTSAgent import MontecarloPlayer
from TicTacToeMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function

tic_tac_toe = TicTacToe()

tic_tac_toe.print_board()
tic_tac_toe.execute_action((1, 1))
tic_tac_toe.execute_action((0, 0))
tic_tac_toe.execute_action((1, 0))
tic_tac_toe.execute_action((1, 2))
tic_tac_toe.execute_action((0, 1))
tic_tac_toe.execute_action((2, 1))
tic_tac_toe.execute_action((2, 0))
# tic_tac_toe.execute_action((2, 2))
# tic_tac_toe.execute_action((0, 2))

tic_tac_toe.print_board()

tic_tac_toe.player_winner()

print(tic_tac_toe.get_possible_actions())

player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

action_node = player.search_best_move()

for child in player.action_tree.childs:
    print(child.action, child.value, child.visits)

