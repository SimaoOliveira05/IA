# Funções de heurística centralizadas
from typing import Optional
from graph.position import Position
from vehicle.vehicle_types import Eletric, Combustion, Hybrid, VehicleType

# Constantes importadas do config
try:
    from config import (
        PRECO_BATERIA, PRECO_COMBUSTIVEL,
        DEFAULT_SPEED_KMH, COST_PER_KM, COST_PER_MIN,
        EURO_TO_METERS, CO2_TO_METERS,
        TRAFFIC_PENALTIES, TRAFFIC_PROPAGATION_FACTOR,
        EMISSIONS_COMBUSTION_G_PER_KM
    )
    from utils.vehicle_costs import calculate_fuel_cost, calculate_emissions
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config import (
        PRECO_BATERIA, PRECO_COMBUSTIVEL,
        DEFAULT_SPEED_KMH, COST_PER_KM, COST_PER_MIN,
        EURO_TO_METERS, CO2_TO_METERS,
        TRAFFIC_PENALTIES, TRAFFIC_PROPAGATION_FACTOR,
        EMISSIONS_COMBUSTION_G_PER_KM
    )
    from utils.vehicle_costs import calculate_fuel_cost, calculate_emissions


# =============================================================================
# FUNÇÕES DE HEURÍSTICA INDIVIDUAIS
# =============================================================================

def _heuristic_distance(dist_meters: float, dist_km: float, speed_kmh: float,
                        vehicle_type: Optional[VehicleType], event_manager,
                        node_id: int, current_time: int) -> float:
    """
    Heurística de distância euclidiana.
    Simples e admissível - nunca sobrestima o custo real.
    """
    return dist_meters


def _heuristic_time(dist_meters: float, dist_km: float, speed_kmh: float,
                    vehicle_type: Optional[VehicleType], event_manager,
                    node_id: int, current_time: int) -> float:
    """
    Heurística de tempo estimado COM impactos de clima e trânsito.
    Calcula tempo base usando velocidade média do veículo.
    """
    base_time = (dist_km / speed_kmh) * 60.0
    
    # Aplica multiplicador combinado de clima + trânsito se disponível
    if event_manager is not None and node_id is not None:
        multiplier = event_manager.get_weather_multiplier(node_id, current_time) * event_manager.get_traffic_multiplier(node_id, current_time)
        time_minutes = base_time * multiplier
        meters_equivalent = time_minutes * (speed_kmh * 1000.0 / 60.0)
        return meters_equivalent
    
    return base_time * (speed_kmh * 1000.0 / 60.0)


def _heuristic_cost(dist_meters: float, dist_km: float, speed_kmh: float,
                    vehicle_type: Optional[VehicleType], event_manager,
                    node_id: int, current_time: int) -> float:
    """
    Heurística de custo operacional em euros.
    Usa função centralizada para calcular custo.
    """
    custo_euros = calculate_fuel_cost(vehicle_type, dist_km)
    return custo_euros * EURO_TO_METERS


def _heuristic_environmental(dist_meters: float, dist_km: float, speed_kmh: float,
                             vehicle_type: Optional[VehicleType], event_manager,
                             node_id: int, current_time: int) -> float:
    """
    Heurística de impacto ambiental (emissões CO₂).
    Usa função centralizada para calcular emissões.
    
    NOTA: Para veículos elétricos (emissões = 0), usa distância como fallback
    para manter a heurística informativa e evitar exploração excessiva.
    """
    emissoes_g = calculate_emissions(vehicle_type, dist_km)
    
    # Se emissões são zero (elétrico ou híbrido com bateria), usa distância como fallback
    if emissoes_g == 0.0:
        return dist_meters
    
    # Converte emissões para "distância equivalente" para compatibilidade
    return emissoes_g * CO2_TO_METERS


def _heuristic_traffic_avoidance(dist_meters: float, dist_km: float, speed_kmh: float,
                                  vehicle_type: Optional[VehicleType], event_manager,
                                  node_id: int, current_time: int) -> float:
    """
    Heurística que penaliza zonas com trânsito.
    
    O trânsito tende a afetar áreas maiores (não só um nó isolado), por isso
    esta heurística aplica uma penalização preventiva para evitar entrar em
    zonas congestionadas, assumindo que nós próximos também terão trânsito.
    """
    base_heuristic = dist_meters
    
    if event_manager is None or node_id is None:
        return base_heuristic
    
    # Obtém nível de trânsito no nó destino
    traffic = event_manager.get_traffic_at_node(node_id, current_time)
    traffic_value = traffic.value if hasattr(traffic, 'value') else str(traffic)
    
    penalty = TRAFFIC_PENALTIES.get(traffic_value, 1.0)
    
    # Aplica penalização extra se trânsito moderado ou pior
    # (zonas com muito trânsito provavelmente têm trânsito nos nós adjacentes)
    if penalty > 1.3:
        penalty *= TRAFFIC_PROPAGATION_FACTOR
    
    return base_heuristic * penalty


def _heuristic_combined(pos1: Position, pos2: Position, dist_meters: float, dist_km: float, 
                        speed_kmh: float, vehicle_type: Optional[VehicleType], event_manager,
                        node_id: int, current_time: int) -> float:
    """
    Heurística combinada: média ponderada de todas as outras.
    """
    h_distance = _heuristic_distance(dist_meters, dist_km, speed_kmh, vehicle_type, 
                                      event_manager, node_id, current_time)
    h_time = _heuristic_time(dist_meters, dist_km, speed_kmh, vehicle_type, 
                              event_manager, node_id, current_time)
    h_cost = _heuristic_cost(dist_meters, dist_km, speed_kmh, vehicle_type, 
                              event_manager, node_id, current_time)
    h_environmental = _heuristic_environmental(dist_meters, dist_km, speed_kmh, vehicle_type, 
                                                event_manager, node_id, current_time)
    h_traffic_avoidance = _heuristic_traffic_avoidance(dist_meters, dist_km, speed_kmh, vehicle_type,
                                                        event_manager, node_id, current_time)
    
    # Média das 5 heurísticas
    return (h_distance + h_time + h_cost + h_environmental + h_traffic_avoidance) / 5.0


# =============================================================================
# FUNÇÃO PRINCIPAL DE CÁLCULO DE HEURÍSTICA
# =============================================================================

def calculate_heuristic(pos1: Position, pos2: Position, criterion: str, 
                        vehicle_type: Optional[VehicleType] = None, 
                        event_manager=None, node_id: int = None, 
                        current_time: int = None) -> float:
    """
    Calcula a heurística h(n) baseada no critério escolhido.
    Usa velocidade média e consumo específico do veículo quando disponível.
    
    Args:
        pos1: Posição atual
        pos2: Posição objetivo
        criterion: Tipo de heurística ('distance', 'time', 'cost', 'environmental', 'combined')
        vehicle_type: Tipo de veículo (opcional, contém average_speed e consumo)
        event_manager: Gestor de eventos (opcional, para 'time' considerar clima/trânsito)
        node_id: ID do nó atual (opcional, usado para heurística de tempo)
        current_time: Tempo atual em minutos (opcional, usado para verificar intervalos)
    
    Returns:
        float: Valor da heurística h(n)
    """
    dist_meters = pos1.distance_to(pos2)
    dist_km = dist_meters / 1000.0
    
    # Usa velocidade do veículo se disponível, senão usa valor padrão
    speed_kmh = getattr(vehicle_type, 'average_speed', DEFAULT_SPEED_KMH) if vehicle_type else DEFAULT_SPEED_KMH

    # Mapeamento de critérios para funções
    heuristic_functions = {
        'distance': _heuristic_distance,
        'time': _heuristic_time,
        'cost': _heuristic_cost,
        'environmental': _heuristic_environmental,
        'traffic_avoidance': _heuristic_traffic_avoidance,
    }
    
    if criterion == 'combined':
        return _heuristic_combined(pos1, pos2, dist_meters, dist_km, speed_kmh, 
                                   vehicle_type, event_manager, node_id, current_time)
    
    if criterion in heuristic_functions:
        return heuristic_functions[criterion](dist_meters, dist_km, speed_kmh, 
                                               vehicle_type, event_manager, 
                                               node_id, current_time)

# =============================================================================
# DICIONÁRIO DE HEURÍSTICAS DISPONÍVEIS
# =============================================================================

HEURISTICS = {
    'distance': 'Distância Euclidiana',
    'time': 'Tempo Estimado (com clima e trânsito)',
    'cost': 'Custo Operacional (€)',
    'environmental': 'Impacto Ambiental (CO₂)',
    'traffic_avoidance': 'Evitar Trânsito (penaliza zonas congestionadas)',
    'combined': 'Combinada (média de todas)',
}