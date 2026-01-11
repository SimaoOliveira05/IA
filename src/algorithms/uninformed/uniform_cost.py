from typing import Any, List, Tuple, Optional
from graph.graph import Graph
from graph.position import Position
from algorithms.utils.cost_function import calculate_edge_cost
from vehicle.vehicle_types import VehicleType
import heapq
import itertools

def uniform_cost_search(start: Position, goal: Position, graph: Graph, 
                        vehicle_type: Optional[VehicleType] = None) -> Tuple[float, float, List[int]]:
    """
    Uniform Cost Search - usa custo unificado das arestas.
    
    O custo combina múltiplos critérios:
    - Tempo de resposta
    - Custo operacional (combustível/energia)
    - Satisfação do cliente
    - Sustentabilidade ambiental (emissões CO₂)
    
    Args:
        start: Posição inicial
        goal: Posição objetivo
        graph: Grafo com o mapa
        vehicle_type: Tipo de veículo (opcional, para cálculos precisos de custo)
    
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
                # Usa custo unificado (tempo, custo operacional, satisfação, ambiente)
                edge_distance = edge.get("distance", 0.0)
                edge_time = edge.get("time", 0.0)
                edge_cost = calculate_edge_cost(edge_distance, edge_time, vehicle_type)
                heapq.heappush(open_set, (cost + edge_cost, next(counter), neighbor, path + [neighbor.id]))
    return float('inf'), float('inf'), []
