import pygame
from TicTacToeLogic import TicTacToe
from MCTSAgent import MontecarloPlayer
from TicTacToeMCTSFunctions import selection_function, expansion_function, retropropagation_function, movement_choice_function, simulation_function


tic_tac_toe = TicTacToe()
player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)
print(player.action_tree.childs)

pygame.init()

win = pygame.display.set_mode((550, 550))

pygame.display.set_caption('Tic Tac Toe')

white = (255, 255, 255)

red = (255, 0, 0)

green = (0, 255, 0)


class Tile(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([150, 150])
        self.image.fill(white)
        self.rect = self.image.get_rect()

tile_list = pygame.sprite.Group()

taken_list = pygame.sprite.Group()

for row in range(3):
    for column in range(3):
        tile = Tile()
        tile.rect.x = 25 + 175 * row
        tile.rect.y = 25 + 175 * column
        tile_list.add(tile)

tile_list.draw(win)

def redraw():
    pygame.display.update()

draw_object = 'rect'
run = True
winner = None
while run:

    pygame.time.delay(100)

    if draw_object == 'circle' and winner == None:
        action_node = player.search_best_move(1)
        print(action_node.action)
        for child in player.action_tree.childs:
            print(child.action, child.value, child.visits)
        tic_tac_toe.execute_action(action_node.action)
        player.execute_action_on_simulation(action_node)
        tile_index = 3 * action_node.action[1] + action_node.action[0]
        tile = tile_list.sprites()[tile_index]
        taken_list.add(tile)
        pygame.draw.circle(win, green, (tile.rect.x + 75, tile.rect.y + 75), 50)
        draw_object = 'rect'
        winner = tic_tac_toe.player_winner()
        tic_tac_toe.print_board()
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    tile_list.draw(win)
                    taken_list = pygame.sprite.Group()
                    tic_tac_toe = TicTacToe()
                    player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)
                    winner = None
                    draw_object = 'rect'

            if event.type == pygame.MOUSEBUTTONUP:
                if winner == None and draw_object == 'rect':
                    pos = pygame.mouse.get_pos()
                    for j, tile in enumerate(tile_list):
                        if tile.rect.collidepoint(pos) and tile not in taken_list:
                            taken_list.add(tile)
                            column = j // 3
                            row = j % 3
                            if draw_object == 'rect':
                                pygame.draw.rect(win, red, (tile.rect.x + 25, tile.rect.y + 25, 100, 100))
                                draw_object = 'circle'
                            else:
                                pygame.draw.circle(win, green, (tile.rect.x + 75, tile.rect.y + 75), 50)
                                draw_object = 'rect'
                            action_node = None
                            print((row, column))
                            for child in player.action_tree.childs:
                                if child.action == (row, column):
                                    action_node = child

                            tic_tac_toe.execute_action((row, column))
                            if action_node != None:
                                player.execute_action_on_simulation(action_node)
                            else:
                                player = MontecarloPlayer(tic_tac_toe, selection_function, expansion_function, retropropagation_function, simulation_function, movement_choice_function)

                            winner = tic_tac_toe.player_winner()
                            tic_tac_toe.print_board()
    redraw()

pygame.quit()