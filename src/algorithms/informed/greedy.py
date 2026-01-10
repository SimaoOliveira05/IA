from typing import List, Tuple
from graph.graph import Graph
from graph.position import Position
import heapq
from algorithms.informed.heuristics import calculate_heuristic

def greedy_bfs(start: Position, goal: Position, graph: Graph, heuristic: str = 'distance',
               event_manager=None, current_time: int = None) -> Tuple[float, float, List[int]]:
    """
    Greedy Best-First Search - usa apenas h(n) para ordenar a busca.
    
    Não considera o custo acumulado g(n), apenas a heurística h(n).
    Pode encontrar soluções subótimas mas é mais rápido.
    
    Args:
        start: Posição inicial
        goal: Posição objetivo
        graph: Grafo com o mapa
        heuristic: Tipo de heurística ('distance', 'time', 'cost', 'combined', etc.)
        event_manager: Gestor de eventos (opcional, para heurísticas de tempo)
        current_time: Tempo atual em minutos (opcional, usado para verificar intervalos de eventos)
    
    Returns:
        Tuple[float, float, List[int]]: (distância total em metros, tempo total em minutos, caminho)
    """
    start_node = graph.find_closest_node(start)
    goal_node = graph.find_closest_node(goal)
    
    open_set = []
    # Greedy usa apenas h(n) para ordenar
    h_start = calculate_heuristic(start_node.position, goal_node.position, heuristic,
                                   event_manager=event_manager, node_id=start_node.id, current_time=current_time)
    heapq.heappush(open_set, (h_start, start_node))
    
    came_from = {}
    visited = set()
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current.id == goal_node.id:
            path = []
            while current.id in came_from:
                path.append(current.id)
                current = came_from[current.id]
            path.append(start_node.id)
            path.reverse()
            total_distance, total_time = graph.calculate_path_metrics(path)
            return total_distance, total_time, path
            
        visited.add(current.id)
        
        for edge in graph.edges[current.id]:
            if not edge.get("open", True):
                continue
            neighbor = graph.get_node(edge["target"])
            if neighbor.id not in visited:
                came_from[neighbor.id] = current
                # Calcula heurística baseada no critério
                h_score = calculate_heuristic(neighbor.position, goal_node.position, heuristic,
                                              event_manager=event_manager, node_id=neighbor.id, current_time=current_time)
                heapq.heappush(open_set, (h_score, neighbor))
                
    return float('inf'), float('inf'), []