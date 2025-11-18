"""
Funções auxiliares para gestão de abastecimento/recarga de veículos.
"""

from vehicle.vehicle import Eletric, Combustion, Hybrid
from refuel_config import REFUEL_TIME, RECHARGE_TIME, SAFETY_MARGIN


def needs_refuel(vehicle, distance):
    """
    Verifica se o veículo precisa de abastecer para percorrer a distância.
    
    Args:
        vehicle: Veículo a verificar
        distance: Distância total a percorrer em metros
        
    Returns:
        bool: True se precisa abastecer, False caso contrário
    """
    vehicle_type = vehicle.vehicle_type
    
    if isinstance(vehicle_type, Eletric):
        return not vehicle_type.has_enough_battery(distance * (1 + SAFETY_MARGIN))
    elif isinstance(vehicle_type, Combustion):
        return not vehicle_type.has_enough_fuel(distance * (1 + SAFETY_MARGIN))
    elif isinstance(vehicle_type, Hybrid):
        return not vehicle_type.has_enough_energy(distance * (1 + SAFETY_MARGIN))
    
    return False


def get_refuel_time(vehicle, station_type=None):
    """
    Retorna o tempo necessário para abastecer o veículo.
    
    Args:
        vehicle: Veículo a abastecer
        station_type: Tipo de estação ("fuel" ou "charging") - se não fornecido, deduz do veículo
        
    Returns:
        float: Tempo de abastecimento em minutos
    """
    vehicle_type = vehicle.vehicle_type
    
    if isinstance(vehicle_type, Eletric):
        return RECHARGE_TIME
    elif isinstance(vehicle_type, Combustion):
        return REFUEL_TIME
    elif isinstance(vehicle_type, Hybrid):
        # Se station_type foi fornecido, usa
        if station_type == "fuel":
            return REFUEL_TIME
        elif station_type == "charging":
            return RECHARGE_TIME
        else:
            # Deduz baseado no que está mais baixo
            battery_pct = vehicle_type.battery_percentage()
            fuel_pct = vehicle_type.fuel_percentage()
            
            if fuel_pct < battery_pct:
                return REFUEL_TIME
            else:
                return RECHARGE_TIME
    
    return 0


def find_nearest_station(graph, position, station_type):
    """
    Encontra a estação mais próxima de um determinado tipo.
    
    Args:
        graph: Grafo com os nós
        position: Posição atual
        station_type: Tipo de estação ("fuel" ou "charging")
        
    Returns:
        Node: Nó da estação mais próxima ou None
    """
    nearest_station = None
    min_distance = float('inf')
    
    for node in graph.nodes:
        if node.node_type == station_type:
            dist = position.distance_to(node.position)
            if dist < min_distance:
                min_distance = dist
                nearest_station = node
    
    return nearest_station


def get_station_type_for_vehicle(vehicle):
    """
    Retorna o tipo de estação que o veículo precisa.
    
    Args:
        vehicle: Veículo
        
    Returns:
        str: "fuel" ou "charging"
    """
    vehicle_type = vehicle.vehicle_type
    
    if isinstance(vehicle_type, Eletric):
        return "charging"
    elif isinstance(vehicle_type, Combustion):
        return "fuel"
    elif isinstance(vehicle_type, Hybrid):
        # Híbrido: escolhe baseado no que está mais baixo
        battery_pct = vehicle_type.battery_percentage()
        fuel_pct = vehicle_type.fuel_percentage()
        
        # Prioriza combustível se ambos estiverem baixos (mais rápido)
        if fuel_pct < 30 and battery_pct < 30:
            return "fuel"
        # Se combustível está muito baixo, vai abastecer
        elif fuel_pct < battery_pct:
            return "fuel"
        # Se bateria está mais baixa, vai carregar
        else:
            return "charging"
    
    return "fuel"  # Default


def calculate_total_distance(graph, path):
    """
    Calcula a distância total de um caminho.
    
    Args:
        graph: Grafo
        path: Lista de IDs de nós
        
    Returns:
        float: Distância total em metros
    """
    total_distance = 0
    
    for i in range(len(path) - 1):
        node_from = path[i]
        node_to = path[i + 1]
        edges = graph.edges.get(node_from, [])
        
        for edge in edges:
            if edge["target"] == node_to:
                total_distance += edge["distance"]
                break
    
    return total_distance
