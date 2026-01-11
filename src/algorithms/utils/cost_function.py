"""
Função de custo unificada para os algoritmos de procura.

Otimiza as operações com base em critérios de:
- Custo operacional (combustível/energia)
- Tempo de resposta
- Satisfação do cliente (tempo de espera/viagem)
- Sustentabilidade ambiental (emissões CO₂)

Este é o custo default do sistema, usado pelos algoritmos que consideram
custos das arestas (uniform_cost e a_star).
"""
from typing import Optional
from vehicle.vehicle_types import VehicleType, Eletric, Combustion, Hybrid

# Constantes importadas do config
try:
    from config import (
        PRECO_BATERIA, PRECO_COMBUSTIVEL,
        PESO_TEMPO, PESO_CUSTO, PESO_AMBIENTE,
     CUSTO_BASE_EUR, EMISSOES_BASE_G
    )
    from utils.vehicle_costs import calculate_fuel_cost as calc_fuel_cost
    from utils.vehicle_costs import calculate_emissions as calc_emissions
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config import (
        PRECO_BATERIA, PRECO_COMBUSTIVEL,
        PESO_TEMPO, PESO_CUSTO, PESO_AMBIENTE,
        CUSTO_BASE_EUR, EMISSOES_BASE_G
    )
    calc_fuel_cost = None
    calc_emissions = None

def calculate_edge_cost(
    distance: float,
    time: float,
    vehicle_type: Optional[VehicleType] = None,
) -> float:
    """
    Calcula o custo unificado de uma aresta considerando múltiplos critérios.
    
    Este custo combina:
    1. Tempo de resposta - quanto mais rápido, melhor
    2. Custo operacional - combustível/energia gasto
    3. Satisfação do cliente - penaliza tempos longos
    4. Sustentabilidade ambiental - emissões de CO₂
    
    Args:
        distance: Distância da aresta em metros
        time: Tempo base da aresta em minutos (já inclui trânsito/clima)
        vehicle_type: Tipo de veículo (opcional, para cálculos precisos)
    
    Returns:
        float: Custo unificado da aresta (valor normalizado)
    """
    dist_km = distance / 1000.0

    custo_euros = _calculate_operational_cost(dist_km, vehicle_type)
    custo_normalizado = custo_euros / CUSTO_BASE_EUR if CUSTO_BASE_EUR > 0 else custo_euros
    
    emissoes_g = _calculate_emissions(dist_km, vehicle_type)
    ambiente_normalizado = emissoes_g / EMISSOES_BASE_G if EMISSOES_BASE_G > 0 else emissoes_g
    
    # =========================================================================
    # CUSTO FINAL: média ponderada dos critérios
    # =========================================================================
    custo_total = (
        PESO_TEMPO * time +
        PESO_CUSTO * custo_normalizado +
        PESO_AMBIENTE * ambiente_normalizado
    )
    
    # Escala para valores comparáveis com distância original (para compatibilidade)
    # Multiplica por distância para manter proporcionalidade
    return custo_total * distance


def _calculate_operational_cost(dist_km: float, vehicle_type: Optional[VehicleType]) -> float:
    """
    Calcula o custo operacional em euros para uma distância.
    Usa função centralizada do módulo utils.
    
    Args:
        dist_km: Distância em quilómetros
        vehicle_type: Tipo de veículo
    
    Returns:
        float: Custo em euros
    """
    if calc_fuel_cost is not None:
        return calc_fuel_cost(vehicle_type, dist_km)
    
    # Fallback se utils não disponível
    if vehicle_type is None:
        return dist_km * CUSTO_BASE_EUR
    
    if isinstance(vehicle_type, Eletric):
        energia_kwh = (vehicle_type.battery_consumption / 100.0) * dist_km
        return energia_kwh * PRECO_BATERIA
    elif isinstance(vehicle_type, Combustion):
        combustivel_l = (vehicle_type.fuel_consumption / 100.0) * dist_km
        return combustivel_l * PRECO_COMBUSTIVEL
    elif isinstance(vehicle_type, Hybrid):
        consumo_bateria_por_km = vehicle_type.battery_consumption / 100.0
        consumo_combustivel_por_km = vehicle_type.fuel_consumption / 100.0
        bateria_km = vehicle_type.current_battery / consumo_bateria_por_km if consumo_bateria_por_km > 0 else 0
        if dist_km <= bateria_km:
            return consumo_bateria_por_km * dist_km * PRECO_BATERIA
        else:
            energia_kwh = consumo_bateria_por_km * bateria_km
            combustivel_l = consumo_combustivel_por_km * (dist_km - bateria_km)
            return energia_kwh * PRECO_BATERIA + combustivel_l * PRECO_COMBUSTIVEL
    return dist_km * CUSTO_BASE_EUR


def _calculate_emissions(dist_km: float, vehicle_type: Optional[VehicleType]) -> float:
    """
    Calcula as emissões de CO₂ em gramas para uma distância.
    Usa função centralizada do módulo utils.
    
    Args:
        dist_km: Distância em quilómetros
        vehicle_type: Tipo de veículo
    
    Returns:
        float: Emissões em gramas de CO₂
    """
    if calc_emissions is not None:
        return calc_emissions(vehicle_type, dist_km)
    
    # Fallback se utils não disponível
    from config import EMISSIONS_COMBUSTION_G_PER_KM, EMISSIONS_HYBRID_G_PER_KM
    
    if vehicle_type is None:
        return EMISSIONS_COMBUSTION_G_PER_KM * dist_km
    
    if isinstance(vehicle_type, Eletric):
        return 0.0
    elif isinstance(vehicle_type, Combustion):
        return EMISSIONS_COMBUSTION_G_PER_KM * dist_km
    elif isinstance(vehicle_type, Hybrid):
        consumo_bateria_por_km = vehicle_type.battery_consumption / 100.0
        bateria_km = vehicle_type.current_battery / consumo_bateria_por_km if consumo_bateria_por_km > 0 else 0
        if dist_km <= bateria_km:
            return 0.0
        else:
            return EMISSIONS_HYBRID_G_PER_KM * (dist_km - bateria_km)
    return EMISSIONS_COMBUSTION_G_PER_KM * dist_km
    
    # Fallback
    return 120.0 * dist_km
