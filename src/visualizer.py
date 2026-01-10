"""
Módulo de visualização da simulação.
Responsável por toda a lógica de desenho e animação.
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Visualizer:
    """
    Gerencia a visualização da simulação usando Matplotlib.
    Completamente separado da lógica de negócio.
    """
    
    def __init__(self, simulation, interval=100):
        """
        Inicializa o visualizador.
        
        Args:
            simulation: Instância de Simulation
            interval: Intervalo entre frames em ms (100ms = 10 FPS)
        """
        self.simulation = simulation
        self.interval = interval
        
        # Referências aos elementos visuais
        self.fig = None
        self.ax_graph = None  # Eixo para o grafo
        self.ax_stats = None  # Eixo para as estatísticas
        self.taxi_markers = []
        self.taxi_labels = []
        self.pickup_markers = []
        self.pickup_labels = []
        self.dropoff_markers = []
        self.dropoff_labels = []
        self.title_text = None
        self.stats_text = None
        self.edge_labels = {}  # Referências às labels das arestas para atualização dinâmica
        self.last_time_update = -1  # Último minuto em que atualizámos as labels
    
    def setup_figure(self):
        """Cria e configura a figura com dois painéis."""
        # Cria figura com dois subplots lado a lado
        self.fig = plt.figure(figsize=(24, 12))
        
        # Painel esquerdo: Grafo (70% da largura)
        self.ax_graph = plt.subplot2grid((1, 10), (0, 0), colspan=7)
        
        # Painel direito: Estatísticas (30% da largura)
        self.ax_stats = plt.subplot2grid((1, 10), (0, 7), colspan=3)
        self.ax_stats.axis('off')
        
        # Ajusta o espaçamento entre os painéis
        plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.05, wspace=0.3)
        
        # Desenha o grafo estático e guarda referências às labels das arestas
        self.edge_labels = self.simulation.graph.draw(
            self.ax_graph, 
            requests=None
        )
    
    def create_markers(self):
        """Cria todos os marcadores visuais."""
        self._create_taxi_markers()
        self._create_request_markers()
        self._create_text_elements()
    
    def _create_taxi_markers(self):
        """Cria marcadores para táxis."""
        for taxi in self.simulation.vehicles:
            # Marcador
            marker, = self.ax_graph.plot([], [], 'o', markersize=10, zorder=6)
            self.taxi_markers.append(marker)
            
            # Label
            label = self.ax_graph.text(0, 0, '', fontsize=8, ha='center', zorder=7)
            self.taxi_labels.append(label)
    
    def _create_request_markers(self):
        """Cria marcadores para requests (pickup e dropoff)."""
        for req in self.simulation.requests:
            # Pickup marker (azul)
            p_marker, = self.ax_graph.plot(
                [], [], '*', color='blue', markersize=15,
                markeredgecolor='white', markeredgewidth=1.5, zorder=7
            )
            self.pickup_markers.append(p_marker)
            
            p_label = self.ax_graph.text(
                0, 0, '', fontsize=8, ha='center', 
                color='blue', fontweight='bold', zorder=8
            )
            self.pickup_labels.append(p_label)
            
            # Dropoff marker (laranja)
            d_marker, = self.ax_graph.plot(
                [], [], '*', color='orange', markersize=15,
                markeredgecolor='white', markeredgewidth=1.5, zorder=7
            )
            self.dropoff_markers.append(d_marker)
            
            d_label = self.ax_graph.text(
                0, 0, '', fontsize=8, ha='center',
                color='orange', fontweight='bold', zorder=8
            )
            self.dropoff_labels.append(d_label)
    
    def _create_text_elements(self):
        """Cria elementos de texto (título e estatísticas)."""
        # Título no painel do grafo
        self.title_text = self.ax_graph.text(
            0.5, 1.02, '', transform=self.ax_graph.transAxes,
            ha='center', fontsize=14, fontweight='bold'
        )
        
        # Estatísticas no painel direito
        self.stats_text = self.ax_stats.text(
            0.05, 0.95, '', transform=self.ax_stats.transAxes,
            ha='left', va='top', fontsize=9, family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9, pad=1)
        )
    
    def update_taxi_markers(self):
        """Atualiza posição e cor dos marcadores de táxis."""
        for taxi, marker, label in zip(
            self.simulation.vehicles, 
            self.taxi_markers, 
            self.taxi_labels
        ):
            x, y = taxi.current_position.x, taxi.current_position.y
            
            # Atualiza posição do marcador
            marker.set_data([x], [y])
            
            # Atualiza cor baseada no status
            if taxi.status.name == 'IDLE':
                marker.set_color('green')
            elif taxi.status.name == 'TRAVELING':
                marker.set_color('red')
            else:
                marker.set_color('gray')
            
            # Atualiza label
            label.set_position((x, y + 2))
            label.set_text(f"{taxi.id}")
    
    def update_edge_labels(self):
        """
        Atualiza as labels das arestas com os tempos atuais.
        Os tempos podem mudar devido a eventos de trânsito/clima.
        """
        graph = self.simulation.graph
        
        for edge_pair, label_info in self.edge_labels.items():
            node1_id, node2_id = edge_pair
            
            # Obtém o tempo atual da aresta (já com eventos aplicados)
            current_time = graph.get_edge_time(node1_id, node2_id)
            if current_time is None:
                continue
            
            distance = label_info['distance']
            text_obj = label_info['text_obj']
            
            # Atualiza o texto da label
            new_text = f"{distance:.0f}m\n{current_time:.1f}min"
            text_obj.set_text(new_text)
    
    def update_request_markers(self):
        """Atualiza marcadores de requests (pickup/dropoff)."""
        current_time = self.simulation.current_time
        
        for req, p_marker, p_label, d_marker, d_label in zip(
            self.simulation.requests,
            self.pickup_markers,
            self.pickup_labels,
            self.dropoff_markers,
            self.dropoff_labels
        ):
            # Só mostra o request se já chegou a sua hora
            if req.requested_time > current_time:
                # Request ainda não foi feito - esconde tudo
                p_marker.set_data([], [])
                p_label.set_text('')
                d_marker.set_data([], [])
                d_label.set_text('')
                
            elif req.status == 'pending' or req.status == 'assigned':
                # Mostra pickup point
                # Cor diferente para eco-friendly (verde)
                marker_color = 'green' if req.eco_friendly else 'blue'
                p_marker.set_color(marker_color)
                p_marker.set_data([req.start_point.x], [req.start_point.y])
                p_label.set_position((req.start_point.x, req.start_point.y + 3))
                p_label.set_color(marker_color)
                # Adiciona indicador ECO ao label
                label_text = f"P{req.id}" if req.eco_friendly else f"P{req.id}"
                p_label.set_text(label_text)
                # Esconde dropoff
                d_marker.set_data([], [])
                d_label.set_text('')
                
            elif req.status == 'picked_up':
                # Esconde pickup
                p_marker.set_data([], [])
                p_label.set_text('')
                # Mostra dropoff point
                d_marker.set_data([req.end_point.x], [req.end_point.y])
                d_label.set_position((req.end_point.x, req.end_point.y + 3))
                d_label.set_text(f"D{req.id}")
                
            else:  # completed
                # Esconde ambos
                p_marker.set_data([], [])
                p_label.set_text('')
                d_marker.set_data([], [])
                d_label.set_text('')
    
    def update_text(self):
        """Atualiza título e estatísticas."""
        # Título com tempo
        self.title_text.set_text(
            f"Simulação UberUM - Tempo: {self.simulation.get_time_string()}"
        )
        
        # Contadores de táxis por estado
        idle_vehicles = []
        traveling_vehicles = []
        for v in self.simulation.vehicles:
            if v.status.name == 'IDLE':
                idle_vehicles.append(v)
            elif v.status.name == 'TRAVELING':
                traveling_vehicles.append(v)
        
        # Estatísticas detalhadas
        stats = self.simulation.stats
        stats_str = "=== ESTATISTICAS ===\n\n"
        
        # Requests
        stats_str += "PEDIDOS\n"
        stats_str += f"  [OK] Completados: {stats['requests_completed']}\n"
        stats_str += f"  [>>] Em andamento: {stats.get('requests_in_progress', 0)}\n"
        stats_str += f"  [...] Pendentes: {stats['requests_pending']}\n"
        stats_str += f"  Total: {len(self.simulation.requests)}\n"
        stats_str += "\n"
        
        # Táxis
        stats_str += "TAXIS\n"
        stats_str += f"  [ ] IDLE: {len(idle_vehicles)}\n"
        stats_str += f"  [*] A viajar: {len(traveling_vehicles)}\n"
        stats_str += f"  Total: {len(self.simulation.vehicles)}\n"
        stats_str += "\n"
        
        # Detalhes dos táxis (formato compacto)
        stats_str += "=== VEICULOS ===\n\n"
        for v in self.simulation.vehicles:
            status_icon = "[ ]" if v.status.name == "IDLE" else "[*]"
            
            # Linha 1: ID, nome e status
            stats_str += f"{status_icon} T{v.id}: {v.name[:15]}\n"
            
            # Linha 2: Energia/Combustível (compacto)
            from vehicle.vehicle import Eletric, Combustion, Hybrid
            if isinstance(v.vehicle_type, Eletric):
                battery_pct = v.vehicle_type.battery_percentage()
                battery_bar = self._get_progress_bar(battery_pct, width=8)
                stats_str += f"    Bat {battery_bar} {battery_pct:.0f}%"
            elif isinstance(v.vehicle_type, Combustion):
                fuel_pct = v.vehicle_type.fuel_percentage()
                fuel_bar = self._get_progress_bar(fuel_pct, width=8)
                stats_str += f"    Gas {fuel_bar} {fuel_pct:.0f}%"
            elif isinstance(v.vehicle_type, Hybrid):
                battery_pct = v.vehicle_type.battery_percentage()
                fuel_pct = v.vehicle_type.fuel_percentage()
                battery_bar = self._get_progress_bar(battery_pct, width=6)
                fuel_bar = self._get_progress_bar(fuel_pct, width=6)
                stats_str += f"    Bat {battery_bar}{battery_pct:.0f}% Gas{fuel_bar}{fuel_pct:.0f}%"
            
            # Request e CO2 na mesma linha
            if v.current_request:
                stats_str += f" | Req#{v.current_request.id}"
            
            impact = v.get_environmental_impact()
            stats_str += f" | {impact['total_emissions_g']:.0f}g CO2"
            stats_str += "\n"
        
        self.stats_text.set_text(stats_str)
    
    def _get_progress_bar(self, percentage: float, width: int = 10) -> str:
        """
        Cria uma barra de progresso ASCII.
        
        Args:
            percentage: Percentagem (0-100)
            width: Largura da barra em caracteres
            
        Returns:
            String com a barra de progresso
        """
        filled = int((percentage / 100) * width)
        empty = width - filled
        
        if percentage > 60:
            bar_char = '='
        elif percentage > 30:
            bar_char = '-'
        else:
            bar_char = '.'
        
        return f"[{bar_char * filled}{' ' * empty}]"
    
    def get_all_artists(self):
        """Retorna lista de todos os artistas para blit."""
        # Inclui as labels das arestas para que sejam atualizadas
        edge_label_artists = [info['text_obj'] for info in self.edge_labels.values()]
        
        return (
            self.taxi_markers + 
            self.taxi_labels + 
            self.pickup_markers + 
            self.pickup_labels + 
            self.dropoff_markers + 
            self.dropoff_labels + 
            [self.title_text, self.stats_text] +
            edge_label_artists
        )
    
    def init_animation(self):
        """Inicialização da animação."""
        return self.get_all_artists()
    
    def update_frame(self, frame):
        """
        Atualiza um frame da animação.
        
        Args:
            frame: Número do frame atual
            
        Returns:
            Lista de artistas atualizados
        """
        # Executa um passo da simulação
        step_info = self.simulation.step()
        
        if step_info['finished']:
            return self.get_all_artists()
        
        # Atualiza labels das arestas a cada 30 minutos de simulação
        # (para refletir mudanças de trânsito/clima)
        current_time = self.simulation.current_time
        time_block = current_time // 30  # Bloco de 30 minutos
        if time_block != self.last_time_update:
            self.update_edge_labels()
            self.last_time_update = time_block
        
        # Atualiza todos os elementos visuais
        self.update_taxi_markers()
        self.update_request_markers()
        self.update_text()
        
        return self.get_all_artists()
    
    def run(self):
        """
        Executa a visualização animada completa.
        
        Returns:
            FuncAnimation: Objeto de animação
        """
        # Setup
        self.setup_figure()
        self.create_markers()
        
        # Cria animação
        total_frames = self.simulation.end_time - self.simulation.current_time
        
        anim = FuncAnimation(
            self.fig,
            self.update_frame,
            init_func=self.init_animation,
            frames=total_frames,
            interval=self.interval,
            blit=True,
            repeat=False
        )
        
        plt.show()
        return anim
