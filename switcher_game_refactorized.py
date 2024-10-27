# Python
import sys

import pygame

from Switcher.game import Config, Game
from Switcher.logic.figures import find_figures


class GameUI:
    def __init__(self, game: Game):
        self.game = game
        pygame.init()
        self.screen = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        self.board_rect = pygame.Rect(
            (Config.SCREEN_WIDTH - Config.BOARD_SIZE) // 2,
            (Config.SCREEN_HEIGHT - Config.BOARD_SIZE) // 2,
            Config.BOARD_SIZE,
            Config.BOARD_SIZE,
        )
        self.player_card_rects = [{} for _ in range(game.players_qty)]
        self.selected_card = None
        self.selected_player_area = None

        # Definir player1_rect y player2_rect
        self.player1_rect = pygame.Rect(
            self.board_rect.x - Config.CARD_WIDTH - Config.MARGIN,
            Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            Config.CARD_WIDTH,
            Config.CARD_HEIGHT,
        )
        self.player2_rect = pygame.Rect(
            self.board_rect.x + Config.BOARD_SIZE + Config.MARGIN,
            Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            Config.CARD_WIDTH,
            Config.CARD_HEIGHT,
        )

    def draw_board(self):
        pygame.draw.rect(self.screen, Config.BOARD_BACKGROUND_COLOR, self.board_rect)
        board_image = [
            [Config.COLORS[(cell.color - 1)] for cell in row]
            for row in self.game.board.state
        ]
        for y, row in enumerate(board_image):
            for x, color in enumerate(row):
                border_color = (
                    Config.SELECTED_CELL_BORDER_COLOR
                    if (x, y) in self.game.selected_cells
                    else Config.BORDER_COLOR
                )
                square_rect = pygame.Rect(
                    self.board_rect.x
                    + x * (Config.BOARD_SIZE // self.game.board.size[0]),
                    self.board_rect.y
                    + y * (Config.BOARD_SIZE // self.game.board.size[0]),
                    Config.BOARD_SIZE // self.game.board.size[0],
                    Config.BOARD_SIZE // self.game.board.size[0],
                )
                pygame.draw.rect(self.screen, color, square_rect, border_radius=10)
                pygame.draw.rect(
                    self.screen, border_color, square_rect, 3, border_radius=10
                )

    def draw_card_area(self, player_index, pos):
        pygame.draw.rect(
            self.screen,
            Config.CARD_COLOR,
            (*pos, Config.CARD_WIDTH, Config.CARD_HEIGHT),
        )
        pygame.draw.rect(
            self.screen,
            Config.BORDER_COLOR,
            (*pos, Config.CARD_WIDTH, Config.CARD_HEIGHT),
            3,
        )

    def draw_card_areas(self):
        positions = [
            (
                self.board_rect.x - Config.CARD_WIDTH - Config.MARGIN,
                Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            ),
            (
                self.board_rect.x + Config.BOARD_SIZE + Config.MARGIN,
                Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            ),
        ]
        for i in range(self.game.players_qty):
            self.draw_card_area(i, positions[i])

    def draw_cards(self):
        for player_index in range(self.game.players_qty):
            player_cards = self.game.logic.players[player_index].hand
            for i, card in player_cards.items():
                card_pos = self.get_card_position(player_index, i)
                card_text = pygame.font.SysFont("Arial", 16).render(
                    card.name, True, (0, 0, 0)
                )
                if i not in self.player_card_rects[player_index]:
                    self.player_card_rects[player_index][i] = pygame.Rect(
                        *card_pos, Config.CARD_WIDTH, 100
                    )
                player_card_rect = self.player_card_rects[player_index][i]
                border_color = (
                    (255, 0, 0)
                    if i == self.selected_card
                    and self.selected_player_area == player_index
                    and player_index == self.game.logic.player_turn
                    else Config.BORDER_COLOR
                )
                pygame.draw.rect(self.screen, Config.CARD_COLOR, player_card_rect)
                pygame.draw.rect(self.screen, border_color, player_card_rect, 3)
                self.screen.blit(card_text, (card_pos[0] + 10, card_pos[1] + 10))

    def get_card_position(self, player_index, card_index):
        if player_index == 0:
            return (
                self.board_rect.x - Config.CARD_WIDTH - Config.MARGIN,
                Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2 + card_index * 120,
            )
        elif player_index == 1:
            return (
                self.board_rect.x + Config.BOARD_SIZE + Config.MARGIN,
                Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2 + card_index * 120,
            )

    def get_square_coordinates(self, mouse_x, mouse_y):
        if self.board_rect.collidepoint(mouse_x, mouse_y):
            col = (mouse_x - self.board_rect.x) // (
                Config.BOARD_SIZE // self.game.board.size[0]
            )
            row = (mouse_y - self.board_rect.y) // (
                Config.BOARD_SIZE // self.game.board.size[0]
            )
            return col, row
        return None

    def event_position_area(self, x, y):
        if self.board_rect.collidepoint(x, y):
            return "board"
        if self.player1_rect.collidepoint(x, y):
            return "player1"
        if self.player2_rect.collidepoint(x, y):
            return "player2"
        return None

    def handle_card_click(self, area, pos):
        player_index = 0 if area == "player1" else 1

        if self.game.logic.player_turn != player_index:
            self.selected_card = None
            self.selected_player_area = None
            return

        for i, rect in self.player_card_rects[player_index].items():
            if rect.collidepoint(pos):
                if (
                    self.selected_card == i
                    and self.selected_player_area == player_index
                ):
                    self.selected_card = None
                    self.selected_player_area = None
                else:
                    self.selected_card = i
                    self.selected_player_area = player_index
                break
        return self.selected_card, self.selected_player_area

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                area = self.event_position_area(x, y)

                if area == "board":
                    cell_x, cell_y = self.get_square_coordinates(x, y)
                    self.game.selected_cells.append((cell_x, cell_y))
                    if len(self.game.selected_cells) == 2:
                        self.game.switch_colors()

                elif area == "player1" or area == "player2":
                    self.handle_card_click(area, (x, y))
                    self.game.selected_move = self.selected_card
        return True

    def main_loop(self):
        running = True
        while running:
            running = self.handle_events()
            self.screen.fill(Config.BACKGROUND_COLOR)
            self.draw_board()
            self.draw_card_areas()
            self.draw_cards()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    print(game.logic.player_turn)
    ui = GameUI(game)
    ui.main_loop()
