from graph.graph import Graph 
from graph.position import Position  
import osmnx as ox

def create_location_graph(place_name): 
    """
    Cria um grafo da rede viária de uma dada localização, usando coordenadas projetadas (em metros).
    O grafo é convertido para a estrutura definida Graph() com nós e arestas.
    """

    print(f"A carregar mapa de: {place_name}")

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
    
    # Adiciona os nós
    for osm_id, data in nodes.iterrows():
        node = graph.add_node(data['x'], data['y'])
        osm_to_internal[osm_id] = node.id

    # Adiciona as arestas
    for (u, v, key), edge in edges.iterrows():
        if u in osm_to_internal and v in osm_to_internal:
            id_u = osm_to_internal[u]
            id_v = osm_to_internal[v]
            length = edge.get("length", None)
            graph.add_edge(id_u, id_v, distance=length, edge_speed=edge.get("speed_kph", 50))
    
    print(f"Grafo criado com {len(graph.nodes)} nós e {sum(len(e) for e in graph.edges.values())} arestas.")
    return graph