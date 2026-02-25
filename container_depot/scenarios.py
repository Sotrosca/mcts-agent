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
            "rollouts_per_move": 20,
        },
        {
            "name": "medium_realistic",
            "board": [
                [[1, 2, 0], [3, 0, 0], [0, 0, 0]],
                [[4, 0, 0], [5, 6, 0], [0, 0, 0]],
            ],
            "pending": [2, 4, 6],
            "max_steps": 40,
            "rollouts_per_move": 25,
        },
        {
            "name": "hard_blocked",
            "board": [
                [[7, 1, 0], [2, 3, 0], [0, 0, 0]],
                [[4, 5, 0], [6, 0, 0], [0, 0, 0]],
            ],
            "pending": [1, 6, 3],
            "max_steps": 60,
            "rollouts_per_move": 30,
        },
    ]
