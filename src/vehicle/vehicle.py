"""
Sistema de veículos para simulação de táxis.
Define o estado, comportamento e movimento dos veículos.
"""
from enum import Enum
from typing import Optional, List, Tuple, TYPE_CHECKING, Dict, Any

from graph.position import Position
from vehicle.vehicle_types import VehicleType, Eletric, Combustion, Hybrid

if TYPE_CHECKING:
    from request import Request
    from graph.graph import Graph


class Vehicle_Status(Enum):
    """Representa o estado atual do veículo."""
    IDLE = 0
    TRAVELING = 1
    REFUELING = 2
    RECHARGING = 3


class Vehicle:
    """
    Representa um veículo individual na simulação.
    Gere movimento, abastecimento e atribuição de pedidos.
    """
    
    def __init__(
        self,
        id: int,
        name: str,
        vehicle_type: VehicleType,
        capacity: int,
        driver: str,
        status: Vehicle_Status,
        start_point: Position
    ) -> None:
        # ===== Identificação =====
        self.id: int = id
        self.name: str = name
        self.vehicle_type: VehicleType = vehicle_type
        self.capacity: int = capacity
        self.driver: str = driver
        self.status: Vehicle_Status = status

        # ===== Posição e navegação =====
        self.current_position: Position = start_point
        self.current_node_id: Optional[int] = None
        self.graph: Optional['Graph'] = None

        # ===== Estado do pedido =====
        self.passengers: int = 0
        self.current_request: Optional['Request'] = None
        self.phase: Optional[str] = None  # 'to_refuel', 'refueling', 'to_pickup', 'to_dropoff'

        # ===== Abastecimento =====
        self.needs_refuel: bool = False
        self.refuel_node_id: Optional[int] = None
        self.refuel_station_type: Optional[str] = None  # "fuel" ou "charging"
        self.refuel_time_remaining: float = 0.0

        # ===== Caminhos planejados =====
        self.path: List[int] = []
        self.path_to_pickup: List[int] = []
        self.path_to_dropoff: List[int] = []

        # ===== Movimento entre arestas =====
        self.current_edge_from: Optional[int] = None
        self.current_edge_to: Optional[int] = None
        self.edge_travel_time: float = 0.0
        self.time_remaining_on_edge: float = 0.0
        
        # ===== Impacto Ambiental =====
        self.total_emissions: float = 0.0  # Total de CO₂ emitido em gramas
        self.total_distance_traveled: float = 0.0  # Distância total percorrida em metros

    # ========================================
    # ATRIBUIÇÃO DE PEDIDOS
    # ========================================

    def assign(
        self,
        request: 'Request',
        path_to_pickup: Optional[List[int]],
        path_to_dropoff: Optional[List[int]],
        graph: 'Graph',
        refuel_info: Optional[Tuple[Optional[List[int]], int, float, str]] = None
    ) -> None:
        """
        Atribui um pedido ao veículo com os caminhos calculados.
        
        Args:
            request: Pedido a atribuir
            path_to_pickup: Caminho até o pickup (ou da estação ao pickup se houver refuel)
            path_to_dropoff: Caminho do pickup ao destino
            graph: Grafo da cidade
            refuel_info: Tupla (refuel_path, refuel_node_id, refuel_time, station_type) se precisar abastecer
        """
        self.current_request = request
        self.graph = graph
        self.passengers = 0
        
        # Atualiza request
        request.assigned_vehicle = self
        request.status = 'assigned'
        
        # Configura abastecimento se necessário
        if refuel_info and refuel_info[0]:
            self._setup_refuel_phase(refuel_info, path_to_pickup)
        else:
            self._setup_pickup_phase(path_to_pickup)
        
        # Guarda caminho para o destino final
        self.path_to_dropoff = path_to_dropoff.copy() if path_to_dropoff else []
        
        # Inicia movimento
        self.advance_to_next_edge()

    def _setup_refuel_phase(
        self,
        refuel_info: Tuple[Optional[List[int]], int, float, str],
        path_to_pickup: Optional[List[int]]
    ) -> None:
        """Configura a fase de abastecimento."""
        refuel_path, refuel_node_id, refuel_time, station_type = refuel_info
        
        self.needs_refuel = True
        self.refuel_node_id = refuel_node_id
        self.refuel_station_type = station_type
        self.refuel_time_remaining = refuel_time
        self.phase = 'to_refuel'
        self.status = Vehicle_Status.TRAVELING
        
        self.path = refuel_path.copy() if refuel_path else []
        self.path_to_pickup = path_to_pickup.copy() if path_to_pickup else []

    def _setup_pickup_phase(self, path_to_pickup: Optional[List[int]]) -> None:
        """Configura a fase de pickup (sem abastecimento)."""
        self.needs_refuel = False
        self.phase = 'to_pickup'
        self.status = Vehicle_Status.TRAVELING
        self.path = path_to_pickup.copy() if path_to_pickup else []

    # ========================================
    # NAVEGAÇÃO E MOVIMENTO
    # ========================================

    def advance_to_next_edge(self) -> None:
        """Avança para a próxima aresta do caminho."""
        if len(self.path) >= 2:
            self._start_edge_travel()
        elif len(self.path) == 1:
            self._arrive_at_destination()
        else:
            self.status = Vehicle_Status.IDLE

    def _start_edge_travel(self) -> None:
        """Inicia viagem numa nova aresta."""
        self.current_edge_from = self.path[0]
        self.current_edge_to = self.path[1]
        
        # Busca tempo da aresta no grafo
        edges: List[Dict[str, Any]] = self.graph.edges.get(self.current_edge_from, [])
        edge_time: float = 0.0
        for edge in edges:
            if edge["target"] == self.current_edge_to:
                edge_time = edge["time"]
                break
        
        self.edge_travel_time = edge_time
        self.time_remaining_on_edge = edge_time
        self.path.pop(0)

    def _arrive_at_destination(self) -> None:
        """Processa chegada ao destino atual."""
        self.current_node_id = self.path[0]
        node = self.graph.get_node(self.current_node_id)
        if node:
            self.current_position = node.position
        
        # Processa transição de fase
        if self.phase == 'to_refuel':
            self._transition_to_refueling()
        elif self.phase == 'to_pickup':
            self._transition_to_dropoff()
        elif self.phase == 'to_dropoff':
            self._complete_trip()

    def _transition_to_refueling(self) -> None:
        """Transição: chegou à estação de abastecimento."""
        print(f"✓ Veículo {self.id} chegou à estação (nó {self.current_node_id})")
        self.phase = 'refueling'
        self.status = Vehicle_Status.REFUELING if hasattr(Vehicle_Status, 'REFUELING') else Vehicle_Status.IDLE

    def _transition_to_dropoff(self) -> None:
        """Transição: apanhou passageiro, vai para destino."""
        self.phase = 'to_dropoff'
        self.passengers = self.current_request.passengers if self.current_request else 0
        if self.current_request:
            self.current_request.status = 'picked_up'
        self.path = self.path_to_dropoff.copy()
        self.advance_to_next_edge()

    def _complete_trip(self) -> None:
        """Transição: terminou a viagem completa."""
        if self.current_request:
            self.current_request.status = 'completed'
        self._reset_to_idle()

    def _reset_to_idle(self) -> None:
        """Reinicia o veículo para estado idle."""
        self.status = Vehicle_Status.IDLE
        self.phase = None
        self.passengers = 0
        self.current_request = None
        self.path = []
        self.current_edge_from = None
        self.current_edge_to = None
        self.needs_refuel = False

    # ========================================
    # ATUALIZAÇÃO DE ESTADO
    # ========================================

    def update_status(self, current_time: int, time_step: int = 1) -> None:
        """
        Atualiza o estado do veículo a cada tick.
        
        Args:
            current_time: Tempo atual da simulação em minutos
            time_step: Quantos minutos avançam neste tick (padrão: 1)
        """
        # Processa abastecimento
        if self.phase == 'refueling':
            self._process_refueling(time_step)
            return
        
        # Processa viagem
        if self.status != Vehicle_Status.TRAVELING:
            return
        
        if self.current_edge_from is None or self.current_edge_to is None:
            return
        
        self._process_travel(time_step)

    def _process_refueling(self, time_step: int) -> None:
        """Processa o abastecimento do veículo."""
        self.refuel_time_remaining -= time_step
        
        if self.refuel_time_remaining <= 0:
            print(f"✓ Veículo {self.id} terminou de abastecer")
            self._complete_refuel()
            
            # Muda para fase to_pickup
            self.phase = 'to_pickup'
            self.status = Vehicle_Status.TRAVELING
            self.path = self.path_to_pickup.copy()
            self.refuel_time_remaining = 0
            self.refuel_station_type = None
            self.advance_to_next_edge()

    def _complete_refuel(self) -> None:
        """Completa o abastecimento baseado no tipo de veículo."""
        if isinstance(self.vehicle_type, Eletric):
            self.vehicle_type.current_battery = self.vehicle_type.battery_capacity
        elif isinstance(self.vehicle_type, Combustion):
            self.vehicle_type.current_fuel = self.vehicle_type.fuel_capacity
        elif isinstance(self.vehicle_type, Hybrid):
            # Híbrido: abastece baseado no tipo de estação
            if self.refuel_station_type == "fuel":
                self.vehicle_type.current_fuel = self.vehicle_type.fuel_capacity
                print(f"   Combustível reabastecido: 100%")
            elif self.refuel_station_type == "charging":
                self.vehicle_type.current_battery = self.vehicle_type.battery_capacity
                print(f"   Bateria recarregada: 100%")

    def _process_travel(self, time_step: int) -> None:
        """Processa o movimento do veículo durante a viagem."""
        # Guarda posição anterior para calcular distância
        old_position: Position = Position(self.current_position.x, self.current_position.y)
        
        # Decrementa tempo restante na aresta
        self.time_remaining_on_edge -= time_step
        
        if self.time_remaining_on_edge <= 0:
            # Chegou ao fim da aresta
            self._complete_edge_travel(old_position)
        else:
            # Interpola posição ao longo da aresta
            self._interpolate_position(old_position)

    def _complete_edge_travel(self, old_position: Position) -> None:
        """Completa a viagem numa aresta."""
        self.current_node_id = self.current_edge_to
        node = self.graph.get_node(self.current_node_id)
        if node:
            self.current_position = node.position
        
        # Calcula distância percorrida e consome energia
        distance_traveled: float = old_position.distance_to(self.current_position)
        self._consume_energy(distance_traveled)
        
        # Avança para próxima aresta
        self.advance_to_next_edge()

    def _interpolate_position(self, old_position: Position) -> None:
        """Interpola a posição do veículo ao longo da aresta."""
        if self.edge_travel_time > 0:
            frac: float = 1 - (self.time_remaining_on_edge / self.edge_travel_time)
            frac = max(0.0, min(1.0, frac))
            
            # Obtém posições dos nós
            node_from = self.graph.get_node(self.current_edge_from)
            node_to = self.graph.get_node(self.current_edge_to)
            
            if node_from and node_to:
                x1, y1 = node_from.position.x, node_from.position.y
                x2, y2 = node_to.position.x, node_to.position.y
                nx: float = x1 + frac * (x2 - x1)
                ny: float = y1 + frac * (y2 - y1)
                self.current_position = Position(nx, ny)
                
                # Consome energia pela distância percorrida
                distance_traveled: float = old_position.distance_to(self.current_position)
                self._consume_energy(distance_traveled)

    def _consume_energy(self, distance: float) -> None:
        """
        Consome energia/combustível baseado na distância percorrida.
        Calcula e rastreia emissões de CO₂.
        
        Args:
            distance: Distância percorrida em metros
        """
        if distance > 0:
            # Calcula emissões ANTES de consumir (para híbridos que podem mudar de modo)
            emissions = self.vehicle_type.calculate_emissions(distance)
            self.total_emissions += emissions
            
            # Consome energia
            self.vehicle_type.consume(distance)
            
            # Rastreia distância total
            self.total_distance_traveled += distance
    
    def get_environmental_impact(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o impacto ambiental do veículo.
        
        Returns:
            Dict com total_emissions (g), total_distance (km), average_emissions (g/km)
        """
        distance_km = self.total_distance_traveled / 1000
        avg_emissions = self.total_emissions / distance_km if distance_km > 0 else 0
        
        return {
            'total_emissions_g': self.total_emissions,
            'total_distance_km': distance_km,
            'average_emissions_per_km': avg_emissions,
            'vehicle_type_emissions_rate': self.vehicle_type.get_emissions_rate()
        }
