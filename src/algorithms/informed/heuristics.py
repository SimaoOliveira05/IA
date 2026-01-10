# Funções de heurística centralizadas
from typing import Optional
from graph.position import Position
from refuel_config import PRECO_BATERIA, PRECO_COMBUSTIVEL
from vehicle.vehicle_types import Eletric, Combustion, Hybrid, VehicleType

MAX_SPEED_KMH = 60.0  # Velocidade máxima esperada para estimativa de tempo
COST_PER_KM = 0.50    # Custo por km (combustível/desgaste)
COST_PER_MIN = 0.20   # Custo por minuto (salário motorista/oportunidade)

def calculate_heuristic(pos1: Position, pos2: Position, criterion: str, vehicle_type: Optional[VehicleType] = None, 
                        event_manager=None, node_id: int = None, current_time: int = None) -> float:
	"""
	Calcula a heurística h(n) baseada no critério escolhido.
	
	Args:
		pos1: Posição atual
		pos2: Posição objetivo
		criterion: Tipo de heurística ('distance', 'time', 'cost', 'environmental', 'combined')
		vehicle_type: Tipo de veículo (opcional, necessário para 'cost')
		event_manager: Gestor de eventos (opcional, para 'time' considerar clima/trânsito)
		node_id: ID do nó atual (opcional, usado para heurística de tempo)
		current_time: Tempo atual em minutos (opcional, usado para verificar intervalos)
	
	Returns:
		float: Valor da heurística h(n) em minutos
	"""
	dist_meters = pos1.distance_to(pos2)
	dist_km = dist_meters / 1000.0

	if criterion == 'distance':
		# Heurística de distância euclidiana convertida para tempo
		# Assume velocidade máxima para manter admissibilidade
		return (dist_km / MAX_SPEED_KMH) * 60.0

	elif criterion == 'time':
		# Heurística de tempo estimado COM impactos de clima e trânsito
		# Calcula tempo base assumindo velocidade máxima
		base_time = (dist_km / MAX_SPEED_KMH) * 60.0  # minutos
		
		# Aplica multiplicador combinado de clima + trânsito se disponível
		if event_manager is not None and node_id is not None:
			multiplier = event_manager.get_combined_multiplier(node_id, current_time)
			return base_time * multiplier
		
		return base_time

	elif criterion == 'cost':
		if vehicle_type is None:
			raise ValueError("Para a heurística de custo operacional, forneça o tipo de veículo.")
		
		# Calcula custo em euros
		if isinstance(vehicle_type, Eletric):
			energia_necessaria = vehicle_type.battery_consumption * dist_km  # kWh
			custo_euros = energia_necessaria * PRECO_BATERIA
		elif isinstance(vehicle_type, Combustion):
			combustivel_necessario = vehicle_type.fuel_consumption * dist_km  # L
			custo_euros = combustivel_necessario * PRECO_COMBUSTIVEL
		elif isinstance(vehicle_type, Hybrid):
			bateria_km = vehicle_type.current_battery / vehicle_type.battery_consumption if vehicle_type.battery_consumption > 0 else 0
			if dist_km <= bateria_km:
				energia_necessaria = vehicle_type.battery_consumption * dist_km
				custo_euros = energia_necessaria * PRECO_BATERIA
			else:
				energia_necessaria = vehicle_type.battery_consumption * bateria_km
				combustivel_necessario = vehicle_type.fuel_consumption * (dist_km - bateria_km)
				custo_euros = energia_necessaria * PRECO_BATERIA + combustivel_necessario * PRECO_COMBUSTIVEL
		else:
			custo_euros = dist_km * COST_PER_KM
		
		# Converte custo para tempo equivalente (minutos) para compatibilidade
		EURO_TO_MINUTES = 5.0  # 1 euro = 5 minutos de "custo"
		return custo_euros * EURO_TO_MINUTES

	elif criterion == 'environmental':
		# Heurística de impacto ambiental (emissões CO₂)
		if vehicle_type is None:
			# Sem veículo, assume combustão média
			emissoes_g = 120.0 * dist_km  # 120 g CO₂/km (média combustão)
		else:
			if isinstance(vehicle_type, Eletric):
				emissoes_g = 0.0
			elif isinstance(vehicle_type, Combustion):
				emissoes_g = 120.0 * dist_km
			elif isinstance(vehicle_type, Hybrid):
				bateria_km = vehicle_type.current_battery / vehicle_type.battery_consumption if vehicle_type.battery_consumption > 0 else 0
				if bateria_km >= dist_km:
					emissoes_g = 0.0
				else:
					combustao_km = dist_km - bateria_km
					emissoes_g = 90.0 * combustao_km
			else:
				emissoes_g = 120.0 * dist_km
		
		# Converte emissões para tempo: 100g CO₂ = 1 minuto de "custo ambiental"
		CO2_TO_MINUTES = 0.01
		return emissoes_g * CO2_TO_MINUTES
	
	elif criterion == 'combined':
		# Heurística combinada: média ponderada de todas as outras
		h_distance = calculate_heuristic(pos1, pos2, 'distance', vehicle_type, event_manager, node_id, current_time)
		h_time = calculate_heuristic(pos1, pos2, 'time', vehicle_type, event_manager, node_id, current_time)
		h_environmental = calculate_heuristic(pos1, pos2, 'environmental', vehicle_type, event_manager, node_id, current_time)
		
		# Para custo, usa estimativa genérica se não houver veículo
		if vehicle_type:
			h_cost = calculate_heuristic(pos1, pos2, 'cost', vehicle_type, event_manager, node_id, current_time)
		else:
			custo_euros = dist_km * COST_PER_KM
			EURO_TO_MINUTES = 5.0
			h_cost = custo_euros * EURO_TO_MINUTES
		
		# Média das 4 heurísticas (todas em minutos)
		return (h_distance + h_time + h_cost + h_environmental) / 4.0

	else:
		# Fallback: usa heurística de tempo
		return calculate_heuristic(pos1, pos2, 'time', vehicle_type, event_manager, node_id, current_time)


# Dicionário de heurísticas disponíveis
HEURISTICS = {
	'distance': 'Distância Euclidiana (tempo estimado)',
	'time': 'Tempo Estimado (com clima e trânsito)',
	'cost': 'Custo Operacional (€ → tempo)',
	'environmental': 'Impacto Ambiental (CO₂ → tempo)',
	'combined': 'Combinada (média de todas)',
}