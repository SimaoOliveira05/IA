from typing import Any, List, Tuple
from graph.graph import Graph
from graph.position import Position
import heapq
import itertools

def uniform_cost_search(start: Position, goal: Position, graph: Graph) -> Tuple[float, float, List[int]]:
    """
    Uniform Cost Search - usa DISTÂNCIA como custo das arestas.
    
    O custo é a distância em metros. Após encontrar o caminho,
    calcula também o tempo total (que pode ser afetado por trânsito/clima).
    
    Returns:
        Tuple[float, float, List[int]]: (distância total em metros, tempo total em minutos, caminho)
    """
    start_node = graph.find_closest_node(start)
    goal_node = graph.find_closest_node(goal)
    open_set = []
    counter = itertools.count()  # Contador para desempate
    heapq.heappush(open_set, (0, next(counter), start_node, [start_node.id]))
    visited = set()
    while open_set:
        cost, _, current, path = heapq.heappop(open_set)
        if current.id == goal_node.id:
            total_distance, total_time = graph.calculate_path_metrics(path)
            return total_distance, total_time, path
        if current.id in visited:
            continue
        visited.add(current.id)
        for edge in graph.edges[current.id]:
            if not edge.get("open", True):
                continue
            neighbor = graph.get_node(edge["target"])
            if neighbor.id not in visited:
                # Usa DISTÂNCIA como custo (em metros)
                edge_distance = edge.get("distance", 0.0)
                heapq.heappush(open_set, (cost + edge_distance, next(counter), neighbor, path + [neighbor.id]))
    return float('inf'), float('inf'), []
