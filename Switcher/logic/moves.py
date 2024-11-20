class SwitchMovementCard:
    moves = None

    def __init__(self, cells_to_switch_row, cells_to_switch_column, name=None):
        self.calculate_moves(cells_to_switch_row, cells_to_switch_column)
        self.name = name

    def calculate_moves(self, cells_to_switch_row, cells_to_switch_column):
        moves = []

        moves.append((cells_to_switch_row, cells_to_switch_column))
        moves.append((-cells_to_switch_row, -cells_to_switch_column))
        moves.append((cells_to_switch_column, -cells_to_switch_row))  # Symmetric move
        moves.append((-cells_to_switch_column, cells_to_switch_row))  # Symmetric move
        self.moves = moves

    def possible_moves(self, x, y):
        return [(x + move[0], y + move[1]) for move in self.moves]

    def __eq__(self, other):
        """
        Moves are equal if almost one of the moves is equal
        """
        for move in self.moves:
            for other_move in other.moves:
                apply_both_moves = (move[0] + other_move[0], move[1] + other_move[1])
                if apply_both_moves == (0, 0):
                    return True
        return False

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return self.__str__()


moves = {
    "One step": (1, 0),
    "Two steps": (2, 0),
    "Three steps": (3, 0),
    "Diagonal": (1, 1),
    "Double diagonal": (2, 2),
    "Knight": (2, 1),
    "Inverted knight": (1, 2),
}

moves_deck = []

for key in moves.keys():
    qty = 5 if key in ["Knight", "Inverted knight"] else 6
    for _ in range(qty):
        moves_deck.append(SwitchMovementCard(*moves[key], name=key))
