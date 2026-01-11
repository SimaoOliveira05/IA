"""
Módulo para gestão de eventos estáticos da simulação.
Inclui condições climáticas, trânsito e fecho de estradas.
Os eventos AFETAM os tempos das arestas do grafo.
"""

from enum import Enum

class WeatherCondition(Enum):
    """Condições climáticas possíveis."""
    CLEAR = "clear"          # Tempo limpo (sem impacto)
    RAIN = "rain"            # Chuva (impacto moderado)
    HEAVY_RAIN = "heavy_rain"  # Chuva forte (impacto alto)
    FOG = "fog"              # Nevoeiro (impacto baixo)
    SNOW = "snow"            # Neve (impacto muito alto)
    
    def get_time_multiplier(self):
        """
        Retorna o fator multiplicador de tempo para esta condição.
        Afeta o tempo real de percurso das arestas.
        """
        multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 1.5,
            WeatherCondition.HEAVY_RAIN: 2,
            WeatherCondition.FOG: 2.5,
            WeatherCondition.SNOW: 5,
        }
        return multipliers.get(self, 1.0)


class TrafficLevel(Enum):
    """Níveis de trânsito possíveis."""
    CLEAR = "clear"           # Trânsito livre
    LIGHT = "light"           # Trânsito leve
    MODERATE = "moderate"     # Trânsito moderado
    HEAVY = "heavy"           # Trânsito intenso
    CONGESTED = "congested"   # Congestionamento
    
    def get_time_multiplier(self):
        """
        Retorna o fator multiplicador de tempo para este nível de trânsito.
        Afeta o tempo real de percurso das arestas.
        """
        multipliers = {
            TrafficLevel.CLEAR: 1.0,
            TrafficLevel.LIGHT: 2,
            TrafficLevel.MODERATE: 3,
            TrafficLevel.HEAVY: 5,
            TrafficLevel.CONGESTED: 8,
        }
        return multipliers.get(self, 1.0)


class EventManager:
    """
    Gerencia eventos estáticos da simulação (clima, trânsito e estradas fechadas).
    Eventos AFETAM os tempos das arestas do grafo.
    """
    
    def __init__(self, graph):
        """
        Inicializa o gestor de eventos.
        
        Args:
            graph: Grafo da simulação
        """
        self.graph = graph
        self.weather_zones = {}  # {node_id: {"condition": WeatherCondition, "start_time": int, "end_time": int}}
        self.traffic_zones = {}  # {node_id: {"level": TrafficLevel, "start_time": int, "end_time": int}}
        self.closed_roads = []   # [(node_id1, node_id2), ...]
    
    def set_weather_zone(self, node_ids, weather_condition, start_time=0, end_time=1440):
        """
        Define condição climática para uma zona (conjunto de nós).
        
        Args:
            node_ids: Lista de IDs de nós afetados
            weather_condition: WeatherCondition a aplicar
            start_time: Minuto do dia em que o evento começa (0-1440, default: 0)
            end_time: Minuto do dia em que o evento termina (0-1440, default: 1440)
        """
        if isinstance(weather_condition, str):
            weather_condition = WeatherCondition(weather_condition)
        
        for node_id in node_ids:
            self.weather_zones[node_id] = {
                "condition": weather_condition,
                "start_time": start_time,
                "end_time": end_time
            }
        
        # Formata os horários para exibição
        start_h, start_m = divmod(start_time, 60)
        end_h, end_m = divmod(end_time, 60)
        time_str = f" ({start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d})" if start_time != 0 or end_time != 1440 else ""
        
        print(f"✓ Clima '{weather_condition.value}' aplicado a {len(node_ids)} nós{time_str}")
    
    def set_traffic_zone(self, node_ids, traffic_level, start_time=0, end_time=1440):
        """
        Define nível de trânsito para uma zona (conjunto de nós).
        
        Args:
            node_ids: Lista de IDs de nós afetados
            traffic_level: TrafficLevel a aplicar
            start_time: Minuto do dia em que o evento começa (0-1440, default: 0)
            end_time: Minuto do dia em que o evento termina (0-1440, default: 1440)
        """
        if isinstance(traffic_level, str):
            traffic_level = TrafficLevel(traffic_level)
        
        for node_id in node_ids:
            self.traffic_zones[node_id] = {
                "level": traffic_level,
                "start_time": start_time,
                "end_time": end_time
            }
        
        # Formata os horários para exibição
        start_h, start_m = divmod(start_time, 60)
        end_h, end_m = divmod(end_time, 60)
        time_str = f" ({start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d})" if start_time != 0 or end_time != 1440 else ""
        
        print(f"✓ Trânsito '{traffic_level.value}' aplicado a {len(node_ids)} nós{time_str}")
    
    def close_road(self, node_id1, node_id2):
        """
        Fecha uma estrada (aresta) entre dois nós.
        
        Args:
            node_id1, node_id2: IDs dos nós conectados pela estrada
        """
        # Marca a aresta como fechada no grafo
        closed = False
        
        # Procura e fecha a aresta em ambas direções
        if node_id1 in self.graph.edges:
            for edge in self.graph.edges[node_id1]:
                if edge['target'] == node_id2:
                    edge['open'] = False
                    closed = True
        
        if node_id2 in self.graph.edges:
            for edge in self.graph.edges[node_id2]:
                if edge['target'] == node_id1:
                    edge['open'] = False
                    closed = True
        
        if closed:
            self.closed_roads.append((node_id1, node_id2))
            print(f"✓ Estrada fechada: {node_id1} ↔ {node_id2}")
        else:
            print(f"⚠ Aviso: Estrada {node_id1} ↔ {node_id2} não encontrada")
    
    def get_weather_at_node(self, node_id, current_time=None):
        """
        Retorna a condição climática de um nó num determinado momento.
        
        Args:
            node_id: ID do nó
            current_time: Tempo atual em minutos (opcional)
            
        Returns:
            WeatherCondition ou CLEAR se clima normal ou fora do intervalo
        """
        if node_id not in self.weather_zones:
            return WeatherCondition.CLEAR
        
        zone = self.weather_zones[node_id]
        
        # Se current_time não fornecido, retorna sempre a condição
        if current_time is None:
            return zone["condition"]
        
        # Verifica se está dentro do intervalo de tempo
        if zone["start_time"] <= current_time <= zone["end_time"]:
            return zone["condition"]
        
        return WeatherCondition.CLEAR
    
    def get_traffic_at_node(self, node_id, current_time=None):
        """
        Retorna o nível de trânsito de um nó num determinado momento.
        
        Args:
            node_id: ID do nó
            current_time: Tempo atual em minutos (opcional)
            
        Returns:
            TrafficLevel ou CLEAR se trânsito livre ou fora do intervalo
        """
        if node_id not in self.traffic_zones:
            return TrafficLevel.CLEAR
        
        zone = self.traffic_zones[node_id]
        
        # Se current_time não fornecido, retorna sempre o nível
        if current_time is None:
            return zone["level"]
        
        # Verifica se está dentro do intervalo de tempo
        if zone["start_time"] <= current_time <= zone["end_time"]:
            return zone["level"]
        
        return TrafficLevel.CLEAR
    
    def get_weather_multiplier(self, node_id, current_time=None):
        """
        Retorna o fator multiplicador de tempo devido ao clima para um nó.
        
        Args:
            node_id: ID do nó
            current_time: Tempo atual em minutos (opcional)
            
        Returns:
            float: Fator multiplicador de tempo (1.0 = sem impacto)
        """
        weather = self.get_weather_at_node(node_id, current_time)
        return weather.get_time_multiplier()
    
    def get_traffic_multiplier(self, node_id, current_time=None):
        """
        Retorna o fator multiplicador de tempo devido ao trânsito para um nó.
        
        Args:
            node_id: ID do nó
            current_time: Tempo atual em minutos (opcional)
            
        Returns:
            float: Fator multiplicador de tempo (1.0 = sem impacto)
        """
        traffic = self.get_traffic_at_node(node_id, current_time)
        return traffic.get_time_multiplier()
    
    def get_combined_multiplier(self, node_id, current_time=None):
        """
        Retorna o fator multiplicador combinado (clima + trânsito) para um nó.
        
        Args:
            node_id: ID do nó
            current_time: Tempo atual em minutos (opcional)
            
        Returns:
            float: Fator multiplicador combinado de tempo
        """
        weather_mult = self.get_weather_multiplier(node_id, current_time)
        traffic_mult = self.get_traffic_multiplier(node_id, current_time)
        # Combina os multiplicadores (efeito composto)
        return weather_mult * traffic_mult
    
    def apply_events_to_edges(self, current_time=None):
        """
        Aplica os efeitos de clima e trânsito aos tempos das arestas do grafo.
        O tempo base é multiplicado pelos fatores de clima e trânsito.
        
        Args:
            current_time: Tempo atual em minutos (opcional, para verificar intervalos)
        """
        affected_edges = 0
        
        for node_id, edges in self.graph.edges.items():
            # Obtém multiplicadores para este nó de origem
            combined_mult = self.get_combined_multiplier(node_id, current_time)
            
            for edge in edges:
                # Guarda o tempo base se ainda não foi guardado
                if 'base_time' not in edge:
                    edge['base_time'] = edge['time']
                
                # Aplica o multiplicador ao tempo base (ou restaura se multiplicador é 1.0)
                edge['time'] = edge['base_time'] * combined_mult
                
                if combined_mult != 1.0:
                    edge['weather'] = self.get_weather_at_node(node_id, current_time).value
                    edge['traffic'] = self.get_traffic_at_node(node_id, current_time).value
                    affected_edges += 1
                else:
                    # Restaura para valores normais
                    edge['weather'] = 'clear'
                    edge['traffic'] = 'clear'
        
        if affected_edges > 0:
            print(f"✓ Efeitos de clima e trânsito aplicados a {affected_edges} arestas")
    
    def is_road_open(self, node_id1, node_id2):
        """
        Verifica se uma estrada está aberta.
        
        Args:
            node_id1, node_id2: IDs dos nós
            
        Returns:
            bool: True se aberta, False se fechada
        """
        return (node_id1, node_id2) not in self.closed_roads and \
               (node_id2, node_id1) not in self.closed_roads
    
    def summary(self):
        """Imprime resumo dos eventos configurados."""
        print("\n" + "="*60)
        print("           🌦️  EVENTOS DA SIMULAÇÃO")
        print("="*60)
        
        # Resumo do clima
        if self.weather_zones:
            print(f"\n📍 Zonas Climáticas: {len(self.weather_zones)} nós afetados")
            weather_counts = {}
            for zone_info in self.weather_zones.values():
                weather = zone_info["condition"].value
                weather_counts[weather] = weather_counts.get(weather, 0) + 1
            
            for weather_type, count in weather_counts.items():
                print(f"   • {weather_type}: {count} nós")
        else:
            print("\n☀️  Sem condições climáticas especiais")
        
        # Resumo do trânsito
        if self.traffic_zones:
            print(f"\n🚗 Zonas de Trânsito: {len(self.traffic_zones)} nós afetados")
            traffic_counts = {}
            for zone_info in self.traffic_zones.values():
                traffic = zone_info["level"].value
                traffic_counts[traffic] = traffic_counts.get(traffic, 0) + 1
            
            for traffic_type, count in traffic_counts.items():
                print(f"   • {traffic_type}: {count} nós")
        else:
            print("\n🛣️  Sem zonas de trânsito especial")
        
        # Resumo das estradas fechadas
        if self.closed_roads:
            print(f"\n🚧 Estradas Fechadas: {len(self.closed_roads)}")
            for road in self.closed_roads[:5]:  # Mostra apenas as primeiras 5
                print(f"   • {road[0]} ↔ {road[1]}")
            if len(self.closed_roads) > 5:
                print(f"   ... e mais {len(self.closed_roads) - 5}")
        else:
            print("\n✅ Todas as estradas abertas")
        
        print("="*60 + "\n")


def parse_time_interval(time_str):
    """
    Converte string de intervalo de tempo para minutos.
    
    Args:
        time_str: String no formato "HH:MM-HH:MM" ou "H-H" (horas simples)
        
    Returns:
        tuple: (start_minutes, end_minutes)
    """
    if "-" not in time_str:
        return 0, 1440  # Dia inteiro
    
    parts = time_str.split("-")
    if len(parts) != 2:
        return 0, 1440
    
    def parse_time(t):
        t = t.strip()
        if ":" in t:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        else:
            return int(t) * 60  # Assume que é apenas hora
    
    return parse_time(parts[0]), parse_time(parts[1])


def load_events_from_config(graph, config):
    """
    Carrega eventos de um dicionário de configuração.
    
    Args:
        graph: Grafo da simulação
        config: Dicionário com 'weather_zones', 'traffic_zones' e 'closed_roads'
        
    Returns:
        EventManager configurado
    
    Exemplo de config:
    {
        "weather_zones": [
            {"nodes": [1, 2, 3, 4], "condition": "rain", "time_interval": "08:00-18:00"},
            {"nodes": [10, 11, 12], "condition": "fog"}
        ],
        "traffic_zones": [
            {"nodes": [5, 6, 7], "level": "heavy", "time_interval": "15:00-17:00"},
            {"nodes": [20, 21], "level": "moderate", "time_interval": "08:00-09:30"}
        ],
        "closed_roads": [
            {"from": 5, "to": 6},
            {"from": 20, "to": 21}
        ]
    }
    """
    event_manager = EventManager(graph)
    
    # Carrega zonas climáticas
    if 'weather_zones' in config:
        for zone in config['weather_zones']:
            # Parse do intervalo de tempo
            time_interval = zone.get('time_interval', None)
            if time_interval:
                start_time, end_time = parse_time_interval(time_interval)
            else:
                start_time, end_time = 0, 1440  # Dia inteiro
            
            event_manager.set_weather_zone(
                zone['nodes'],
                zone['condition'],
                start_time,
                end_time
            )
    
    # Carrega zonas de trânsito
    if 'traffic_zones' in config:
        for zone in config['traffic_zones']:
            # Parse do intervalo de tempo
            time_interval = zone.get('time_interval', None)
            if time_interval:
                start_time, end_time = parse_time_interval(time_interval)
            else:
                start_time, end_time = 0, 1440  # Dia inteiro
            
            event_manager.set_traffic_zone(
                zone['nodes'],
                zone['level'],
                start_time,
                end_time
            )
    
    # Carrega estradas fechadas
    if 'closed_roads' in config:
        for road in config['closed_roads']:
            event_manager.close_road(road['from'], road['to'])
    
    # Aplica efeitos de clima e trânsito aos tempos das arestas
    event_manager.apply_events_to_edges()
    
    # Mostra resumo
    event_manager.summary()
    
    return event_manager
