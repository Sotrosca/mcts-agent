from Switcher.logic.logic import Switcher

if __name__ == "__main__":
    game = Switcher(1)

    game.deal_figures()
    game.deal_moves()

    print("Figures Deck")
    for key, figure_name in game.current_player.figures_slots.items():
        print(key, figure_name)
    for key, figure_name in game.current_player.hand.items():
        print(key, figure_name)

    continue_game = True

    while continue_game:

        print("Board")
        state = game.board.state
        for row in state:
            # switch -1 to X
            row = [str(cell.color) for cell in row]
            print(" ".join(row))

        print("Moves")
        for key, figure_name in game.current_player.hand.items():
            print(key, figure_name)
        print("9. Exit")

        move_number = int(input("Select a move: "))

        if move_number == 9:
            continue_game = False
            continue

        if move_number not in game.current_player.hand.keys():
            print("Invalid move")
            continue

        selected_cell_x = int(input("Select cell x coordinate: "))

        if (
            selected_cell_x < 0
            or selected_cell_x >= game.board.size[0] * game.board.size[1]
        ):
            print("Invalid cell row")
            continue

        selected_cell_y = int(input("Select cell y coordinate: "))
        if (
            selected_cell_y < 0
            or selected_cell_y >= game.board.size[0] * game.board.size[1]
        ):
            print("Invalid cell column")
            continue

        selected_cell = game.board.state[selected_cell_x][selected_cell_y]

        possible_moves = [
            (selected_cell_x + move[0], selected_cell_y + move[1])
            for move in game.current_player.hand[move_number].moves
        ]

        for i, move in enumerate(possible_moves):
            print(i, move)

        selected_move = int(input("Select a move: "))

        move = possible_moves[selected_move]

        valid_move = game.switch_cells(
            selected_cell_x,
            selected_cell_y,
            move[0] - selected_cell_x,
            move[1] - selected_cell_y,
        )

        if not valid_move:
            print("Error switching")
            continue
