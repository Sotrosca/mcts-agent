import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ContainerDepotSimulation import Simulation
from ExampleMCTSFunctions import ContainerDepotMCTSAdapter

from MCTSAgent.MCTSAgent import MontecarloPlayer


def manhattan_distance(x_position, y_position):
    return abs(x_position[0] - y_position[0]) + abs(
        x_position[1] - y_position[1]
    )  # distancia infinito


board = [[[1, 2, 3], [14, 9, 0], [8, 0, 0]], [[4, 5, 0], [6, 0, 0], [0, 0, 0]]]

simulation = Simulation((0, 0), board, 0, manhattan_distance, [2, 4, 1])

player = MontecarloPlayer(ContainerDepotMCTSAdapter(simulation))

while not simulation.is_simulation_end():
    print(simulation.board)
    action_node = player.search_best_move(5)
    print(action_node.action)
    simulation.execute_action(action_node.action)
    player.execute_action_on_simulation(action_node)

"""Profiling helpers removed in adapter-based engine."""
