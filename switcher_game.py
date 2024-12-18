import sys

import pygame

from MCTSAgent.MCTSAgent import MontecarloPlayer
from Switcher.game import Config, Game
from Switcher.game.renderer import GameRenderer
from Switcher.game.state import ActionState
from Switcher.logic.figures import BoardFigure, figures
from Switcher.mcts_functions import (
    expansion_function,
    movement_choice_function,
    retropropagation_function,
    selection_function,
    simulation_function,
)
from Switcher.mcts_simulation import SwitcherSimulation


class GameUI:
    def __init__(self, game: Game):
        self.game = game
        self.simulation = SwitcherSimulation(game.logic)
        self.action_state = ActionState()
        self.game_renderer = GameRenderer(game, self.action_state)

    def get_square_coordinates(self, mouse_x, mouse_y):
        if self.game_renderer.board_rect.collidepoint(mouse_x, mouse_y):
            col = (mouse_x - self.game_renderer.board_rect.x) // (
                Config.BOARD_SIZE // self.game.board.size[0]
            )
            row = (mouse_y - self.game_renderer.board_rect.y) // (
                Config.BOARD_SIZE // self.game.board.size[0]
            )
            return col, row
        return None

    def event_position_area(self, x, y):
        if self.game_renderer.board_rect.collidepoint(x, y):
            return "board"
        if self.game_renderer.player1_hand_rect.collidepoint(x, y):
            return "player1_hand"
        if self.game_renderer.player2_hand_rect.collidepoint(x, y):
            return "player2_hand"
        if self.game_renderer.player1_figures_area_rect.collidepoint(x, y):
            return "player1_figures_area"
        if self.game_renderer.player2_figures_area_rect.collidepoint(x, y):
            return "player2_figures_area"
        return None

    def handle_card_click(self, area, pos):
        player_index = 0 if area == "player1_hand" else 1

        if self.game.logic.player_turn != player_index:
            self.action_state.selected_card = None
            self.action_state.selected_player_area = None
            self.action_state.selected_cells.clear()
            return

        for i, rect in self.game_renderer.player_card_rects[player_index].items():
            if rect.collidepoint(pos):
                if self.game.logic.players[player_index].hand[i] is None or (
                    self.action_state.selected_card == i
                    and self.action_state.selected_player_area == player_index
                ):
                    self.action_state.selected_card = None
                    self.action_state.selected_player_area = None
                else:
                    self.action_state.selected_card = i
                    self.action_state.selected_player_area = player_index
                break
        return self.action_state.selected_card, self.action_state.selected_player_area

    def handle_figure_click(self, area, pos):
        player_index = 0 if area == "player1_figures_area" else 1
        player_figures = self.game.get_player_figures(player_index)
        for i, rect in self.game_renderer.player_figures_rect[player_index].items():
            if rect.collidepoint(pos):
                if (
                    self.game.logic.players[player_index].figures_slots[i] is None
                    or (
                        self.action_state.selected_figure_idx == i
                        and self.action_state.selected_figure_area == player_index
                    )
                    or (
                        self.game.player_is_blocked(player_index)
                        and player_index != self.game.logic.player_turn
                    )
                    or (self.game.get_banned_player_figures(player_index)[i])
                    or not self.game_renderer.playable_figure_in_board(
                        player_figures[i]
                    )
                ):
                    self.action_state.selected_figure_idx = None
                    self.action_state.selected_figure_area = None
                else:
                    self.action_state.selected_figure_idx = i
                    self.action_state.selected_figure_area = player_index
                break
        return (
            self.action_state.selected_figure_idx,
            self.action_state.selected_figure_area,
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # Create a profiler

                ia_player = MontecarloPlayer(
                    original_simulation=self.simulation,
                    selection_function=selection_function,
                    expansion_function=expansion_function,
                    retropropagation_function=retropropagation_function,
                    simulation_function=simulation_function,
                    movement_choice_function=movement_choice_function,
                )
                # self.simulation.set_initial_state()
                # possible_actions = self.simulation.get_possible_actions()
                # [print(f"Action {str(action)}") for action in possible_actions]
                # self.clean_selected()
                # pr = cProfile.Profile()
                # pr.enable()
                print(len(ia_player.action_tree.childs))
                qty_possible_actions = len(ia_player.action_tree.childs)
                ia_player.explore_action_tree(
                    epochs=qty_possible_actions * 3, log=False
                )
                best_move = ia_player.get_best_move()
                print(f"Best move: {best_move}")
                print(best_move.action)
                # Disable the profiler
                # pr.disable()

                # Create a stream to hold the profiling results
                # s = io.StringIO()
                # ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.TIME)
                # ps.print_stats()
                # Write the profiling results to a file
                # with open("profiling_results_2.txt", "w") as f:
                #    f.write(s.getvalue())
                self.action_state.board_figures = game.find_board_figures()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                area = self.event_position_area(x, y)

                if self.game_renderer.pass_turn_button.collidepoint(x, y):
                    self.game.pass_turn()
                    self.action_state.clean_selected()
                elif area == "board" and self.is_figure_selected():
                    cell_x, cell_y = self.get_square_coordinates(x, y)
                    figure_to_match_cells = (
                        self.game_renderer.cells_to_match_with_selected_figure()
                    )
                    if (cell_y, cell_x) in figure_to_match_cells:
                        game.match_figure(
                            self.action_state.selected_figure_area,
                            self.action_state.selected_figure_idx,
                            cell_y,
                            cell_x,
                            self.action_state.board_figures,
                        )
                        self.action_state.clean_selected()
                        print("Figure matched")
                elif (
                    area == "board"
                    and self.action_state.selected_card is not None
                    and self.action_state.selected_player_area is not None
                ):
                    cell_x, cell_y = self.get_square_coordinates(x, y)
                    print(cell_x, cell_y)

                    if (cell_x, cell_y) in self.action_state.selected_cells:
                        self.action_state.selected_cells.remove((cell_x, cell_y))
                        self.action_state.possible_switches = None

                    if len(self.action_state.selected_cells) == 0 or (
                        len(self.action_state.selected_cells) == 1
                        and (cell_x, cell_y) not in self.action_state.possible_switches
                    ):
                        self.action_state.selected_cells.clear()
                        self.action_state.selected_cells.append((cell_x, cell_y))
                        possible_switches = self.game.possible_switches(
                            (cell_x, cell_y), self.action_state.selected_card
                        )
                        self.action_state.possible_switches = possible_switches
                    elif len(self.action_state.selected_cells) == 1:
                        self.action_state.selected_cells.append((cell_x, cell_y))
                        self.game.switch_colors(
                            self.action_state.selected_cells,
                            self.action_state.selected_card,
                        )
                        self.action_state.board_figures = self.game.find_board_figures()
                        self.action_state.clean_selected()

                elif area == "player1_hand" or area == "player2_hand":
                    self.handle_card_click(area, (x, y))
                    self.action_state.selected_move = self.action_state.selected_card

                elif area == "player1_figures_area" or area == "player2_figures_area":
                    self.handle_figure_click(area, (x, y))

        return True

    def is_figure_selected(self):
        return (
            self.action_state.selected_figure_idx is not None
            and self.action_state.selected_figure_area is not None
        )

    def main_loop(self):

        running = True

        self.action_state.board_figures = game.find_board_figures()
        while running:
            player_winner = self.game.check_player_winner()
            running = self.handle_events()
            self.game_renderer.screen.fill(Config.BACKGROUND_COLOR)
            self.game_renderer.draw_board()
            self.game_renderer.draw_card_areas()
            self.game_renderer.draw_cards()
            self.game_renderer.draw_pass_turn_button()
            self.game_renderer.draw_players_figures()
            self.game_renderer.draw_game_info()
            if player_winner is not None:
                self.game_renderer.draw_player_winner(player_winner)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    pygame.init()
    game = Game()
    ui = GameUI(game)
    ui.main_loop()
