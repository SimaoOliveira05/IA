"""
Funções centralizadas para cálculos de custos e emissões de veículos.
Evita duplicação de código em múltiplos módulos.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vehicle.vehicle_types import VehicleType

# Importa constantes do config
from config import (
    PRECO_BATERIA,
    PRECO_COMBUSTIVEL,
    EMISSIONS_COMBUSTION_G_PER_KM,
    EMISSIONS_HYBRID_G_PER_KM,
)


def calculate_fuel_cost(vehicle_type: 'VehicleType', distance_km: float) -> float:
    """
    Calcula o custo de combustível/energia para uma distância.
    
    Args:
        vehicle_type: Tipo de veículo (Eletric, Combustion, Hybrid)
        distance_km: Distância em quilómetros
        
    Returns:
        float: Custo em euros
    """
    # Import local para evitar circular imports
    from vehicle.vehicle_types import Eletric, Combustion, Hybrid
    
    if vehicle_type is None:
        # Fallback: custo médio
        return distance_km * 0.15
    
    if isinstance(vehicle_type, Eletric):
        # Custo elétrico: consumo (kWh/100km) * distância * preço
        energia_kwh = (vehicle_type.battery_consumption / 100.0) * distance_km
        return energia_kwh * PRECO_BATERIA
    
    elif isinstance(vehicle_type, Combustion):
        # Custo combustão: consumo (L/100km) * distância * preço
        combustivel_l = (vehicle_type.fuel_consumption / 100.0) * distance_km
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
        
        if distance_km <= bateria_km:
            # Toda a viagem com bateria
            energia_kwh = consumo_bateria_por_km * distance_km
            return energia_kwh * PRECO_BATERIA
        else:
            # Parte com bateria, resto com combustível
            energia_kwh = consumo_bateria_por_km * bateria_km
            combustivel_l = consumo_combustivel_por_km * (distance_km - bateria_km)
            return energia_kwh * PRECO_BATERIA + combustivel_l * PRECO_COMBUSTIVEL
    
    # Fallback
    return distance_km * 0.15


def calculate_emissions(vehicle_type: 'VehicleType', distance_km: float, 
                        battery_level_before: float = None) -> float:
    """
    Calcula as emissões de CO₂ para uma distância.
    Usa fórmula consistente baseada nas constantes de config.py.
    
    Args:
        vehicle_type: Tipo de veículo (Eletric, Combustion, Hybrid)
        distance_km: Distância em quilómetros
        battery_level_before: Para híbridos, nível de bateria ANTES do consumo (opcional)
        
    Returns:
        float: Emissões em gramas de CO₂
    """
    # Import local para evitar circular imports
    from vehicle.vehicle_types import Eletric, Combustion, Hybrid
    
    if vehicle_type is None:
        # Fallback: assume combustão típica
        return EMISSIONS_COMBUSTION_G_PER_KM * distance_km
    
    if isinstance(vehicle_type, Eletric):
        # Elétricos não têm emissões diretas
        return 0.0
    
    elif isinstance(vehicle_type, Combustion):
        # Combustão: usa constante fixa (120 g/km)
        return EMISSIONS_COMBUSTION_G_PER_KM * distance_km
    
    elif isinstance(vehicle_type, Hybrid):
        # Híbrido: depende de quanto usa de cada fonte
        consumo_bateria_por_km = vehicle_type.battery_consumption / 100.0 if vehicle_type.battery_consumption > 0 else 0
        
        # Usa nível de bateria antes do consumo se fornecido
        battery_level = battery_level_before if battery_level_before is not None else vehicle_type.current_battery
        
        # Quantos km conseguia percorrer com bateria
        if consumo_bateria_por_km > 0:
            bateria_km = battery_level / consumo_bateria_por_km
        else:
            bateria_km = 0
        
        if bateria_km >= distance_km:
            # Toda a viagem com bateria (sem emissões)
            return 0.0
        else:
            # Só a parte com combustível gera emissões
            combustao_km = distance_km - bateria_km
            return EMISSIONS_HYBRID_G_PER_KM * combustao_km
    
    # Fallback
    return EMISSIONS_COMBUSTION_G_PER_KM * distance_km


def get_energy_percentage(vehicle_type: 'VehicleType') -> dict:
    """
    Obtém percentagens de energia do veículo.
    
    Args:
        vehicle_type: Tipo de veículo
        
    Returns:
        dict: {'battery': float ou None, 'fuel': float ou None}
    """
    # Import local para evitar circular imports
    from vehicle.vehicle_types import Eletric, Combustion, Hybrid
    
    result = {'battery': None, 'fuel': None}
    
    if isinstance(vehicle_type, Eletric):
        result['battery'] = vehicle_type.battery_percentage()
    elif isinstance(vehicle_type, Combustion):
        result['fuel'] = vehicle_type.fuel_percentage()
    elif isinstance(vehicle_type, Hybrid):
        result['battery'] = vehicle_type.battery_percentage()
        result['fuel'] = vehicle_type.fuel_percentage()
    
    return result


def calculate_total_fuel_cost_consumed(vehicle_type: 'VehicleType') -> float:
    """
    Calcula o custo total do combustível/energia JÁ CONSUMIDO pelo veículo.
    Baseado na diferença entre capacidade máxima e nível atual.
    
    Args:
        vehicle_type: Tipo de veículo
        
    Returns:
        float: Custo total em euros
    """
    # Import local para evitar circular imports
    from vehicle.vehicle_types import Eletric, Combustion, Hybrid
    
    if isinstance(vehicle_type, Eletric):
        energia_consumida = vehicle_type.battery_capacity - vehicle_type.current_battery
        return energia_consumida * PRECO_BATERIA
    
    elif isinstance(vehicle_type, Combustion):
        combustivel_consumido = vehicle_type.fuel_capacity - vehicle_type.current_fuel
        return combustivel_consumido * PRECO_COMBUSTIVEL
    
    elif isinstance(vehicle_type, Hybrid):
        energia_consumida = vehicle_type.battery_capacity - vehicle_type.current_battery
        combustivel_consumido = vehicle_type.fuel_capacity - vehicle_type.current_fuel
        return (energia_consumida * PRECO_BATERIA + 
                combustivel_consumido * PRECO_COMBUSTIVEL)
    
    return 0.0
