from graph.graph import Graph 
from graph.position import Position  
import osmnx as ox
import math

def create_location_graph(place_name : str, min_distance: float = 100) -> Graph: 
    """
    Cria um grafo da rede viária de uma dada localização, usando coordenadas projetadas (em metros).
    O grafo é convertido para a estrutura definida Graph() com nós e arestas.
    
    Args:
        place_name: Nome da localização a carregar
        min_distance: Distância mínima (em metros) entre nodos. Nodos mais próximos que isto serão ignorados. (padrão: 10.0)
    """

    print(f"A carregar mapa de: {place_name} (distância mínima entre nodos: {min_distance}m)")

    # Obtem o grafo rodoviário a partir do OpenStreetMap
    G_osm = ox.graph_from_place(place_name, network_type="drive")

    # Projeta o grafo para coordenadas métricas, i.e, converte latitude/longitude para x, y em metros
    G_proj = ox.project_graph(G_osm)

    # Adiciona velocidades e tempos de viagem ao grafo JÁ projetado
    G_proj = ox.add_edge_speeds(G_proj)         # acrescenta 'speed_kph' se possível
    G_proj = ox.add_edge_travel_times(G_proj)   # acrescenta 'travel_time' (seconds)

    # Converte para GeoDataFrames (para aceder facilmente aos dados dos nós e arestas)
    nodes, edges = ox.graph_to_gdfs(G_proj)

    graph = Graph()
    osm_to_internal = {} # usado para mapear o id OSM para o node id
    merged_nodes = 0
    
    def find_close_node(x, y, existing_nodes, min_dist):
        """
        Encontra um nodo já existente que esteja próximo de (x, y).
        Retorna o ID do nodo encontrado ou None se não houver nenhum próximo.
        """
        for node in existing_nodes:
            dist = math.sqrt((x - node.position.x)**2 + (y - node.position.y)**2)
            if dist < min_dist:
                return node.id
        return None
    
    # Adiciona os nós (ou mapeia para nodos próximos existentes)
    for osm_id, data in nodes.iterrows():
        x, y = data['x'], data['y']
        
        # Verifica se há algum nodo próximo já criado
        close_node_id = find_close_node(x, y, graph.nodes, min_distance)
        
        if close_node_id is not None:
            # Funde este nodo com o nodo próximo existente
            osm_to_internal[osm_id] = close_node_id
            merged_nodes += 1
        else:
            # Cria um novo nodo
            node = graph.add_node(x, y)
            osm_to_internal[osm_id] = node.id

    # Adiciona as arestas
    for (u, v, key), edge in edges.iterrows():
        if u in osm_to_internal and v in osm_to_internal:
            id_u = osm_to_internal[u]
            id_v = osm_to_internal[v]
            
            # Evita criar arestas de um nodo para ele próprio (self-loops)
            if id_u == id_v:
                continue
                
            length = edge.get("length", None)
            graph.add_edge(
                id_u, id_v,
                distance=length,
                edge_speed=edge.get("speed_kph", 50),
                travel_time=edge.get("travel_time")  # Passa o tempo fornecido pelo OSMnx (em segundos)
            )
    
    print(f"Grafo criado com {len(graph.nodes)} nós e {sum(len(e) for e in graph.edges.values())} arestas.")
    print(f"Nodos fundidos (simplificados): {merged_nodes}")
    return graph