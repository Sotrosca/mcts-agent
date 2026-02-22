from MCTSAgent.MCTSAgent import MontecarloPlayer
from Switcher.logic.logic import Switcher
from Switcher.mcts_functions import SwitcherMCTSAdapter
from Switcher.mcts_simulation import SwitcherSimulation

game = Switcher(players_quantity=2)
game.deal_figures()
game.deal_moves()
simulation = SwitcherSimulation(game)
adapter_1 = SwitcherMCTSAdapter(simulation)
adapter_2 = SwitcherMCTSAdapter(simulation)

player_1 = MontecarloPlayer(
    adapter=adapter_1,
)

player_2 = MontecarloPlayer(
    adapter=adapter_2,
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
    simulation.logic.do_move(action_node.action)
    state = simulation.get_state()
    for player in players.values():
        player.reset_root(state)
    i += 1
