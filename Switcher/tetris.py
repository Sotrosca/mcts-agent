import numpy as np

# Definir las figuras de Tetris
figures = {
    "I": [[1, 1, 1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
}


# Función para rotar una figura 90 grados
def rotate_90(mat):
    return [list(row) for row in zip(*mat[::-1])]


# Generar todas las rotaciones y reflejos de una figura
def generate_variations(figure):
    variations = []
    current = figure
    for _ in range(4):
        current = rotate_90(current)
        # Check if the current variation is already in the list
        if current not in variations:
            variations.append(current)

    return variations


# Función para buscar una figura en una posición de la matriz
def match_at_position(matrix, figure, x, y):
    for i in range(len(figure)):
        for j in range(len(figure[0])):
            if figure[i][j] and (
                x + i >= len(matrix)
                or y + j >= len(matrix[0])
                or matrix[x + i][y + j] != figure[i][j]
            ):
                return False
    return True


# Función para buscar todas las figuras en la matriz
def find_figures(matrix):
    for name, figure in figures.items():
        variations = generate_variations(figure)
        print(variations)
        for x in range(len(matrix)):
            for y in range(len(matrix[0])):
                for variation in variations:

                    if match_at_position(matrix, variation, x, y):
                        print(f"Figura {name} encontrada en posición ({x}, {y})")


# Ejemplo de uso
board = [
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0],
    [1, 1, 0, 0, 0],
]

find_figures(board)
