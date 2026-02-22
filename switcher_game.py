import sys

import pygame

from switcher.game import Game
from switcher.game.scenes.game_scene import GameScene
from switcher.mcts_simulation import SwitcherSimulation

if __name__ == "__main__":
    pygame.init()
    game = Game()
    simulation = SwitcherSimulation(game.logic)
    ui = GameScene(game, simulation)
    ui.main_loop()
