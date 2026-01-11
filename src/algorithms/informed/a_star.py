"""
Implementação do algoritmo A* com suporte a múltiplos critérios de heurística:
- 'distance': Heurística de distância euclidiana
- 'time': Heurística de tempo estimado (considera clima/trânsito)
- 'cost': Heurística de custo operacional
- 'combined': Heurística combinada

IMPORTANTE: O custo g(n) das arestas usa a função de custo unificada que combina:
- Tempo de resposta
- Custo operacional (combustível/energia)
- Satisfação do cliente
- Sustentabilidade ambiental (emissões CO₂)

A heurística h(n) varia conforme o critério escolhido.
"""
from typing import List, Tuple, Optional
from graph.graph import Graph
from graph.position import Position
import heapq
import itertools

# Importa preços de energia/combustível e função de custo
from algorithms.informed.heuristics import calculate_heuristic
from algorithms.utils.cost_function import calculate_edge_cost
from vehicle.vehicle_types import VehicleType

def a_star(start: Position, goal: Position, graph: Graph, criterion: str = 'distance', 
           event_manager=None, current_time: int = None, vehicle_type: Optional[VehicleType] = None) -> Tuple[float, float, List[int]]:
    """
    A* Search - usa DISTÂNCIA como custo g(n) das arestas, com heurística variável h(n).
    
    Args:
        start: Posição inicial
        goal: Posição objetivo
        graph: Grafo com o mapa
        criterion: Tipo de heurística ('distance', 'time', 'cost', 'combined', etc.)
        event_manager: Gestor de eventos (opcional, para heurísticas que consideram clima/trânsito)
        current_time: Tempo atual em minutos (opcional, usado para verificar intervalos de eventos)
        vehicle_type: Tipo de veículo (opcional, necessário para heurísticas de custo)
    
    Returns:
        Tuple[float, float, List[int]]: (distância total em metros, tempo total em minutos, caminho)
    """
    start_node = graph.find_closest_node(start)
    goal_node = graph.find_closest_node(goal)
    
    # Priority Queue armazena (f_score, counter, node)
    open_set = []
    counter = itertools.count()  # Contador para desempate
    
    # Inicializa scores
    g_score = {node.id: float('inf') for node in graph.nodes}
    g_score[start_node.id] = 0
    
    h_start = calculate_heuristic(start_node.position, goal_node.position, criterion, 
                                   vehicle_type=vehicle_type, event_manager=event_manager, 
                                   node_id=start_node.id, current_time=current_time)
    f_score = {node.id: float('inf') for node in graph.nodes}
    f_score[start_node.id] = h_start
    
    heapq.heappush(open_set, (f_score[start_node.id], next(counter), start_node))
    came_from = {}
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        
        if current.id == goal_node.id:
            path = []
            while current.id in came_from:
                path.append(current.id)
                current = came_from[current.id]
            path.append(start_node.id)
            path.reverse()
            total_distance, total_time = graph.calculate_path_metrics(path)
            return total_distance, total_time, path
            
        for edge in graph.edges[current.id]:
            if not edge.get("open", True):
                continue
            neighbor = graph.get_node(edge["target"])
            
            # g(n) é o custo unificado (tempo, custo operacional, satisfação, ambiente)
            edge_distance = edge.get("distance", 0.0)
            edge_time = edge.get("time", 0.0)
            edge_cost = calculate_edge_cost(edge_distance, edge_time, vehicle_type)
            tentative_g_score = g_score[current.id] + edge_cost
            
            if tentative_g_score < g_score[neighbor.id]:
                came_from[neighbor.id] = current
                g_score[neighbor.id] = tentative_g_score
                
                # h(n) varia conforme o critério da heurística
                h_score = calculate_heuristic(neighbor.position, goal_node.position, criterion,
                                              vehicle_type=vehicle_type, event_manager=event_manager, 
                                              node_id=neighbor.id, current_time=current_time)
                f_score[neighbor.id] = tentative_g_score + h_score
                heapq.heappush(open_set, (f_score[neighbor.id], next(counter), neighbor))
                
    return float('inf'), float('inf'), []