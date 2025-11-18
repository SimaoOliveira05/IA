"""
Módulo para gestão de eventos estáticos da simulação.
Inclui condições climáticas e fecho de estradas.
"""

from enum import Enum

class WeatherCondition(Enum):
    """Condições climáticas possíveis."""
    CLEAR = "clear"          # Tempo limpo (sem impacto)
    RAIN = "rain"            # Chuva (aumenta tempo ~30%)
    HEAVY_RAIN = "heavy_rain"  # Chuva forte (aumenta tempo ~50%)
    FOG = "fog"              # Nevoeiro (aumenta tempo ~20%)
    SNOW = "snow"            # Neve (aumenta tempo ~60%)
    
    def get_time_multiplier(self):
        """Retorna o fator multiplicador de tempo para esta condição."""
        multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 1.3,
            WeatherCondition.HEAVY_RAIN: 1.5,
            WeatherCondition.FOG: 1.2,
            WeatherCondition.SNOW: 1.6,
        }
        return multipliers.get(self, 1.0)


class EventManager:
    """
    Gerencia eventos estáticos da simulação (clima e estradas fechadas).
    Eventos são definidos no início e aplicados ao grafo.
    """
    
    def __init__(self, graph):
        """
        Inicializa o gestor de eventos.
        
        Args:
            graph: Grafo da simulação
        """
        self.graph = graph
        self.weather_zones = {}  # {node_id: WeatherCondition}
        self.closed_roads = []   # [(node_id1, node_id2), ...]
    
    def set_weather_zone(self, node_ids, weather_condition):
        """
        Define condição climática para uma zona (conjunto de nós).
        
        Args:
            node_ids: Lista de IDs de nós afetados
            weather_condition: WeatherCondition a aplicar
        """
        if isinstance(weather_condition, str):
            weather_condition = WeatherCondition(weather_condition)
        
        for node_id in node_ids:
            self.weather_zones[node_id] = weather_condition
        
        print(f"✓ Clima '{weather_condition.value}' aplicado a {len(node_ids)} nós")
    
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
    
    def apply_weather_effects(self):
        """
        Aplica efeitos climáticos às arestas do grafo.
        Aumenta o tempo de viagem em zonas com mau tempo.
        """
        affected_edges = 0
        
        for node_id, edges in self.graph.edges.items():
            # Verifica se este nó tem clima especial
            if node_id in self.weather_zones:
                weather = self.weather_zones[node_id]
                multiplier = weather.get_time_multiplier()
                
                # Aplica multiplicador a todas as arestas que saem deste nó
                for edge in edges:
                    original_time = edge['time']
                    edge['time'] = original_time * multiplier
                    edge['weather'] = weather.value
                    affected_edges += 1
        
        print(f"✓ Efeitos climáticos aplicados a {affected_edges} arestas")
    
    def get_weather_at_node(self, node_id):
        """
        Retorna a condição climática de um nó.
        
        Args:
            node_id: ID do nó
            
        Returns:
            WeatherCondition ou None se clima normal
        """
        return self.weather_zones.get(node_id, WeatherCondition.CLEAR)
    
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
        
        if self.weather_zones:
            print(f"\n📍 Zonas Climáticas: {len(set(self.weather_zones.values()))} tipos")
            weather_counts = {}
            for weather in self.weather_zones.values():
                weather_counts[weather.value] = weather_counts.get(weather.value, 0) + 1
            
            for weather_type, count in weather_counts.items():
                print(f"   • {weather_type}: {count} nós")
        else:
            print("\n☀️  Sem condições climáticas especiais")
        
        if self.closed_roads:
            print(f"\n🚧 Estradas Fechadas: {len(self.closed_roads)}")
            for road in self.closed_roads[:5]:  # Mostra apenas as primeiras 5
                print(f"   • {road[0]} ↔ {road[1]}")
            if len(self.closed_roads) > 5:
                print(f"   ... e mais {len(self.closed_roads) - 5}")
        else:
            print("\n✅ Todas as estradas abertas")
        
        print("="*60 + "\n")


def load_events_from_config(graph, config):
    """
    Carrega eventos de um dicionário de configuração.
    
    Args:
        graph: Grafo da simulação
        config: Dicionário com 'weather_zones' e 'closed_roads'
        
    Returns:
        EventManager configurado
    
    Exemplo de config:
    {
        "weather_zones": [
            {"nodes": [1, 2, 3, 4], "condition": "rain"},
            {"nodes": [10, 11, 12], "condition": "fog"}
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
            event_manager.set_weather_zone(
                zone['nodes'],
                zone['condition']
            )
    
    # Carrega estradas fechadas
    if 'closed_roads' in config:
        for road in config['closed_roads']:
            event_manager.close_road(road['from'], road['to'])
    
    # Aplica efeitos climáticos
    event_manager.apply_weather_effects()
    
    # Mostra resumo
    event_manager.summary()
    
    return event_manager
