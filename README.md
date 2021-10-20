# Montecarlo Tree Search Agent

Agente implementable para aprendizaje reforzado que utiliza algoritmos de Montecarlo Tree Searching.

Correr TicTacToeGame.py para ver demo del agente utilizado en un juego de ta-te-ti.

# Qué es MCTS?

El algoritmo MCTS se engloba en lo que es el aprendizaje reforzado.

Consta de la exploración de un árbol de decisión, que representa las posibles acciones a realizar en un entorno.

Esta exploración se realiza mediante métodos de tipo Montecarlo (simulaciones aleatorias).

Luego, utilizando un función de recompensa o valoración, se puntúa cada rama explorada y después de varias simulaciones se elige la acción mejor puntuada.

El proceso de exploración del árbol consta de 4 fases:

- Selección: Donde se elige la rama del árbol a explorar.
- Expansión: Donde se determina si el nodo terminal de esa rama se expandirá en esta iteración o no.
- Simulación: Se simula, de manera aleatoria o pseudoaleatoria, a partir del nodo terminal de la rama elegida.
- Retropropagación: Se puntúa el resultado de la simulación y se retropropaga esa puntuación a todos los nodos de la rama.

Luego de explorar el tiempo deseado, se elige el mejor movimiento de entre los nodos principales.

Éste será el nodo que reprensenta la próxima acción a realizar.

De esta manera el un algoritmo MCTS tiene el potencial de poder resolver cualquier problema de decisión que sea simulable.

# Cómo utilizarlo

Para utilizar el agente, deberá implementarse la simulación en la que quiera ejecutarse dicho agente.

La simulación deberá contar con los siguientes métodos:

    - get_state() (Devuelve el estado actual de la simulación)
    - set_state(state_dict) (Setea la simulación en el estado pasado por parámetro)
    - get_possible_actions (Lista de acciones posibles)
    - execute_action (Ejecuta una acción en la simulación)

Además habrá que implementar la funciones que se encargarán de cada etapa del proceso de exploración y la función selectora del mejor movimiento.

# Ta-Te-Ti Demo

Ejecutando el archivo 'TicTacToeGame.py' podrás jugar al ta-te-ti contra un bot cuya inteligencia es un MCTS.

Las funciones para ejecutar la exploración del árbol de decisiones en este caso se encuentran en el archivo 'TicTacToe/TicTacToeMCTSFunctions.py'

Son las siguientes:

 - Selección: UCT (Upper Confidence bounds applied to Trees).
 - Expansión: Cada visita a un nodo lo expande.
 - Simulación: Totalmente aleatoria hasta que termine el juego.
 - Retropropagación: Recompensa las partidas ganadas sumando en 1 el valor del nodo y penalizo 