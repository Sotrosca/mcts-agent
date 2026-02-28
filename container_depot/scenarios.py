def manhattan_distance(x_position, y_position):
    return abs(x_position[0] - y_position[0]) + abs(x_position[1] - y_position[1])


def get_container_depot_scenarios():
    return [
        {
            "name": "small_easy",
            "board": [
                [[1, 0], [0, 0]],
                [[2, 0], [0, 0]],
            ],
            "pending": [1, 2],
            "max_steps": 20,
            "rollouts_per_move": 1000,
        },
        {
            "name": "medium_realistic",
            "board": [
                [[1, 2, 0], [3, 0, 0], [0, 0, 0]],
                [[4, 0, 0], [5, 6, 0], [0, 0, 0]],
            ],
            "pending": [2, 4, 6],
            "max_steps": 40,
            "rollouts_per_move": 1000,
        },
        {
            "name": "hard_blocked",
            "board": [
                [[7, 1, 0], [2, 3, 0], [0, 0, 0]],
                [[4, 5, 0], [6, 0, 0], [0, 0, 0]],
            ],
            "pending": [1, 6, 3],
            "max_steps": 60,
            "rollouts_per_move": 1000,
        },
        {
            "name": "logic_blocked_2x2",
            "board": [
                [[1, 8, 9], [2, 0, 0]],
                [[4, 0, 0], [0, 0, 0]],
            ],
            "pending": [1, 2],
            "max_steps": 20,
            "rollouts_per_move": 1000,
        },
        {
            "name": "very_hard_stacked_3x3",
            "board": [
                [[11, 12, 13, 14], [2, 17, 0, 0], [5, 6, 0, 0]],
                [[7, 8, 9, 0], [3, 4, 0, 0], [10, 0, 0, 0]],
                [[1, 0, 0, 0], [15, 16, 0, 0], [0, 0, 0, 0]],
            ],
            "pending": [11, 7, 3],
            "max_steps": 120,
            "rollouts_per_move": 1000,
        },
    ]
