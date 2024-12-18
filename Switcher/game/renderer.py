# renderer.py

import pygame
import pygame.draw

from Switcher.game import Config, Game
from Switcher.game.state import ActionState
from Switcher.logic.figures import figures


class GameRenderer:
    def __init__(self, game, actions_state: ActionState):
        self.game: Game = game
        self.actions_state = actions_state

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

        self.player1_hand_rect, self.player2_hand_rect = self.create_player_hand_rects()
        self.pass_turn_button = pygame.Rect(
            (Config.SCREEN_WIDTH - 100) // 2, Config.SCREEN_HEIGHT - 50, 100, 30
        )
        self.player1_figures_area_rect, self.player2_figures_area_rect = (
            self.create_player_figures_area_rects()
        )

        self.player_figures_rect = [{} for _ in range(game.players_qty)]

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

    def draw_board(self):
        board_rect = self.board_rect
        pygame.draw.rect(self.screen, Config.BOARD_BACKGROUND_COLOR, board_rect)
        board_image = self.get_board_image()

        all_player_figures = self.game.get_all_player_figure_names()

        figure_to_match_cells = self.cells_to_match_with_selected_figure()

        playable_board_figures = self.get_playable_board_figures()

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
                    for figure in playable_board_figures:
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
                        if (x, y) in self.actions_state.selected_cells
                        or player_board_figure_cell
                        else (
                            Config.POSSIBLE_SWITCHES_BORDER_COLOR
                            if self.actions_state.possible_switches is not None
                            and (x, y) in self.actions_state.possible_switches
                            else Config.BORDER_COLOR
                        )
                    )
                    border_radius = (
                        Config.SELECTED_CELL_BORDER_RADIUS
                        if (x, y) in self.actions_state.selected_cells
                        or self.actions_state.possible_switches is not None
                        and (x, y) in self.actions_state.possible_switches
                        else Config.BORDER_RADIUS
                    )

                square_rect = pygame.Rect(
                    board_rect.x + x * (Config.BOARD_SIZE // self.game.board.size[0]),
                    board_rect.y + y * (Config.BOARD_SIZE // self.game.board.size[0]),
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

    def draw_card_area(self, pos):
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
        for pos in positions:
            self.draw_card_area(pos)

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
                    if i == self.actions_state.selected_card
                    and self.actions_state.selected_player_area == player_index
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

    def draw_figure(self, figure, top_left_x, top_left_y):
        for i, row in enumerate(figure):
            for j, cell in enumerate(row):
                if cell == 1:
                    pygame.draw.rect(
                        self.screen,
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
                        self.screen,
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

    def _draw_player_figures(
        self, player_index, player_figures_area_rect, player_figures_rect
    ):
        player_figures = self.game.get_player_figures(player_index)
        player_banned_figures = self.game.get_banned_player_figures(player_index)
        for i, figure_name in player_figures.items():
            is_banned = player_banned_figures[i]
            x = player_figures_area_rect.x + (i % 2) * (
                player_figures_area_rect.width // 2
            )
            y = player_figures_area_rect.y + (i // 2) * (
                player_figures_area_rect.height // 2
            )

            if i not in player_figures_rect[player_index]:
                player_figures_rect[player_index][i] = pygame.Rect(
                    x,
                    y,
                    player_figures_area_rect.width // 2,
                    player_figures_area_rect.height // 2,
                )
            figure_rect = player_figures_rect[player_index][i]

            figure_background_color = (
                Config.FIGURE_ON_BOARD_BACKGROUND_COLOR
                if self.playable_figure_in_board(figure_name)
                else Config.FIGURE_BACKGROUND_COLOR
            )

            pygame.draw.rect(self.screen, figure_background_color, figure_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), figure_rect, 3)

            figure_matrix = figures.get(figure_name)
            if figure_matrix:
                figure_width = len(figure_matrix[0]) * Config.CELL_SIZE
                figure_height = len(figure_matrix) * Config.CELL_SIZE
                offset_x = (player_figures_area_rect.width // 2 - figure_width) // 2
                offset_y = (player_figures_area_rect.height // 2 - figure_height) // 2
                self.draw_figure(figure_matrix, x + offset_x, y + offset_y)
            if is_banned:
                # Draw a red cross over the figure
                pygame.draw.line(
                    self.screen,
                    (255, 0, 0),
                    (x, y),
                    (x + figure_rect.width, y + figure_rect.height),
                    3,
                )

    def draw_players_figures(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.player1_figures_area_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.player2_figures_area_rect)

        self._draw_player_figures(
            0, self.player1_figures_area_rect, self.player_figures_rect
        )
        self._draw_player_figures(
            1, self.player2_figures_area_rect, self.player_figures_rect
        )

    def draw_pass_turn_button(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.pass_turn_button)
        font = pygame.font.SysFont("Arial", 16)
        text = font.render("Pass Turn", True, (0, 0, 0))
        self.screen.blit(
            text, (self.pass_turn_button.x + 10, self.pass_turn_button.y + 5)
        )

    def draw_game_info(self):
        font = pygame.font.SysFont("Arial", 16)

        # Player turn text
        player_turn_text = font.render(
            f"Player {self.game.logic.player_turn + 1} turn", True, (0, 0, 0)
        )
        player_turn_rect = player_turn_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 10)
        )
        self.screen.blit(player_turn_text, player_turn_rect)

        # Remaining figure cards for each player
        player1_figures_remaining = self.game.player_figures_deck_qty(0)
        player2_figures_remaining = self.game.player_figures_deck_qty(1)
        player1_figures_text = font.render(
            f"Player 1 Figures: {player1_figures_remaining}", True, (0, 0, 0)
        )
        player2_figures_text = font.render(
            f"Player 2 Figures: {player2_figures_remaining}", True, (0, 0, 0)
        )
        player1_figures_rect = player1_figures_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 30)
        )
        player2_figures_rect = player2_figures_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 50)
        )
        self.screen.blit(player1_figures_text, player1_figures_rect)
        self.screen.blit(player2_figures_text, player2_figures_rect)

        # Last played color
        last_color = self.game.last_color_played()
        last_color_text = font.render("Last Color Played:", True, (0, 0, 0))
        last_color_rect = last_color_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2 - 50, 70)
        )
        self.screen.blit(last_color_text, last_color_rect)

        if last_color is not None:
            color = Config.COLORS[last_color - 1]
            pygame.draw.circle(
                self.screen, color, (Config.SCREEN_WIDTH // 2 + 50, 70), 10
            )
        else:
            pygame.draw.circle(
                self.screen, (255, 255, 255), (Config.SCREEN_WIDTH // 2 + 50, 70), 10
            )

    def draw_player_winner(self, player_winner):
        font = pygame.font.SysFont("Arial", 40)
        text = font.render(f"Player {player_winner} wins!", True, (0, 0, 0))
        text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, 100))
        self.screen.blit(text, text_rect)

    def get_board_image(self):
        return [
            [Config.COLORS[(cell.color - 1)] for cell in row]
            for row in self.game.board.state
        ]

    def cells_to_match_with_selected_figure(self):
        if not self.is_figure_selected():
            return []

        figure_name_to_match = self.game.get_player_figures(
            self.actions_state.selected_figure_area
        )[self.actions_state.selected_figure_idx]

        return self.cells_to_match_with_figure(figure_name_to_match)

    def cells_to_match_with_figure(self, figure_name):
        figure_to_match_cells = [
            cell
            for figure in self.actions_state.board_figures
            if figure.name == figure_name
            and figure.color != self.game.last_color_played()
            for cell in figure.cells
        ]
        return figure_to_match_cells

    def playable_figure_in_board(self, figure_name):
        last_color_played = self.game.last_color_played()
        for figure in self.actions_state.board_figures:
            if figure.name == figure_name and last_color_played != figure.color:
                return True
        return False

    def get_playable_board_figures(self):
        last_color_played = self.game.last_color_played()
        return [
            figure
            for figure in self.actions_state.board_figures
            if last_color_played != figure.color
        ]

    def is_figure_selected(self):
        return (
            self.actions_state.selected_figure_idx is not None
            and self.actions_state.selected_figure_area is not None
        )

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
