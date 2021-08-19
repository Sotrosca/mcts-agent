from ContainerDepotSimulation import Simulation
from MCTSAgent import MontecarloPlayer
import cProfile, pstats
from ExampleMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function


def manhattan_distance(x_position, y_position):
    return  abs(x_position[0] - y_position[0]) + abs(x_position[1] - y_position[1]) # distancia infinito


board = [[[1,2,3], [0, 0, 0], [0, 0, 0]], [[4, 5, 0], [6, 0, 0], [0, 0, 0]]]

simulation = Simulation((0, 0), board, 0, manhattan_distance, [2, 4, 1, 6, 3])

player = MontecarloPlayer(simulation, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

profiler = cProfile.Profile()
profiler.enable()

i = 1

while player.action_tree_depth < 10 and i < 50000:
    player.explore_action_tree(1, log=False)
    if i % 200 == 0:
        print((i, player.action_tree_depth))
    i += 1

profiler.disable()

stats = pstats.Stats(profiler).strip_dirs()

stats.sort_stats('tottime').print_stats()