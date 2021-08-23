import pygame

white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)

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

    def draw_ellipse(self, tile):
        margin_x = self.window_relations.get('rect_margin_x')
        margin_y = self.window_relations.get('rect_margin_y')
        width = self.window_relations.get('rect_width')
        height = self.window_relations.get('rect_height')
        line_width = self.window_relations.get('line_width')

        pygame.draw.ellipse(self.window, green, (tile.rect.x + margin_x, tile.rect.y + margin_y, width, height), line_width)

    def draw_cross(self, tile):
        margin_x = self.window_relations.get('rect_margin_x')
        margin_y = self.window_relations.get('rect_margin_y')
        width = self.window_relations.get('rect_width')
        height = self.window_relations.get('rect_height')
        line_width = self.window_relations.get('line_width')

        first_line_start = (tile.rect.x + margin_x, tile.rect.y + margin_y)
        first_line_end = (first_line_start[0] + width, first_line_start[1] + height)
        second_line_start = (tile.rect.x + margin_x, tile.rect.y + margin_y + height)
        second_line_end = (first_line_start[0] + width, first_line_start[1])
        pygame.draw.line(self.window, red, first_line_start, first_line_end, line_width)
        pygame.draw.line(self.window, red, second_line_start, second_line_end, line_width)

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
        window_relations['rect_margin_x'] = self.window_width / 22
        window_relations['rect_margin_y'] = self.window_height / 22
        window_relations['rect_width'] = self.window_width / 5.5
        window_relations['rect_height'] = self.window_height / 5.5
        window_relations['line_width'] = (self.window_width + self.window_height) // 110
        window_relations['tile_width'] = self.window_width * 3 // 11
        window_relations['tile_height'] = self.window_height * 3 // 11
        window_relations['tile_margin_x'] = self.window_width / 22
        window_relations['tile_margin_y'] = self.window_height / 22
        window_relations['tile_rect_x_multiplier'] = self.window_width * 7 / 22
        window_relations['tile_rect_y_multiplier'] = self.window_height * 7 / 22
        return window_relations

    def game_finished_messages(self, winner, player_one_figure, is_ia_player_one):
        message = None
        if winner == '-':
            message = 'Tie, press space and play again'
        elif winner == (player_one_figure and is_ia_player_one) or winner != (player_one_figure and not is_ia_player_one):
            message = 'I Won !!! press space and try again.'
        else:
            message = 'I Can´t believe you beat me :('

        return message
