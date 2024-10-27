class PlayerMove:
    def __init__(
        self,
        move_type,
        move_card_slot=None,
        cell_x_target=None,
        cell_y_target=None,
        steps_x=None,
        steps_y=None,
        figure_name=None,
        figure_board_color=None,
        figure_board_x=None,
        figure_board_y=None,
        player_id=None,
        player_figure_slot=None,
    ):
        self.type = move_type  # Pass, Switch, Match figure
        self.move_card_slot = move_card_slot
        self.cell_x_target = cell_x_target
        self.cell_y_target = cell_y_target
        self.steps_x = steps_x
        self.steps_y = steps_y
        self.figure_name = figure_name
        self.figure_board_color = figure_board_color
        self.figure_board_x = figure_board_x
        self.figure_board_y = figure_board_y
        self.player_id = player_id
        self.player_figure_slot = player_figure_slot


class SwitchMove(PlayerMove):
    def __init__(self, move_card_slot, cell_x_target, cell_y_target, steps_x, steps_y):
        super().__init__(
            "Switch", move_card_slot, cell_x_target, cell_y_target, steps_x, steps_y
        )

    def possible_moves(self, x, y):
        moves = [
            (x + self.steps_x, y + self.steps_y),
            (x - self.steps_y, y + self.steps_x),
            (x - self.steps_x, y - self.steps_y),
            (x + self.steps_y, y - self.steps_x),
        ]

        return moves


class PassMove(PlayerMove):
    def __init__(self):
        super().__init__("Pass")


class MatchFigureMove(PlayerMove):
    def __init__(
        self,
        figure_name,
        figure_board_position,
        figure_board_color,
        player_id,
        player_figure_slot,
    ):
        super().__init__(
            "Match figure",
            figure_name,
            figure_board_position,
            figure_board_color,
            player_id,
            player_figure_slot,
        )
