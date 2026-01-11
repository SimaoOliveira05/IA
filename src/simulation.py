"""
Módulo de simulação do sistema de táxis.
Responsável pela lógica de negócio da simulação.
"""

import time
from refuel_helper import (
    needs_refuel, 
    get_refuel_time, 
    find_nearest_station, 
    get_station_type_for_vehicle,
)
from vehicle.vehicle_types import Eletric

class Simulation:
    """
    Gerencia a lógica de simulação de táxis e requests.
    Separada da visualização para melhor modularização.
    """
    
    def __init__(self, database, search_algorithm, time_step=1, heuristic=None):
        """
        Inicializa a simulação.
        
        Args:
            database: Database contendo veículos, grafo e requests
            search_algorithm: Função de algoritmo de procura a usar
            time_step: Quantos minutos avançam a cada tick (padrão: 1)
            heuristic: Heurística a usar (para algoritmos informados)
        """
        self.db = database
        self.search_algorithm_func = search_algorithm
        self.heuristic = heuristic
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
            'total_time': 0,
            'total_fuel_cost': 0.0,
            'requests_not_served': 0
        }
        
        # Estatísticas de tempo de procura do algoritmo
        self.search_times = []  # Lista de tempos de cada procura (em ms)
    
    def search_algorithm(self, start, goal, graph, vehicle=None):
        """
        Wrapper para chamar o algoritmo de busca com ou sem heurística.
        Agora normalizado: tanto A* como Greedy usam 'criterion'.
        Mede o tempo de execução de cada procura.
        
        Args:
            start: Posição inicial
            goal: Posição objetivo  
            graph: Grafo
            vehicle: Veículo (opcional, para passar vehicle_type às heurísticas)
        """
        import inspect
        sig = inspect.signature(self.search_algorithm_func)
        params = sig.parameters
        
        # Mede tempo de execução
        start_time = time.perf_counter()
        
        # Prepara vehicle_type se disponível
        vehicle_type = vehicle.vehicle_type if vehicle else None
        
        # Verifica se o algoritmo aceita 'criterion' (algoritmos informados: A*, Greedy)
        if 'criterion' in params and self.heuristic:
            # Prepara argumentos opcionais
            kwargs = {'criterion': self.heuristic}
            
            if 'vehicle_type' in params:
                kwargs['vehicle_type'] = vehicle_type
            
            # Passa event_manager e current_time para heurísticas de tempo/trânsito
            if 'event_manager' in params and hasattr(self.db, 'event_manager'):
                kwargs['event_manager'] = self.db.event_manager
            
            if 'current_time' in params:
                kwargs['current_time'] = self.current_time
            
            result = self.search_algorithm_func(start, goal, graph, **kwargs)
        else:
            # Algoritmos não informados (BFS, DFS, Uniform Cost)
            # Uniform Cost também aceita vehicle_type para cálculo de custo
            if 'vehicle_type' in params:
                result = self.search_algorithm_func(start, goal, graph, vehicle_type=vehicle_type)
            else:
                result = self.search_algorithm_func(start, goal, graph)
        
        # Regista tempo de execução (em milissegundos)
        end_time = time.perf_counter()
        search_time_ms = (end_time - start_time) * 1000
        self.search_times.append(search_time_ms)
        
        return result
    
    def reset(self):
        """Reset da simulação para estado inicial."""
        self.current_time = 8 * 60
        self.stats = {
            'requests_completed': 0,
            'requests_pending': len(self.requests),
            'total_distance': 0,
            'total_time': 0
        }
        self.search_times = []  # Reset tempos de procura
    
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
                return None
        
        best_vehicle = None
        best_cost = float('inf')
        best_paths = None
        best_refuel_info = None
        best_real_distance = 0.0  # Inicializa para evitar erro se nenhum veículo for compatível
        
        for vehicle in available_vehicles:
            # Verifica se o veículo tem capacidade suficiente para o pedido
            if hasattr(request, 'passengers') and vehicle.capacity < request.passengers:
                continue

            # Caminho: veículo → pickup
            # IMPORTANTE: Os algoritmos retornam (distância_metros, tempo_minutos, path)
            # Usamos TEMPO como critério de escolha do melhor veículo
            dist1, time1, path1 = self.search_algorithm(
                vehicle.current_position, 
                request.start_point, 
                self.graph,
                vehicle=vehicle
            )

            # Caminho: pickup → destino
            dist2, time2, path2 = self.search_algorithm(
                request.start_point, 
                request.end_point, 
                self.graph,
                vehicle=vehicle
            )

            total_distance = dist1 + dist2

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
                    station_dist, station_time, station_path = self.search_algorithm(
                        vehicle.current_position,
                        refuel_station.position,
                        self.graph,
                        vehicle=vehicle
                    )

                    # Recalcula caminho da estação até o pickup
                    dist1_new, time1_new, path1_new = self.search_algorithm(
                        refuel_station.position,
                        request.start_point,
                        self.graph,
                        vehicle=vehicle
                    )

                    # Tempo total de abastecimento (baseado no tipo de estação)
                    refuel_time = get_refuel_time(vehicle, station_type)

                    # Ajusta tempo total (critério de otimização é TEMPO)
                    time1 = station_time + refuel_time + time1_new

                    # Atualiza caminhos
                    refuel_path = station_path
                    path1 = path1_new
                    
                    # IMPORTANTE: Recalcula distância REAL com o novo caminho
                    total_distance = station_dist + dist1_new + dist2

            total_time_cost = time1 + time2

            if total_time_cost < best_cost:
                best_cost = total_time_cost
                best_vehicle = vehicle
                best_paths = (time1, time2, path1, path2)
                best_refuel_info = (refuel_needed, refuel_station, refuel_path, refuel_time, station_type if refuel_needed else None)
                best_real_distance = total_distance  # Guarda a distância REAL do melhor caminho
        
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
            
            # Atualiza estatísticas - USA DISTÂNCIA REAL, não o tempo otimizado
            self.stats['total_distance'] += best_real_distance
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
        
        # Calcula custo total de combustível
        from refuel_config import PRECO_BATERIA, PRECO_COMBUSTIVEL
        from vehicle.vehicle_types import Eletric, Combustion, Hybrid
        
        total_fuel_cost = 0.0
        for vehicle in self.vehicles:
            vtype = vehicle.vehicle_type
            
            if isinstance(vtype, Eletric):
                # Custo = energia consumida * preço bateria
                energia_consumida = vtype.battery_capacity - vtype.current_battery
                total_fuel_cost += energia_consumida * PRECO_BATERIA
            
            elif isinstance(vtype, Combustion):
                # Custo = combustível consumido * preço combustível
                combustivel_consumido = vtype.fuel_capacity - vtype.current_fuel
                total_fuel_cost += combustivel_consumido * PRECO_COMBUSTIVEL
            
            elif isinstance(vtype, Hybrid):
                # Custo = energia + combustível consumidos
                energia_consumida = vtype.battery_capacity - vtype.current_battery
                combustivel_consumido = vtype.fuel_capacity - vtype.current_fuel
                total_fuel_cost += (energia_consumida * PRECO_BATERIA + 
                                   combustivel_consumido * PRECO_COMBUSTIVEL)
        
        self.stats['total_fuel_cost'] = total_fuel_cost
        
        # Requests não atendidos (finalizou simulação com status 'pending')
        if self.is_finished():
            self.stats['requests_not_served'] = self.stats['requests_pending']
        
        # Estatísticas de tempo de procura do algoritmo
        if self.search_times:
            self.stats['search_count'] = len(self.search_times)
            self.stats['search_time_total_ms'] = sum(self.search_times)
            self.stats['search_time_avg_ms'] = sum(self.search_times) / len(self.search_times)
            self.stats['search_time_min_ms'] = min(self.search_times)
            self.stats['search_time_max_ms'] = max(self.search_times)
        else:
            self.stats['search_count'] = 0
            self.stats['search_time_total_ms'] = 0
            self.stats['search_time_avg_ms'] = 0
            self.stats['search_time_min_ms'] = 0
            self.stats['search_time_max_ms'] = 0
    
    def step(self):
        """
        Executa um passo (tick) da simulação.
        
        Returns:
            dict: Informação sobre o passo executado
        """
        if self.is_finished():
            return {'finished': True}
        
        # Aplica eventos de clima/trânsito baseados no tempo atual
        # (atualiza tempos das arestas a cada 30 minutos de simulação)
        if self.db.event_manager and self.current_time % 30 == 0:
            self.db.event_manager.apply_events_to_edges(self.current_time)
        
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
