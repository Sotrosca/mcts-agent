from Switcher.logic.figures import BoardFigure


class ActionState:
    def __init__(self):
        self.selected_card = None
        self.selected_player_area = None
        self.selected_figure_idx = None
        self.selected_figure_area = None
        self.selected_cells = []
        self.possible_switches = None
        self.board_figures: list[BoardFigure] = []

    def clean_selected(self):
        self.selected_card = None
        self.selected_player_area = None
        self.selected_figure_idx = None
        self.selected_figure_area = None
        self.selected_cells.clear()
        self.possible_switches = None
