import pygame
from TicTacToe.TicTacToeLogic import TicTacToe
from MCTSAgent.MCTSAgent import MontecarloPlayer
from TicTacToe.TicTacToeMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function


tic_tac_toe = TicTacToe()
player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

class Tile(pygame.sprite.Sprite):

    def __init__(self, surface_width, surface_height):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([surface_width, surface_height])
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
        self.window_relations = self.calculate_window_relations()
        self.fill_tile_list()


    def get_tile_to_draw(self, grid_cordinates):
        tile_index = 3 * grid_cordinates[1] + grid_cordinates[0]
        tile = self.tile_list.sprites()[tile_index]
        self.taken_list.add(tile)

        return tile

    def draw_figure(self, figure, grid_cordinates):
        tile = self.get_tile_to_draw(grid_cordinates)

        if figure == 'circle':
            self.draw_ellipse(tile)
        elif figure == 'rect':
            self.draw_square(tile)
        elif figure == 'cross':
            self.draw_cross(tile)

    def draw_circle(self, tile):
        margin_x = self.window_relations.get('circle_margin_x')
        margin_y = self.window_relations.get('circle_margin_y')
        line_width = self.window_relations.get('circle_line_width')
        radius = self.window_relations.get('circle_radius')
        pygame.draw.circle(self.window, green, (tile.rect.x + margin_x, tile.rect.y + margin_y), radius, line_width)

    def draw_ellipse(self, tile):
        margin_x = self.window_relations.get('cross_margin_x')
        margin_y = self.window_relations.get('cross_margin_y')
        width = self.window_relations.get('cross_width')
        height = self.window_relations.get('cross_height')
        width_line = self.window_relations.get('cross_width_line')

        pygame.draw.ellipse(self.window, green, (tile.rect.x + margin_x, tile.rect.y + margin_y, width, height), width_line)


    def draw_square(self, tile):
        margin_x = self.window_width / 22
        margin_y = self.window_height / 22
        width = self.window_width / 5.5
        height = self.window_height / 5.5
        pygame.draw.rect(self.window, red, (tile.rect.x + margin_x, tile.rect.y + margin_y, width, height))

    def draw_cross(self, tile):
        margin_x = self.window_relations.get('cross_margin_x')
        margin_y = self.window_relations.get('cross_margin_y')
        width = self.window_relations.get('cross_width')
        height = self.window_relations.get('cross_height')
        width_line = self.window_relations.get('cross_width_line')

        first_line_start = (tile.rect.x + margin_x, tile.rect.y + margin_y)
        first_line_end = (first_line_start[0] + width, first_line_start[1] + height)
        second_line_start = (tile.rect.x + margin_x, tile.rect.y + margin_y + height)
        second_line_end = (first_line_start[0] + width, first_line_start[1])
        pygame.draw.line(self.window, red, first_line_start, first_line_end, width_line)
        pygame.draw.line(self.window, red, second_line_start, second_line_end, width_line)

    def fill_tile_list(self):
        for row in range(3):
            for column in range(3):
                tile = Tile(self.window_relations.get('tile_width'), self.window_relations.get('tile_height'))
                tile.rect.x = self.window_relations.get('tile_margin_x') + self.window_relations.get('tile_rect_x_multiplier') * row
                tile.rect.y = self.window_relations.get('tile_margin_y') + self.window_relations.get('tile_rect_y_multiplier') * column
                self.tile_list.add(tile)

    def draw_tiles(self):
        self.tile_list.draw(self.window)

    def redraw(self):
        pygame.display.update()

    def get_player_figure(self, is_player_one):
        if is_player_one:
            return 'cross'
        else:
            return 'circle'

    def calculate_window_relations(self):
        window_relations = {}
        window_relations['circle_margin_x'] = self.window_width * 3 / 22
        window_relations['circle_margin_y'] = self.window_height * 3 / 22
        window_relations['circle_radius'] = int((self.window_width + self.window_width) * 6 / 110)
        window_relations['circle_line_width'] = int((self.window_width + self.window_width) / 137.5)
        window_relations['cross_margin_x'] = self.window_width / 22
        window_relations['cross_margin_y'] = self.window_height / 22
        window_relations['cross_width'] = self.window_width / 5.5
        window_relations['cross_height'] = self.window_height / 5.5
        window_relations['cross_width_line'] = (self.window_width + self.window_height) // 110
        window_relations['tile_width'] = self.window_width * 3 // 11
        window_relations['tile_height'] = self.window_height * 3 // 11
        window_relations['tile_margin_x'] = self.window_width / 22
        window_relations['tile_margin_y'] = self.window_height / 22
        window_relations['tile_rect_x_multiplier'] = self.window_width * 7 / 22
        window_relations['tile_rect_y_multiplier'] = self.window_height * 7 / 22
        return window_relations


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

window_width = 300
window_height = 500
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)

pygame.init()
pygame.display.set_caption('Tic Tac Toe')

game_manager_render = GameRenderManager(window_width, window_height)

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