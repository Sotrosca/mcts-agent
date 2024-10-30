class Config:
    SCREEN_WIDTH, SCREEN_HEIGHT = 880, 680
    COLORS = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 0)]
    BOARD_FIGURE_COLOR_CHANGE = 2
    BACKGROUND_COLOR = (100, 130, 130)
    BOARD_BACKGROUND_COLOR = (40, 40, 40)
    CARD_COLOR = (255, 255, 255)
    CURRENT_PLAYER_CARD_COLOR = (80, 200, 100)
    EMPTY_CARD_COLOR = (100, 100, 100)
    BORDER_COLOR = (40, 40, 40)
    BORDER_RADIUS = 10
    SELECTED_CELL_BORDER_COLOR = (100, 100, 100)
    POSSIBLE_SWITCHES_BORDER_COLOR = (150, 150, 150)
    SELECTED_CELL_BORDER_RADIUS = 15
    CARD_WIDTH, CARD_HEIGHT = 200, 350
    FIGURE_WIDTH, FIGURE_HEIGHT = 60, 60
    CARDS_QTY = 3
    BOARD_SIZE = 320
    MARGIN = 20
    FIGURE_COLOR = (100, 100, 100)
    FIGURE_ON_BOARD_BACKGROUND_COLOR = (255, 210, 97)
    FIGURE_BACKGROUND_COLOR = (255, 255, 255)
    CELL_SIZE = 15

    def board_figure_color(color):
        new_color = []
        for i in range(3):
            new_value = color[i] // Config.BOARD_FIGURE_COLOR_CHANGE
            if new_value < 0:
                new_value = 0
            new_color.append(new_value)
        return tuple(new_color)
