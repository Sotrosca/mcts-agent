# Python
import sys

import pygame

from Switcher.game import Config, Game
from Switcher.logic.figures import BoardFigure, figures
from Switcher.player.player_move import MatchFigureMove


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
        self.selected_figure_idx = None
        self.selected_figure_area = None
        self.selected_cells = []
        self.possible_switches = None
        self.board_figures: list[BoardFigure] = []

        self.player1_hand_rect, self.player2_hand_rect = self.create_player_hand_rects()
        self.pass_turn_button = pygame.Rect(
            (Config.SCREEN_WIDTH - 100) // 2, Config.SCREEN_HEIGHT - 50, 100, 30
        )
        self.player1_figures_area_rect, self.player2_figures_area_rect = (
            self.create_player_figures_area_rects()
        )

        self.player_figures_rect = [{} for _ in range(game.players_qty)]

    def clean_selected(self):
        self.selected_card = None
        self.selected_player_area = None
        self.selected_figure_idx = None
        self.selected_figure_area = None
        self.selected_cells.clear()
        self.possible_switches = None

    def create_player_hand_rects(self):
        player1_rect = pygame.Rect(
            self.board_rect.x - Config.CARD_WIDTH - Config.MARGIN,
            Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            Config.CARD_WIDTH,
            Config.CARD_HEIGHT,
        )
        player2_rect = pygame.Rect(
            self.board_rect.x + Config.BOARD_SIZE + Config.MARGIN,
            Config.SCREEN_HEIGHT // 2 - Config.CARD_HEIGHT // 2,
            Config.CARD_WIDTH,
            Config.CARD_HEIGHT,
        )
        return player1_rect, player2_rect

    def create_player_figures_area_rects(self):
        player1_figures_area_rect = pygame.Rect(
            self.board_rect.x - Config.CARD_WIDTH - Config.MARGIN,
            self.player1_hand_rect.y - 160,
            Config.CARD_WIDTH,
            160,
        )
        player2_figures_area_rect = pygame.Rect(
            self.board_rect.x + Config.BOARD_SIZE + Config.MARGIN,
            self.player2_hand_rect.y - 160,
            Config.CARD_WIDTH,
            160,
        )
        return player1_figures_area_rect, player2_figures_area_rect

    def cells_to_match_with_selected_figure(self):

        if not self.is_figure_selected():
            return []

        figure_name_to_match = self.game.get_player_figures(self.selected_figure_area)[
            self.selected_figure_idx
        ]

        return self.cells_to_match_with_figure(figure_name_to_match)

    def cells_to_match_with_figure(self, figure_name):
        figure_to_match_cells = [
            cell
            for figure in self.board_figures
            if figure.name == figure_name
            for cell in figure.cells
        ]
        return figure_to_match_cells

    def get_board_image(self):
        return [
            [Config.COLORS[(cell.color - 1)] for cell in row]
            for row in self.game.board.state
        ]

    def draw_board(self):
        pygame.draw.rect(self.screen, Config.BOARD_BACKGROUND_COLOR, self.board_rect)
        board_image = self.get_board_image()

        all_player_figures = self.game.get_all_player_figure_names()

        figure_to_match_cells = self.cells_to_match_with_selected_figure()

        for y, row in enumerate(board_image):
            for x, color in enumerate(row):
                if len(figure_to_match_cells) > 0:
                    if (y, x) in figure_to_match_cells:
                        color = color
                        border_color = Config.BORDER_COLOR
                        border_radius = Config.BORDER_RADIUS
                    else:
                        color = Config.board_figure_color(color)
                        border_color = Config.BORDER_COLOR
                        border_radius = Config.BORDER_RADIUS

                else:
                    player_board_figure_cell = False
                    for figure in self.board_figures:
                        if (y, x) in figure.cells and figure.name in all_player_figures:
                            player_board_figure_cell = True
                            break

                    color = (
                        color
                        if not player_board_figure_cell
                        else Config.board_figure_color(color)
                    )

                    border_color = (
                        Config.SELECTED_CELL_BORDER_COLOR
                        if (x, y) in self.selected_cells or player_board_figure_cell
                        else (
                            Config.POSSIBLE_SWITCHES_BORDER_COLOR
                            if self.possible_switches is not None
                            and (x, y) in self.possible_switches
                            else Config.BORDER_COLOR
                        )
                    )
                    border_radius = (
                        Config.SELECTED_CELL_BORDER_RADIUS
                        if (x, y) in self.selected_cells
                        or self.possible_switches is not None
                        and (x, y) in self.possible_switches
                        else Config.BORDER_RADIUS
                    )

                square_rect = pygame.Rect(
                    self.board_rect.x
                    + x * (Config.BOARD_SIZE // self.game.board.size[0]),
                    self.board_rect.y
                    + y * (Config.BOARD_SIZE // self.game.board.size[0]),
                    Config.BOARD_SIZE // self.game.board.size[0],
                    Config.BOARD_SIZE // self.game.board.size[0],
                )
                pygame.draw.rect(
                    self.screen, color, square_rect, border_radius=border_radius
                )
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    square_rect,
                    3,
                    border_radius=border_radius,
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
                name = card.name if card is not None else "None"
                card_text = pygame.font.SysFont("Arial", 16).render(
                    name, True, (0, 0, 0)
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

                color = (
                    Config.EMPTY_CARD_COLOR
                    if card is None
                    else (
                        Config.CURRENT_PLAYER_CARD_COLOR
                        if player_index == self.game.logic.player_turn
                        else Config.CARD_COLOR
                    )
                )

                pygame.draw.rect(self.screen, color, player_card_rect)
                pygame.draw.rect(self.screen, border_color, player_card_rect, 3)
                self.screen.blit(card_text, (card_pos[0] + 10, card_pos[1] + 10))

    def draw_figure(self, screen, figure, top_left_x, top_left_y):
        for i, row in enumerate(figure):
            for j, cell in enumerate(row):
                if cell == 1:
                    pygame.draw.rect(
                        screen,
                        Config.FIGURE_COLOR,
                        pygame.Rect(
                            top_left_x + j * Config.CELL_SIZE,
                            top_left_y + i * Config.CELL_SIZE,
                            Config.CELL_SIZE,
                            Config.CELL_SIZE,
                        ),
                        border_radius=2,
                    )
                    # draw border
                    pygame.draw.rect(
                        screen,
                        (40, 40, 40),
                        pygame.Rect(
                            top_left_x + j * Config.CELL_SIZE,
                            top_left_y + i * Config.CELL_SIZE,
                            Config.CELL_SIZE,
                            Config.CELL_SIZE,
                        ),
                        1,
                        border_radius=2,
                    )

    def figure_in_board(self, figure_name):
        for figure in self.board_figures:
            if figure.name == figure_name:
                return True
        return False

    def draw_player_figures(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.player1_figures_area_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.player2_figures_area_rect)

        # Draw player 1 figures
        player1_figures = self.game.get_player_figures(0)

        for slot_idx, figure_name in player1_figures.items():
            x = self.player1_figures_area_rect.x + (slot_idx % 2) * (
                self.player1_figures_area_rect.width // 2
            )
            y = self.player1_figures_area_rect.y + (slot_idx // 2) * (
                self.player1_figures_area_rect.height // 2
            )

            if slot_idx not in self.player_figures_rect[0]:
                self.player_figures_rect[0][slot_idx] = pygame.Rect(
                    x,
                    y,
                    self.player1_figures_area_rect.width // 2,
                    self.player1_figures_area_rect.height // 2,
                )
            figure_rect = self.player_figures_rect[0][slot_idx]

            figure_background_color = (
                Config.FIGURE_ON_BOARD_BACKGROUND_COLOR
                if self.figure_in_board(figure_name)
                else Config.FIGURE_BACKGROUND_COLOR
            )
            pygame.draw.rect(self.screen, figure_background_color, figure_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), figure_rect, 3)
            figure_matrix = figures.get(figure_name)
            if figure_matrix:
                figure_width = len(figure_matrix[0]) * Config.CELL_SIZE
                figure_height = len(figure_matrix) * Config.CELL_SIZE
                offset_x = (figure_rect.width - figure_width) // 2
                offset_y = (figure_rect.height - figure_height) // 2
                self.draw_figure(self.screen, figure_matrix, x + offset_x, y + offset_y)

        # Draw player 2 figures
        player2_figures = self.game.get_player_figures(1)
        for slot_idx, figure_name in player2_figures.items():
            x = self.player2_figures_area_rect.x + (slot_idx % 2) * (
                self.player2_figures_area_rect.width // 2
            )
            y = self.player2_figures_area_rect.y + (slot_idx // 2) * (
                self.player2_figures_area_rect.height // 2
            )
            if slot_idx not in self.player_figures_rect[1]:
                self.player_figures_rect[1][slot_idx] = pygame.Rect(
                    x,
                    y,
                    self.player2_figures_area_rect.width // 2,
                    self.player2_figures_area_rect.height // 2,
                )
            figure_rect = self.player_figures_rect[1][slot_idx]

            figure_background_color = (
                Config.FIGURE_ON_BOARD_BACKGROUND_COLOR
                if self.figure_in_board(figure_name)
                else Config.FIGURE_BACKGROUND_COLOR
            )

            pygame.draw.rect(self.screen, figure_background_color, figure_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), figure_rect, 3)
            figure_matrix = figures.get(figure_name)
            if figure_matrix:
                figure_width = len(figure_matrix[0]) * Config.CELL_SIZE
                figure_height = len(figure_matrix) * Config.CELL_SIZE
                offset_x = (figure_rect.width - figure_width) // 2
                offset_y = (figure_rect.height - figure_height) // 2
                self.draw_figure(self.screen, figure_matrix, x + offset_x, y + offset_y)

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
        if self.player1_hand_rect.collidepoint(x, y):
            return "player1_hand"
        if self.player2_hand_rect.collidepoint(x, y):
            return "player2_hand"
        if self.player1_figures_area_rect.collidepoint(x, y):
            return "player1_figures_area"
        if self.player2_figures_area_rect.collidepoint(x, y):
            return "player2_figures_area"
        return None

    def handle_card_click(self, area, pos):
        player_index = 0 if area == "player1_hand" else 1

        if self.game.logic.player_turn != player_index:
            self.selected_card = None
            self.selected_player_area = None
            self.selected_cells.clear()
            return

        for i, rect in self.player_card_rects[player_index].items():
            if rect.collidepoint(pos):
                if self.game.logic.players[player_index].hand[i] is None or (
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

    def handle_figure_click(self, area, pos):
        player_index = 0 if area == "player1_figures_area" else 1
        player_figures = self.game.get_player_figures(player_index)
        for i, rect in self.player_figures_rect[player_index].items():
            if rect.collidepoint(pos):
                if (
                    self.game.logic.players[player_index].figures_slots[i] is None
                    or (
                        self.selected_figure_idx == i
                        and self.selected_figure_area == player_index
                    )
                    or not self.figure_in_board(player_figures[i])
                ):
                    self.selected_figure_idx = None
                    self.selected_figure_area = None
                else:
                    self.selected_figure_idx = i
                    self.selected_figure_area = player_index
                break
        return self.selected_figure_idx, self.selected_figure_area

    def draw_pass_turn_button(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.pass_turn_button)
        font = pygame.font.SysFont("Arial", 16)
        text = font.render("Pass Turn", True, (0, 0, 0))
        self.screen.blit(
            text, (self.pass_turn_button.x + 10, self.pass_turn_button.y + 5)
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                area = self.event_position_area(x, y)

                if self.pass_turn_button.collidepoint(x, y):
                    self.game.pass_turn()
                    self.clean_selected()
                elif area == "board" and self.is_figure_selected():
                    cell_x, cell_y = self.get_square_coordinates(x, y)
                    figure_to_match_cells = self.cells_to_match_with_selected_figure()
                    if (cell_y, cell_x) in figure_to_match_cells:
                        game.match_figure(
                            self.selected_figure_area,
                            self.selected_figure_idx,
                            cell_y,
                            cell_x,
                            self.board_figures,
                        )
                elif (
                    area == "board"
                    and self.selected_card is not None
                    and self.selected_player_area is not None
                ):
                    cell_x, cell_y = self.get_square_coordinates(x, y)

                    if (cell_x, cell_y) in self.selected_cells:
                        self.selected_cells.remove((cell_x, cell_y))
                        self.possible_switches = None

                    if len(self.selected_cells) == 0 or (
                        len(self.selected_cells) == 1
                        and (cell_x, cell_y) not in self.possible_switches
                    ):
                        self.selected_cells.clear()
                        self.selected_cells.append((cell_x, cell_y))
                        possible_switches = self.game.possible_switches(
                            (cell_x, cell_y), self.selected_card
                        )
                        self.possible_switches = possible_switches
                    elif len(self.selected_cells) == 1:
                        self.selected_cells.append((cell_x, cell_y))
                        self.game.switch_colors(self.selected_cells, self.selected_card)
                        self.board_figures = self.game.find_board_figures()
                        self.selected_cells.clear()
                        self.possible_switches = None
                        self.selected_card = None

                elif area == "player1_hand" or area == "player2_hand":
                    self.handle_card_click(area, (x, y))
                    self.selected_move = self.selected_card

                elif area == "player1_figures_area" or area == "player2_figures_area":
                    self.handle_figure_click(area, (x, y))

        return True

    def is_figure_selected(self):
        return (
            self.selected_figure_idx is not None
            and self.selected_figure_area is not None
        )

    def main_loop(self):
        running = True

        self.board_figures = game.find_board_figures()
        while running:
            running = self.handle_events()
            self.screen.fill(Config.BACKGROUND_COLOR)
            self.draw_board()
            self.draw_card_areas()
            self.draw_cards()
            self.draw_pass_turn_button()
            self.draw_player_figures()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    ui = GameUI(game)
    ui.main_loop()
