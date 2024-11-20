from MCTSAgent.MCTSAgent import MontecarloPlayer
from Switcher.logic.logic import Switcher
from Switcher.mcts_functions import (
    expansion_function,
    movement_choice_function,
    retropropagation_function,
    selection_function,
    simulation_function,
)
from Switcher.mcts_simulation import SwitcherSimulation

game = Switcher(players_quantity=2)
game.deal_figures()
game.deal_moves()
simulation = SwitcherSimulation(game)

player_1 = MontecarloPlayer(
    original_simulation=simulation,
    selection_function=selection_function,
    expansion_function=expansion_function,
    retropropagation_function=retropropagation_function,
    simulation_function=simulation_function,
    movement_choice_function=movement_choice_function,
)

player_2 = MontecarloPlayer(
    original_simulation=simulation,
    selection_function=selection_function,
    expansion_function=expansion_function,
    retropropagation_function=retropropagation_function,
    simulation_function=simulation_function,
    movement_choice_function=movement_choice_function,
)


players = {0: player_1, 1: player_2}
i = 0
while i < 100:
    print(i)
    current_player_turn = simulation.logic.player_turn
    print(f"Player {current_player_turn} turn")
    current_player = players[current_player_turn]

    action_node = current_player.search_best_move(1)
    print(action_node)
    current_player.execute_action_on_simulation(action_node)
    simulation.logic.do_move(action_node.action)
    i += 1
