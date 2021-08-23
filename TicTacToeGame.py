import pygame
from TicTacToe.TicTacToeLogic import TicTacToe
from MCTSAgent.MCTSAgent import MontecarloPlayer
from TicTacToe.TicTacToeMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function
from TicTacToe.TicTacToeGameRenderManager import GameRenderManager, Tile

tic_tac_toe = TicTacToe()
player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

def execute_ia_move(ia_player):
    action_node = ia_player.search_best_move(1)
    tic_tac_toe.execute_action(action_node.action)
    ia_player.execute_action_on_simulation(action_node)
    return action_node

def make_play_and_check_winner(ia_player, action_node):
    tic_tac_toe.execute_action(action_node.action)
    ia_player.execute_action_on_simulation(action_node)
    winner = tic_tac_toe.player_winner()
    return winner

def find_ia_action_node(ia_player, row_action, column_action):
    action_node = None
    for child in ia_player.action_tree.childs:
        if child.action == (row_action, column_action):
            action_node = child
    return action_node

window_width = 400
window_height = 400

pygame.init()
pygame.display.set_caption('Thinking ...')

game_manager_render = GameRenderManager(window_width, window_height)

game_manager_render.draw_tiles()

run = True
winner = None

ia_go_first = True

while run:

    pygame.time.delay(100)

    if ia_go_first == tic_tac_toe.player_one_move and winner == None:
        pygame.display.set_caption('Thinking ...')
        action_node = player.search_best_move(0.5)
        figure = figure = game_manager_render.get_player_figure(tic_tac_toe.player_one_move)
        game_manager_render.draw_figure(figure, action_node.action)
        winner = make_play_and_check_winner(player, action_node)

    else:
        pygame.display.set_caption('Your Turn')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_manager_render.draw_tiles()
                    game_manager_render.taken_list = pygame.sprite.Group()
                    tic_tac_toe = TicTacToe()
                    player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)
                    winner = None
                    ia_go_first = not ia_go_first
                    pygame.display.set_caption('Thinking ...') if ia_go_first else pygame.display.set_caption('Your Turn')

            if event.type == pygame.MOUSEBUTTONUP:
                if winner == None and ia_go_first != tic_tac_toe.player_one_move:
                    pos = pygame.mouse.get_pos()
                    for j, tile in enumerate(game_manager_render.tile_list):
                        if tile.rect.collidepoint(pos) and tile not in game_manager_render.taken_list:
                            column = j // 3
                            row = j % 3
                            figure = game_manager_render.get_player_figure(tic_tac_toe.player_one_move)
                            game_manager_render.draw_figure(figure, (row, column))

                            action_node = find_ia_action_node(player, row, column)

                            winner = make_play_and_check_winner(player, action_node)

    if winner != None:
        message = game_manager_render.game_finished_messages(winner, tic_tac_toe.player_one_figure, ia_go_first)
        pygame.display.set_caption(message)

    game_manager_render.redraw()

pygame.quit()