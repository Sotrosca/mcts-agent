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

# Colores
BACKGROUND_COLOR = (100, 130, 130)
BOARD_BACKGROUND_COLOR = (40, 40, 40)
CARD_COLOR = (255, 255, 255)
BORDER_COLOR = (40, 40, 40)
SELECTED_CELL_BORDER_COLOR = (210, 210, 210)

# Dimensiones y posiciones de las áreas de las cartas
CARD_WIDTH, CARD_HEIGHT = 140, 350
CARDS_QTY = 3
BOARD_SIZE = 320  # El tablero será un cuadrado de 400x400
BOARD_POS = ((SCREEN_WIDTH - BOARD_SIZE) // 2, (SCREEN_HEIGHT - BOARD_SIZE) // 2)
SQUARE_SIZE = BOARD_SIZE // board.size[0]
MARGIN = 20  # Espacio adicional para evitar superposición

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Board setup

selected_cells = []

player1_card_rects = {}
player2_card_rects = {}


def draw_board(board_state):
    # board background
    background_rect = (BOARD_POS[0], BOARD_POS[1], BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, background_rect)
    board_image = [[COLORS[(cell.color - 1)] for cell in row] for row in board_state]
    for y, row in enumerate(board_image):
        for x, color in enumerate(row):
            if (x, y) in selected_cells:
                border_color = SELECTED_CELL_BORDER_COLOR
            else:
                border_color = BORDER_COLOR
            square_rect = square_rect = (
                BOARD_POS[0] + x * SQUARE_SIZE,
                BOARD_POS[1] + y * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )
            pygame.draw.rect(screen, color, square_rect, border_radius=10)

            # Dibujar el borde de la celda
            pygame.draw.rect(screen, border_color, square_rect, 3, border_radius=10)


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
        # for color in range(1, board.color_quantity + 1):
        #    find_figures(board_state_with_border, color)


def draw_card_areas(num_players):
    if num_players >= 1:
        # Jugador 1
        player1_pos = (
            BOARD_POS[0] - CARD_WIDTH - MARGIN,
            SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2,
        )
        pygame.draw.rect(screen, CARD_COLOR, (*player1_pos, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(
            screen, BORDER_COLOR, (*player1_pos, CARD_WIDTH, CARD_HEIGHT), 3
        )
    if num_players >= 2:
        # Jugador 2
        player2_pos = (
            BOARD_POS[0] + BOARD_SIZE + MARGIN,
            SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2,
        )
        pygame.draw.rect(screen, CARD_COLOR, (*player2_pos, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(
            screen, BORDER_COLOR, (*player2_pos, CARD_WIDTH, CARD_HEIGHT), 3
        )
    if num_players >= 3:
        # Jugador 3
        player3_pos = (
            SCREEN_WIDTH // 2 - CARD_HEIGHT // 2,
            BOARD_POS[1] - CARD_WIDTH - MARGIN,
        )  # Invertir las dimensiones
        pygame.draw.rect(screen, CARD_COLOR, (*player3_pos, CARD_HEIGHT, CARD_WIDTH))
        pygame.draw.rect(
            screen, BORDER_COLOR, (*player3_pos, CARD_HEIGHT, CARD_WIDTH), 3
        )
    if num_players == 4:
        # Jugador 4
        player4_pos = (
            SCREEN_WIDTH // 2 - CARD_HEIGHT // 2,
            BOARD_POS[1] + BOARD_SIZE + MARGIN,
        )  # Invertir las dimensiones
        pygame.draw.rect(screen, CARD_COLOR, (*player4_pos, CARD_HEIGHT, CARD_WIDTH))
        pygame.draw.rect(
            screen, BORDER_COLOR, (*player4_pos, CARD_HEIGHT, CARD_WIDTH), 3
        )


def draw_cards(
    num_players,
    player1_card_rects,
    player2_card_rects,
    selected_card,
    selected_player_area,
):

    if num_players >= 1:
        player1_cards = game.players[0].hand
        for i, card in player1_cards.items():
            card_pos = (
                BOARD_POS[0] - CARD_WIDTH - MARGIN,
                SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 + i * 120,
            )
            card_text = pygame.font.SysFont("Arial", 16).render(
                card.name, True, (0, 0, 0)
            )

            if i not in player1_card_rects:
                player1_card_rects[i] = pygame.Rect(*card_pos, CARD_WIDTH, 100)

            player_card_rect = player1_card_rects[i]

            border_color = (
                (255, 0, 0)
                if i == selected_card
                and game.player_turn == 0
                and selected_player_area == 0
                else BORDER_COLOR
            )

            pygame.draw.rect(screen, CARD_COLOR, player_card_rect)
            pygame.draw.rect(screen, border_color, player_card_rect, 3)
            screen.blit(card_text, (card_pos[0] + 10, card_pos[1] + 10))
    if num_players >= 2:
        player2_cards = game.players[0].hand
        for i, card in player2_cards.items():
            card_pos = (
                BOARD_POS[0] + BOARD_SIZE + MARGIN,
                SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 + i * 120,
            )
            card_text = pygame.font.SysFont("Arial", 16).render(
                card.name, True, (0, 0, 0)
            )
            if i not in player2_card_rects:
                player2_card_rects[i] = pygame.Rect(*card_pos, CARD_WIDTH, 100)

            player_card_rect = player2_card_rects[i]

            border_color = (
                (255, 0, 0)
                if i == selected_card
                and game.player_turn == 1
                and selected_player_area == 1
                else BORDER_COLOR
            )

            pygame.draw.rect(screen, CARD_COLOR, player_card_rect)
            pygame.draw.rect(screen, border_color, player_card_rect, 3)
            screen.blit(card_text, (card_pos[0] + 10, card_pos[1] + 10))
    if num_players >= 3:
        for i in range(CARDS_QTY):
            card_pos = (
                SCREEN_WIDTH // 2 - CARD_HEIGHT // 2 + i * 120,
                BOARD_POS[1] - CARD_WIDTH - MARGIN,
            )
            pygame.draw.rect(screen, CARD_COLOR, (*card_pos, 100, CARD_WIDTH))
            pygame.draw.rect(screen, BORDER_COLOR, (*card_pos, 100, CARD_WIDTH), 3)
    if num_players == 4:
        for i in range(CARDS_QTY):
            card_pos = (
                SCREEN_WIDTH // 2 - CARD_HEIGHT // 2 + i * 120,
                BOARD_POS[1] + BOARD_SIZE + MARGIN,
            )
            pygame.draw.rect(screen, CARD_COLOR, (*card_pos, 100, CARD_WIDTH))
            pygame.draw.rect(screen, BORDER_COLOR, (*card_pos, 100, CARD_WIDTH), 3)


def get_square_coordinates(mouse_x, mouse_y):
    if (
        BOARD_POS[0] <= mouse_x <= BOARD_POS[0] + BOARD_SIZE
        and BOARD_POS[1] <= mouse_y <= BOARD_POS[1] + BOARD_SIZE
    ):
        col = (mouse_x - BOARD_POS[0]) // SQUARE_SIZE
        row = (mouse_y - BOARD_POS[1]) // SQUARE_SIZE
        return col, row
    return None


def event_position_area(x, y):
    if (
        BOARD_POS[0] <= x <= BOARD_POS[0] + BOARD_SIZE
        and BOARD_POS[1] <= y <= BOARD_POS[1] + BOARD_SIZE
    ):
        return "board"
    if (
        BOARD_POS[0] - CARD_WIDTH - MARGIN <= x <= BOARD_POS[0]
        and SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
        <= y
        <= SCREEN_HEIGHT // 2 + CARD_HEIGHT // 2
    ):
        return "player1"
    if (
        BOARD_POS[0] + BOARD_SIZE
        <= x
        <= BOARD_POS[0] + BOARD_SIZE + CARD_WIDTH + MARGIN
        and SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
        <= y
        <= SCREEN_HEIGHT // 2 + CARD_HEIGHT // 2
    ):
        return "player2"
    return None


def handle_card_click(
    area,
    pos,
    player1_card_rects,
    player2_card_rects,
    selected_card,
    selected_player_area,
):
    if area == "player1":
        for i, rect in player1_card_rects.items():
            if rect.collidepoint(pos):
                selected_card = i
                selected_player_area = 0

    elif area == "player2":
        for i, rect in player2_card_rects.items():
            if rect.collidepoint(pos):
                selected_card = i
                selected_player_area = 1

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
                print(area)
                if area == "board":
                    cell_x, cell_y = get_square_coordinates(x, y)
                    selected_cells.append((cell_x, cell_y))
                    if len(selected_cells) == 2:
                        switch_colors()
                if area == "player1" or area == "player2":
                    selected_card, selected_player_area = handle_card_click(
                        area,
                        (x, y),
                        player1_card_rects,
                        player2_card_rects,
                        selected_card,
                        selected_player_area,
                    )
                else:
                    selected_card = None
                    selected_player_area = None

        screen.fill(BACKGROUND_COLOR)
        draw_board(board.state)

        # Dibujar las cartas del jugador y del adversario
        draw_card_areas(players_qty)

        draw_cards(
            players_qty,
            player1_card_rects,
            player2_card_rects,
            selected_card,
            selected_player_area,
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
