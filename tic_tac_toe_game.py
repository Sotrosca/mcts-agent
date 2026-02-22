import pygame
from mcts_agent import MonteCarloPlayer
from tic_tac_toe import TicTacToe, TicTacToeMCTSAdapter
from tic_tac_toe.tic_tac_toe_game_render_manager import GameRenderManager, Tile

tic_tac_toe = TicTacToe()
player = MonteCarloPlayer(TicTacToeMCTSAdapter(tic_tac_toe))

def execute_ai_move(ai_player):
    action_node = ai_player.search_best_move(1)
    tic_tac_toe.execute_action(action_node.action)
    ai_player.execute_action_on_simulation(action_node)
    return action_node

def make_play_and_check_winner(ai_player, action_node):
    tic_tac_toe.execute_action(action_node.action)
    ai_player.execute_action_on_simulation(action_node)
    winner = tic_tac_toe.player_winner()
    return winner

def find_ai_action_node(ai_player, row_action, column_action):
    action_node = None
    for child in ai_player.action_tree.children:
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

ai_goes_first = True

while run:

    pygame.time.delay(100)

    if ai_goes_first == tic_tac_toe.player_one_move and winner is None:
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
                    player = MonteCarloPlayer(TicTacToeMCTSAdapter(tic_tac_toe))
                    winner = None
                    ai_goes_first = not ai_goes_first
                    pygame.display.set_caption('Thinking ...') if ai_goes_first else pygame.display.set_caption('Your Turn')

            if event.type == pygame.MOUSEBUTTONUP:
                if winner is None and ai_goes_first != tic_tac_toe.player_one_move:
                    pos = pygame.mouse.get_pos()
                    for j, tile in enumerate(game_manager_render.tile_list):
                        if tile.rect.collidepoint(pos) and tile not in game_manager_render.taken_list:
                            column = j // 3
                            row = j % 3
                            figure = game_manager_render.get_player_figure(tic_tac_toe.player_one_move)
                            game_manager_render.draw_figure(figure, (row, column))

                            action_node = find_ai_action_node(player, row, column)

                            winner = make_play_and_check_winner(player, action_node)

    if winner is not None:
        message = game_manager_render.game_finished_messages(winner, tic_tac_toe.player_one_figure, ai_goes_first)
        pygame.display.set_caption(message)

    game_manager_render.redraw()

pygame.quit()