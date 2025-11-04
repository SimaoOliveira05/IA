from graph.graph import Graph
import osmnx as ox

def create_location_graph():

    G_osm = ox.graph_from_place("Gualtar, Braga, Portugal", network_type="drive")
    nodes, edges = ox.graph_to_gdfs(G_osm)

    graph = Graph()

    for node_id, data in nodes.iterrows():
        graph.add_node(str(node_id), data['y'], data['x'])

    for (u, v, key), edge in edges.iterrows():
        graph.add_edge(str(u), str(v), edge['length'])

    return graph