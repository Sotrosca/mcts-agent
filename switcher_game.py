import sys

import pygame

from Switcher.game import Game
from Switcher.game.scenes.game_scene import GameScene
from Switcher.mcts_simulation import SwitcherSimulation

if __name__ == "__main__":
    pygame.init()
    game = Game()
    simulation = SwitcherSimulation(game.logic)
    ui = GameScene(game, simulation)
    ui.main_loop()
