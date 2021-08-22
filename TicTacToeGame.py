import pygame
from TicTacToe.TicTacToeLogic import TicTacToe
from MCTSAgent.MCTSAgent import MontecarloPlayer
from TicTacToe.TicTacToeMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function


tic_tac_toe = TicTacToe()
player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

class Tile(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([150, 150])
        self.image.fill(white)
        self.rect = self.image.get_rect()

class GameRenderManager():

    def __init__(self, window_width = 550, window_height = 550):
        self.tile_list = pygame.sprite.Group()
        self.taken_list = pygame.sprite.Group()
        self.window_width = window_width
        self.window_height = window_height
        self.window = pygame.display.set_mode((window_width, window_height))
        self.ia_thinking = False
        self.fill_tile_list()

    def get_tile_to_draw(self, grid_cordinates):
        tile_index = 3 * grid_cordinates[1] + grid_cordinates[0]
        tile = self.tile_list.sprites()[tile_index]
        self.taken_list.add(tile)

        return tile

    def draw_figure(self, figure, grid_cordinates):

        tile = self.get_tile_to_draw(grid_cordinates)

        if figure == 'circle':
            self.draw_circle(tile)
        elif figure == 'rect':
            self.draw_square(tile)
        elif figure == 'cross':
            self.draw_cross(tile)

    def draw_circle(self, tile):
        pygame.draw.circle(self.window, green, (tile.rect.x + 75, tile.rect.y + 75), 50)

    def draw_square(self, tile):
        pygame.draw.rect(self.window, red, (tile.rect.x + 25, tile.rect.y + 25, 100, 100))

    def draw_cross(self, tile):
        pass

    def fill_tile_list(self):
        for row in range(3):
            for column in range(3):
                tile = Tile()
                tile.rect.x = 25 + 175 * row
                tile.rect.y = 25 + 175 * column
                self.tile_list.add(tile)

    def draw_tiles(self):
        self.tile_list.draw(self.window)

    def redraw(self):
        pygame.display.update()

    def get_player_figure(self, is_player_one):
        if is_player_one:
            return 'rect'
        else:
            return 'circle'




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

window_width = 550
window_height = 550
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)

pygame.init()
pygame.display.set_caption('Tic Tac Toe')

game_manager_render = GameRenderManager(550, 550)

game_manager_render.draw_tiles()

run = True
winner = None
while run:

    pygame.time.delay(100)

    if tic_tac_toe.player_one_move and winner == None:
        action_node = player.search_best_move(1)
        figure = figure = game_manager_render.get_player_figure(tic_tac_toe.player_one_move)
        game_manager_render.draw_figure(figure, action_node.action)
        winner = make_play_and_check_winner(player, action_node)

    else:
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

            if event.type == pygame.MOUSEBUTTONUP:
                if winner == None and not tic_tac_toe.player_one_move:
                    pos = pygame.mouse.get_pos()
                    for j, tile in enumerate(game_manager_render.tile_list):
                        if tile.rect.collidepoint(pos) and tile not in game_manager_render.taken_list:
                            column = j // 3
                            row = j % 3
                            figure = game_manager_render.get_player_figure(tic_tac_toe.player_one_move)
                            game_manager_render.draw_figure(figure, (row, column))

                            action_node = find_ia_action_node(player, row, column)

                            winner = make_play_and_check_winner(player, action_node)


    game_manager_render.redraw()

pygame.quit()