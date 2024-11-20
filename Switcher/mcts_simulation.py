import copy

from Switcher.logic import Switcher
from Switcher.logic.figures import BoardFigure
from Switcher.logic.moves import SwitchMovementCard
from Switcher.player.player import Player
from Switcher.player.player_move import MatchFigureMove, PassMove, SwitchMove


class SwitchCells:
    def __init__(self, x1, y1, x2, y2, move_card_slot=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.move_card_slot = move_card_slot

    def __eq__(self, other):
        return (
            self.x1 == other.x1
            and self.y1 == other.y1
            and self.x2 == other.x2
            and self.y2 == other.y2
        ) or (
            self.x1 == other.x2
            and self.y1 == other.y2
            and self.x2 == other.x1
            and self.y2 == other.y1
        )

    def __str__(self):
        return f"Switch cells: ({self.x1}, {self.y1}) -> ({self.x2}, {self.y2})"


class SwitcherSimulation:

    def __init__(self, logic):
        self.logic: Switcher = logic
        self.initial_state = copy.deepcopy(self.get_state())

    def player_winner(self):
        return self.logic.winner

    def get_state(self):
        ret = {
            "board_state": self.logic.board.state,
            # "figures_deck": self.logic.figures_deck,
            "moves_deck": self.logic.moves_deck,
            "moves_discard": self.logic.moves_discard,
            "last_color_played": self.logic.last_color_played,
            "player_turn": self.logic.player_turn,
            "turn": self.logic.turn,
            "winner": self.logic.winner,
            "player1_state": {
                "figures_slots": self.logic.players[0].figures_slots,
                "figures_played": self.logic.players[0].figures_played,
                "figures_blocked": self.logic.players[0].figures_blocked,
                "figures_deck": self.logic.players[0].figures_deck,
                "hand": self.logic.players[0].hand,
                "hand_size": self.logic.players[0].hand_size,
                "is_blocked": self.logic.players[0].is_blocked,
            },
            "player2_state": {
                "figures_slots": self.logic.players[1].figures_slots,
                "figures_played": self.logic.players[1].figures_played,
                "figures_blocked": self.logic.players[1].figures_blocked,
                "figures_deck": self.logic.players[1].figures_deck,
                "hand": self.logic.players[1].hand,
                "hand_size": self.logic.players[1].hand_size,
                "is_blocked": self.logic.players[1].is_blocked,
            },
        }
        return ret

    def set_state(self, state_dict: dict):
        state_dict = copy.deepcopy(state_dict)
        self.logic.board.state = state_dict.get("board_state")
        # self.logic.figures_deck = state_dict.get("figures_deck")
        self.logic.moves_deck = self.logic.shuffle_deck(state_dict.get("moves_deck"))
        self.logic.moves_discard = state_dict.get("moves_discard")
        self.logic.last_color_played = state_dict.get("last_color_played")
        self.logic.player_turn = state_dict.get("player_turn")
        self.logic.current_player = self.logic.players[self.logic.player_turn]
        self.logic.turn = state_dict.get("turn")
        self.logic.winner = state_dict.get("winner")
        self.logic.players[0].figures_slots = state_dict.get("player1_state").get(
            "figures_slots"
        )
        self.logic.players[0].figures_played = state_dict.get("player1_state").get(
            "figures_played"
        )
        self.logic.players[0].figures_blocked = state_dict.get("player1_state").get(
            "figures_blocked"
        )
        self.logic.players[0].figures_deck = self.logic.shuffle_deck(
            state_dict.get("player1_state").get("figures_deck")
        )
        self.logic.players[0].hand = state_dict.get("player1_state").get("hand")
        self.logic.players[0].hand_size = state_dict.get("player1_state").get(
            "hand_size"
        )
        self.logic.players[0].is_blocked = state_dict.get("player1_state").get(
            "is_blocked"
        )
        self.logic.players[1].figures_slots = state_dict.get("player2_state").get(
            "figures_slots"
        )
        self.logic.players[1].figures_played = state_dict.get("player2_state").get(
            "figures_played"
        )
        self.logic.players[1].figures_blocked = state_dict.get("player2_state").get(
            "figures_blocked"
        )
        self.logic.players[1].figures_deck = self.logic.shuffle_deck(
            state_dict.get("player2_state").get("figures_deck")
        )
        self.logic.players[1].hand = state_dict.get("player2_state").get("hand")
        self.logic.players[1].hand_size = state_dict.get("player2_state").get(
            "hand_size"
        )
        self.logic.players[1].is_blocked = state_dict.get("player2_state").get(
            "is_blocked"
        )

    def set_initial_state(self):
        state = copy.deepcopy(self.initial_state)
        self.set_state(state)

    def get_switch_actions(self):
        logic = self.logic

        moves = []
        for move_card_slot, move_card in logic.current_player.hand.items():
            if move_card is None:
                continue
            card_moves = []
            for y in range(logic.board.size[0]):
                for x in range(logic.board.size[0]):
                    cell_color = logic.board.state[y][x].color
                    for move in logic.switch_possible_moves(move_card, x, y):
                        switch_move = SwitchCells(
                            x, y, move[0], move[1], move_card_slot
                        )
                        to_cell_color = logic.board.state[move[1]][move[0]].color
                        if (
                            switch_move not in card_moves
                            and switch_move not in moves
                            and cell_color != to_cell_color
                        ):
                            card_moves.append(switch_move)
            moves.extend(card_moves)

        # transform to SwitchMove

        moves = [
            SwitchMove(
                move.move_card_slot,
                move.x1,
                move.y1,
                move.x2 - move.x1,
                move.y2 - move.y1,
            )
            for move in moves
        ]
        return moves

    def find_board_figure(self, figure_name):
        # We convert the cells in the board with the border to the cells without the border
        figures_in_board_with_border = self.logic.find_board_figure(figure_name)
        for figure in figures_in_board_with_border:
            figure: BoardFigure = figure
            cells = []
            for cell in figure.cells:
                cell_x, cell_y = cell[0] - 1, cell[1] - 1  # We remove the border
                cells.append((cell_x, cell_y))
            figure.cells = cells
        return figures_in_board_with_border

    def playable_figure(self, figure_slot, player_id):
        player: Player = self.logic.players[player_id]
        player_blocked = player.is_blocked
        figure_name = player.figures_slots[figure_slot]
        figure_blocked = player.figures_blocked[figure_slot]
        current_player_id = self.logic.player_turn

        if figure_name is None:
            return False

        if player_blocked and (current_player_id != player_id):
            return False

        if figure_blocked:
            return False

        board_figures = self.find_board_figure(figure_name)
        last_color_played = self.logic.last_color_played
        figures_to_play = []
        for board_figure in board_figures:
            if (
                board_figure.name == figure_name
                and last_color_played != board_figure.color
            ):
                figures_to_play.append(board_figure)

        return False if len(figures_to_play) == 0 else figures_to_play

    def match_figure_actions(self):
        actions = []
        for player in self.logic.players:
            for i in range(player.figures_slots_qty):
                figures_to_play = self.playable_figure(i, player.player_id)
                if figures_to_play:
                    for figure in figures_to_play:
                        action = MatchFigureMove(
                            figure.name,
                            figure.x,
                            figure.y,
                            figure.color,
                            player.player_id,
                            i,
                        )
                        actions.append(action)
        return actions

    def get_possible_actions(self):
        possible_actions = [PassMove()]
        switch_moves = self.get_switch_actions()
        match_moves = self.match_figure_actions()
        possible_actions.extend(switch_moves)
        possible_actions.extend(match_moves)

        return possible_actions

    def execute_action(self, action):
        self.logic.do_move(action)
