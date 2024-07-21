import sys

import pygame

from Switcher.figures import figures, find_figures
from Switcher.logic import Board, MovementCard, Switcher

game = Switcher(1)
board: Board = game.board

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 400
CELL_SIZE = SCREEN_WIDTH // board.size[0]

# Colors
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
BACKGROUND_COLOR = (255, 255, 255)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Board setup

selected_cells = []


def draw_board(board_state):
    board_image = [[COLORS[(cell.color - 1)] for cell in row] for row in board_state]
    for y, row in enumerate(board_image):
        for x, color in enumerate(row):
            pygame.draw.rect(
                screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )


def print_board(board_state):
    for row in board_state:
        row = ["*" if cell == -1 else str(cell) for cell in row]
        print(" ".join(row))


def switch_colors():
    if len(selected_cells) == 2:
        cell1_x, cell1_y = selected_cells[0]
        cell2_x, cell2_y = selected_cells[1]
        print(f"Switching {cell1_x}, {cell1_y} with {cell2_x}, {cell2_y}")
        valid_move = game.board.switch_cells(cell1_y, cell1_x, cell2_y, cell2_x)
        selected_cells.clear()
        board_state_with_border = game.board.get_board_state_color(with_border=True)
        # print_board(board_state_with_border)
        for color in range(1, board.color_quantity + 1):
            find_figures(board_state_with_border, color)


def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                cell_x, cell_y = x // CELL_SIZE, y // CELL_SIZE
                selected_cells.append((cell_x, cell_y))
                if len(selected_cells) == 2:
                    switch_colors()

        screen.fill(BACKGROUND_COLOR)
        draw_board(board.state)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
