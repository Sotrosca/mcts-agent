import sys

import pygame

from Switcher.game.figures import find_figures
from Switcher.logic import Board, Switcher

players_qty = 2
game = Switcher(players_qty)
game.deal_figures()
game.deal_moves()
board: Board = game.board

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 880, 680

# Colors
COLORS = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 0)]
BACKGROUND_COLOR = (100, 130, 130)
BOARD_BACKGROUND_COLOR = (40, 40, 40)
CARD_COLOR = (255, 255, 255)
BORDER_COLOR = (40, 40, 40)
SELECTED_CELL_BORDER_COLOR = (210, 210, 210)

# Dimensions and positions
CARD_WIDTH, CARD_HEIGHT = 140, 350
CARDS_QTY = 3
BOARD_SIZE = 320
BOARD_POS = ((SCREEN_WIDTH - BOARD_SIZE) // 2, (SCREEN_HEIGHT - BOARD_SIZE) // 2)
SQUARE_SIZE = BOARD_SIZE // board.size[0]
MARGIN = 20

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Board setup
selected_cells = []
player_card_rects = [{} for _ in range(players_qty)]

# Define areas using pygame.Rect
board_rect = pygame.Rect(BOARD_POS[0], BOARD_POS[1], BOARD_SIZE, BOARD_SIZE)
player1_rect = pygame.Rect(
    BOARD_POS[0] - CARD_WIDTH - MARGIN,
    SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2,
    CARD_WIDTH,
    CARD_HEIGHT,
)
player2_rect = pygame.Rect(
    BOARD_POS[0] + BOARD_SIZE + MARGIN,
    SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2,
    CARD_WIDTH,
    CARD_HEIGHT,
)


def draw_board(board_state):
    pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, board_rect)
    board_image = [[COLORS[(cell.color - 1)] for cell in row] for row in board_state]
    for y, row in enumerate(board_image):
        for x, color in enumerate(row):
            border_color = (
                SELECTED_CELL_BORDER_COLOR if (x, y) in selected_cells else BORDER_COLOR
            )
            square_rect = pygame.Rect(
                BOARD_POS[0] + x * SQUARE_SIZE,
                BOARD_POS[1] + y * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )
            pygame.draw.rect(screen, color, square_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, square_rect, 3, border_radius=10)


def switch_colors():
    if len(selected_cells) == 2:
        cell1_x, cell1_y = selected_cells[0]
        cell2_x, cell2_y = selected_cells[1]
        print(f"Switching {cell1_x}, {cell1_y} with {cell2_x}, {cell2_y}")
        valid_move = game.board.switch_cells(cell1_y, cell1_x, cell2_y, cell2_x)
        selected_cells.clear()
        board_state_with_border = game.board.get_board_state_color(with_border=True)


def draw_card_area(player_index, pos):
    pygame.draw.rect(screen, CARD_COLOR, (*pos, CARD_WIDTH, CARD_HEIGHT))
    pygame.draw.rect(screen, BORDER_COLOR, (*pos, CARD_WIDTH, CARD_HEIGHT), 3)


def draw_card_areas(num_players):
    positions = [
        (BOARD_POS[0] - CARD_WIDTH - MARGIN, SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2),
        (BOARD_POS[0] + BOARD_SIZE + MARGIN, SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2),
        (SCREEN_WIDTH // 2 - CARD_HEIGHT // 2, BOARD_POS[1] - CARD_WIDTH - MARGIN),
        (SCREEN_WIDTH // 2 - CARD_HEIGHT // 2, BOARD_POS[1] + BOARD_SIZE + MARGIN),
    ]
    for i in range(num_players):
        draw_card_area(i, positions[i])


def draw_cards(num_players, player_card_rects, selected_card, selected_player_area):
    for player_index in range(num_players):
        player_cards = game.players[player_index].hand
        for i, card in player_cards.items():
            card_pos = get_card_position(player_index, i)
            card_text = pygame.font.SysFont("Arial", 16).render(
                card.name, True, (0, 0, 0)
            )
            if i not in player_card_rects[player_index]:
                player_card_rects[player_index][i] = pygame.Rect(
                    *card_pos, CARD_WIDTH, 100
                )
            player_card_rect = player_card_rects[player_index][i]
            border_color = (
                (255, 0, 0)
                if i == selected_card
                and game.player_turn == player_index
                and selected_player_area == player_index
                else BORDER_COLOR
            )
            pygame.draw.rect(screen, CARD_COLOR, player_card_rect)
            pygame.draw.rect(screen, border_color, player_card_rect, 3)
            screen.blit(card_text, (card_pos[0] + 10, card_pos[1] + 10))


def get_card_position(player_index, card_index):
    if player_index == 0:
        return (
            BOARD_POS[0] - CARD_WIDTH - MARGIN,
            SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 + card_index * 120,
        )
    elif player_index == 1:
        return (
            BOARD_POS[0] + BOARD_SIZE + MARGIN,
            SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 + card_index * 120,
        )
    elif player_index == 2:
        return (
            SCREEN_WIDTH // 2 - CARD_HEIGHT // 2 + card_index * 120,
            BOARD_POS[1] - CARD_WIDTH - MARGIN,
        )
    elif player_index == 3:
        return (
            SCREEN_WIDTH // 2 - CARD_HEIGHT // 2 + card_index * 120,
            BOARD_POS[1] + BOARD_SIZE + MARGIN,
        )


def get_square_coordinates(mouse_x, mouse_y):
    if board_rect.collidepoint(mouse_x, mouse_y):
        col = (mouse_x - BOARD_POS[0]) // SQUARE_SIZE
        row = (mouse_y - BOARD_POS[1]) // SQUARE_SIZE
        return col, row
    return None


def event_position_area(x, y):
    if board_rect.collidepoint(x, y):
        return "board"
    if player1_rect.collidepoint(x, y):
        return "player1"
    if player2_rect.collidepoint(x, y):
        return "player2"
    return None


def handle_card_click(
    area, pos, player_card_rects, selected_card, selected_player_area
):
    player_index = 0 if area == "player1" else 1
    for i, rect in player_card_rects[player_index].items():
        if rect.collidepoint(pos):
            selected_card = i
            selected_player_area = player_index
    return selected_card, selected_player_area


def main():
    selected_card = None
    selected_player_area = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                area = event_position_area(x, y)

                if area == "board":
                    cell_x, cell_y = get_square_coordinates(x, y)
                    selected_cells.append((cell_x, cell_y))
                    if len(selected_cells) == 2:
                        switch_colors()
                if area == "player1" or area == "player2":
                    selected_card, selected_player_area = handle_card_click(
                        area,
                        (x, y),
                        player_card_rects,
                        selected_card,
                        selected_player_area,
                    )
                else:
                    selected_card = None
                    selected_player_area = None
        screen.fill(BACKGROUND_COLOR)
        draw_board(board.state)
        draw_card_areas(players_qty)
        draw_cards(players_qty, player_card_rects, selected_card, selected_player_area)
        pygame.display.flip()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
