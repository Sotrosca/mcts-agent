#%%
import cProfile
import pstats

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from container_depot_simulation import Simulation
from example_mcts_functions import ContainerDepotMCTSAdapter
from mcts_agent.core import MonteCarloPlayer


def manhattan_distance(x_position, y_position):
    return  abs(x_position[0] - y_position[0]) + abs(x_position[1] - y_position[1]) # distancia infinito


board = [[[1,2,3], [14, 9, 0], [8, 0, 0]], [[4, 5, 0], [6, 0, 0], [0, 0, 0]], [[11,10,12], [0, 0, 0], [13, 0, 0]]]

simulation = Simulation((0, 0), board, 0, manhattan_distance, [2, 4, 1, 6, 5, 3, 13, 11, 9])

player = MonteCarloPlayer(ContainerDepotMCTSAdapter(simulation))

#%%
profiler = cProfile.Profile()
profiler.enable()

i = 1
while player.action_tree_depth < 30 and i < 50000:
    player.explore_action_tree(1, log=False)
    if i % 200 == 0:
        print((i, player.action_tree_depth))
    i += 1

profiler.disable()

stats = pstats.Stats(profiler).strip_dirs()

#%%
stats.sort_stats('tottime').print_stats()

#%%
for action in player.get_best_move_sequence():
    print(action.action)

