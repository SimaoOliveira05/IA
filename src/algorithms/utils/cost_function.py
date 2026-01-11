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
from refuel_config import PRECO_BATERIA, PRECO_COMBUSTIVEL

# =============================================================================
# PESOS DOS CRITÉRIOS (somam 1.0)
# =============================================================================
PESO_TEMPO = 0.35           # Tempo de resposta (importante para satisfação)
PESO_CUSTO = 0.50           # Custo operacional (€)
PESO_AMBIENTE = 0.15        # Sustentabilidade ambiental (emissões CO₂)

# =============================================================================
# CONSTANTES DE NORMALIZAÇÃO (para trazer tudo à mesma escala)
# =============================================================================
# Base: 1km de distância como referência
TEMPO_BASE_MIN = 1.2        # ~1.2 min para percorrer 1km a 50km/h
CUSTO_BASE_EUR = 0.15       # ~0.15€ por km (média entre elétrico e combustão)
EMISSOES_BASE_G = 60.0      # ~60g CO₂/km (média considerando mix de veículos)

def calculate_edge_cost(
    distance: float,
    time: float,
    vehicle_type: Optional[VehicleType] = None,
    event_multiplier: float = 1.0
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
        time: Tempo base da aresta em minutos (pode já incluir trânsito/clima)
        vehicle_type: Tipo de veículo (opcional, para cálculos precisos)
        event_multiplier: Multiplicador de eventos (trânsito/clima) já aplicado ao tempo
    
    Returns:
        float: Custo unificado da aresta (valor normalizado)
    """
    dist_km = distance / 1000.0
    

    # Tempo já vem em minutos, normaliza para a escala base
    tempo_normalizado = time / TEMPO_BASE_MIN if TEMPO_BASE_MIN > 0 else time

    custo_euros = _calculate_operational_cost(dist_km, vehicle_type)
    custo_normalizado = custo_euros / CUSTO_BASE_EUR if CUSTO_BASE_EUR > 0 else custo_euros
    
    emissoes_g = _calculate_emissions(dist_km, vehicle_type)
    ambiente_normalizado = emissoes_g / EMISSOES_BASE_G if EMISSOES_BASE_G > 0 else emissoes_g
    
    # =========================================================================
    # CUSTO FINAL: média ponderada dos critérios
    # =========================================================================
    custo_total = (
        PESO_TEMPO * tempo_normalizado +
        PESO_CUSTO * custo_normalizado +
        PESO_AMBIENTE * ambiente_normalizado
    )
    
    # Escala para valores comparáveis com distância original (para compatibilidade)
    # Multiplica por distância para manter proporcionalidade
    return custo_total * distance


def _calculate_operational_cost(dist_km: float, vehicle_type: Optional[VehicleType]) -> float:
    """
    Calcula o custo operacional em euros para uma distância.
    
    Args:
        dist_km: Distância em quilómetros
        vehicle_type: Tipo de veículo
    
    Returns:
        float: Custo em euros
    """
    if vehicle_type is None:
        # Sem veículo especificado, usa custo médio
        return dist_km * CUSTO_BASE_EUR
    
    if isinstance(vehicle_type, Eletric):
        # Custo elétrico: consumo (kWh/100km) * distância * preço
        energia_kwh = (vehicle_type.battery_consumption / 100.0) * dist_km
        return energia_kwh * PRECO_BATERIA
    
    elif isinstance(vehicle_type, Combustion):
        # Custo combustão: consumo (L/100km) * distância * preço
        combustivel_l = (vehicle_type.fuel_consumption / 100.0) * dist_km
        return combustivel_l * PRECO_COMBUSTIVEL
    
    elif isinstance(vehicle_type, Hybrid):
        # Híbrido: prioriza bateria, depois combustível
        consumo_bateria_por_km = vehicle_type.battery_consumption / 100.0
        consumo_combustivel_por_km = vehicle_type.fuel_consumption / 100.0
        
        # Quantos km consegue fazer com bateria atual
        if consumo_bateria_por_km > 0:
            bateria_km = vehicle_type.current_battery / consumo_bateria_por_km
        else:
            bateria_km = 0
        
        if dist_km <= bateria_km:
            # Toda a viagem com bateria
            energia_kwh = consumo_bateria_por_km * dist_km
            return energia_kwh * PRECO_BATERIA
        else:
            # Parte com bateria, resto com combustível
            energia_kwh = consumo_bateria_por_km * bateria_km
            combustivel_l = consumo_combustivel_por_km * (dist_km - bateria_km)
            return energia_kwh * PRECO_BATERIA + combustivel_l * PRECO_COMBUSTIVEL
    
    # Fallback
    return dist_km * CUSTO_BASE_EUR


def _calculate_emissions(dist_km: float, vehicle_type: Optional[VehicleType]) -> float:
    """
    Calcula as emissões de CO₂ em gramas para uma distância.
    
    Args:
        dist_km: Distância em quilómetros
        vehicle_type: Tipo de veículo
    
    Returns:
        float: Emissões em gramas de CO₂
    """
    if vehicle_type is None:
        # Sem veículo, assume média de 120 g/km (combustão típica)
        return 120.0 * dist_km
    
    if isinstance(vehicle_type, Eletric):
        # Elétricos não têm emissões diretas
        return 0.0
    
    elif isinstance(vehicle_type, Combustion):
        # Combustão: ~2.3kg CO₂ por litro de gasolina
        consumo_por_km = vehicle_type.fuel_consumption / 100.0
        return consumo_por_km * 2300.0 * dist_km
    
    elif isinstance(vehicle_type, Hybrid):
        # Híbrido: depende de quanto usa de cada
        consumo_bateria_por_km = vehicle_type.battery_consumption / 100.0
        consumo_combustivel_por_km = vehicle_type.fuel_consumption / 100.0
        
        if consumo_bateria_por_km > 0:
            bateria_km = vehicle_type.current_battery / consumo_bateria_por_km
        else:
            bateria_km = 0
        
        if dist_km <= bateria_km:
            # Toda a viagem com bateria (sem emissões)
            return 0.0
        else:
            # Só a parte com combustível gera emissões
            combustao_km = dist_km - bateria_km
            return consumo_combustivel_por_km * 2300.0 * combustao_km
    
    # Fallback
    return 120.0 * dist_km
