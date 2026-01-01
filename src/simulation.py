"""
Módulo de simulação do sistema de táxis.
Responsável pela lógica de negócio da simulação.
"""

from refuel_helper import (
    needs_refuel, 
    get_refuel_time, 
    find_nearest_station, 
    get_station_type_for_vehicle,
    calculate_total_distance
)
from vehicle.vehicle_types import Eletric

class Simulation:
    """
    Gerencia a lógica de simulação de táxis e requests.
    Separada da visualização para melhor modularização.
    """
    
    def __init__(self, database, search_algorithm, time_step=1):
        """
        Inicializa a simulação.
        
        Args:
            database: Database contendo veículos, grafo e requests
            search_algorithm: Função de algoritmo de procura a usar
            time_step: Quantos minutos avançam a cada tick (padrão: 1)
        """
        self.db = database
        self.search_algorithm = search_algorithm
        self.vehicles = database.vehicles
        self.requests = database.requests
        self.graph = database.graph
        
        # Configuração de tempo
        self.time_step = time_step  # Minutos que avançam por tick
        
        # Estado da simulação
        self.current_time = 8 * 60  # 8:00 em minutos
        self.end_time = 20 * 60     # 20:00 em minutos
        
        # Estatísticas
        self.stats = {
            'requests_completed': 0,
            'requests_pending': len(self.requests),
            'total_distance': 0,
            'total_time': 0
        }
    
    def reset(self):
        """Reset da simulação para estado inicial."""
        self.current_time = 8 * 60
        self.stats = {
            'requests_completed': 0,
            'requests_pending': len(self.requests),
            'total_distance': 0,
            'total_time': 0
        }
    
    def is_finished(self):
        """Verifica se a simulação terminou."""
        return self.current_time >= self.end_time
    

    def get_available_vehicles(self):
        """Retorna lista de veículos disponíveis (IDLE)."""
        return [v for v in self.vehicles if v.status.name == 'IDLE']
    
    def get_available_vehicles_for_request(self, request):
        """
        Retorna lista de veículos disponíveis e compatíveis com o request.
        Se o cliente preferir eco-friendly, apenas veículos elétricos são considerados.
        
        Args:
            request: Request a ser verificado
            
        Returns:
            Lista de veículos disponíveis e compatíveis
        """
        available = self.get_available_vehicles()
        
        # Filtra por preferência ambiental
        if request.eco_friendly:
            # Apenas veículos elétricos
            available = [v for v in available if isinstance(v.vehicle_type, Eletric)]
            
        return available


    
    def assign_request_to_vehicle(self, request):
        """
        Atribui um request ao melhor veículo disponível.
        Considera necessidade de abastecimento na escolha.
        Respeita preferências ambientais do cliente.
        
        Args:
            request: Request a ser atribuído
            
        Returns:
            Vehicle atribuído ou None se não houver disponível
        """
        available_vehicles = self.get_available_vehicles_for_request(request)
        
        if not available_vehicles:
            if request.eco_friendly:
                print(f"⚠️  Request {request.id} (ECO-FRIENDLY) não pode ser atendido: sem veículos elétricos disponíveis")
            return None
        
        best_vehicle = None
        best_cost = float('inf')
        best_paths = None
        best_refuel_info = None
        
        for vehicle in available_vehicles:
            # Caminho: veículo → pickup
            cost1, time1, path1 = self.search_algorithm(
                vehicle.current_position, 
                request.start_point, 
                self.graph
            )
            
            # Caminho: pickup → destino
            cost2, time2, path2 = self.search_algorithm(
                request.start_point, 
                request.end_point, 
                self.graph
            )
            
            # Calcula distância total da viagem completa
            total_distance = calculate_total_distance(self.graph, path1)
            total_distance += calculate_total_distance(self.graph, path2)
            
            # Verifica se precisa abastecer
            refuel_needed = needs_refuel(vehicle, total_distance)
            refuel_time = 0
            refuel_station = None
            refuel_path = None
            
            if refuel_needed:
                # Encontra estação mais próxima
                station_type = get_station_type_for_vehicle(vehicle)
                refuel_station = find_nearest_station(
                    self.graph, 
                    vehicle.current_position, 
                    station_type
                )
                
                if refuel_station:
                    # Calcula caminho até a estação
                    station_cost, station_time, station_path = self.search_algorithm(
                        vehicle.current_position,
                        refuel_station.position,
                        self.graph
                    )
                    
                    # Recalcula caminho da estação até o pickup
                    cost1_new, time1_new, path1_new = self.search_algorithm(
                        refuel_station.position,
                        request.start_point,
                        self.graph
                    )
                    
                    # Tempo total de abastecimento (baseado no tipo de estação)
                    refuel_time = get_refuel_time(vehicle, station_type)
                    
                    # Ajusta custos
                    cost1 = station_cost + cost1_new
                    time1 = station_time + refuel_time + time1_new
                    
                    # Atualiza caminhos
                    refuel_path = station_path
                    path1 = path1_new
            
            total_cost = cost1 + cost2
            
            if total_cost < best_cost:
                best_cost = total_cost
                best_vehicle = vehicle
                best_paths = (time1, time2, path1, path2)
                best_refuel_info = (refuel_needed, refuel_station, refuel_path, refuel_time, station_type if refuel_needed else None)
        
        if best_vehicle and best_paths:
            time_to_pickup, trip_time, path_to_pickup, path_to_dest = best_paths
            refuel_needed, refuel_station, refuel_path, refuel_time, station_type = best_refuel_info
            
            # Se precisa abastecer, adiciona informação ao veículo
            if refuel_needed and refuel_station and refuel_path:
                print(f"⚠ Veículo {best_vehicle.id} precisa abastecer!")
                print(f"   Estação: Nó {refuel_station.id} ({refuel_station.node_type})")
                print(f"   Tempo de abastecimento: {refuel_time:.1f} min")
                
                # Passa informação de abastecimento (incluindo tipo de estação)
                refuel_info = (refuel_path, refuel_station.id, refuel_time, station_type)
            else:
                refuel_info = None
            
            best_vehicle.assign(
                request, 
                path_to_pickup, 
                path_to_dest, 
                self.graph,
                refuel_info=refuel_info
            )
            
            # Atualiza estatísticas
            self.stats['total_distance'] += best_cost
            self.stats['total_time'] += time_to_pickup + trip_time
        
        return best_vehicle
    
    def process_new_requests(self):
        """Processa requests que chegam no tempo atual e ainda não foram atribuídos."""
        new_requests = [
            r for r in self.requests 
            if r.requested_time <= self.current_time and r.status == 'pending'  # Apenas não atribuídos
        ]
        
        for request in new_requests:
            vehicle = self.assign_request_to_vehicle(request)
            if vehicle:
                # Request foi atribuído com sucesso, status mudou para 'assigned'
                pass
        
        return len(new_requests)
    
    def update_vehicles(self):
        """Atualiza estado de todos os veículos."""
        for vehicle in self.vehicles:
            vehicle.update_status(self.current_time, self.time_step)
    
    def update_statistics(self):
        """Atualiza estatísticas da simulação."""
        self.stats['requests_completed'] = sum(
            1 for r in self.requests if r.status == 'completed'
        )
        # Pendentes = não atribuídos (status 'pending')
        # 'assigned' e 'picked_up' não contam como pendentes
        self.stats['requests_pending'] = sum(
            1 for r in self.requests if r.status == 'pending'
        )
        # Opcional: adicionar estatística de requests em andamento
        self.stats['requests_in_progress'] = sum(
            1 for r in self.requests if r.status in ['assigned', 'picked_up']
        )
    
    def step(self):
        """
        Executa um passo (tick) da simulação.
        
        Returns:
            dict: Informação sobre o passo executado
        """
        if self.is_finished():
            return {'finished': True}
        
        # Processa novos requests
        new_requests = self.process_new_requests()
        
        # Atualiza veículos
        self.update_vehicles()
        
        # Atualiza estatísticas
        self.update_statistics()
        
        # Avança tempo usando time_step
        self.current_time += self.time_step
        
        return {
            'finished': False,
            'time': self.current_time,
            'new_requests': new_requests,
            'stats': self.stats.copy()
        }
    
    def run_batch(self):
        """
        Executa a simulação completa sem visualização.
        Útil para testes e benchmarks.
        
        Returns:
            dict: Estatísticas finais
        """
        while not self.is_finished():
            self.step()
        
        return self.stats
    
    def get_time_string(self):
        """Retorna string formatada do tempo atual."""
        hours = self.current_time // 60
        minutes = self.current_time % 60
        return f"{hours:02d}:{minutes:02d}"
