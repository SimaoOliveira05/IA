from graph.node import Node
import math
import matplotlib.pyplot as plt

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class Graph:
    def __init__(self, directed=False):
        self.m_nodes = []  
        self.m_directed = directed
        self.m_graph = {}  

    def add_node(self, name, lat, lon):
        n = Node(name, lat, lon)
        if n not in self.m_nodes:
            n.setId(len(self.m_nodes))
            self.m_nodes.append(n)
            self.m_graph[name] = []
        return n

    def get_node_by_name(self, name):
        for node in self.m_nodes:
            if node.m_name == name:
                return node
        return None

    def add_edge(self, node1_name, node2_name, weight=None):
        n1 = self.get_node_by_name(node1_name)
        n2 = self.get_node_by_name(node2_name)
        if not n1 or not n2:
            raise ValueError("Both nodes must exist before adding an edge")

        # If weight is not given, compute geographic distance automatically
        if weight is None:
            weight = haversine_distance(n1.lat, n1.lon, n2.lat, n2.lon)

        self.m_graph[node1_name].append((node2_name, weight))
        if not self.m_directed:
            self.m_graph[node2_name].append((node1_name, weight))

    def plot(self):
        for node in self.m_nodes:
            plt.scatter(node.lon, node.lat, color='blue', s=5)
        for key, edges in self.m_graph.items():
            n1 = self.get_node_by_name(key)
            for edge in edges:
                n2 = self.get_node_by_name(edge[0])
                plt.plot([n1.lon, n2.lon], [n1.lat, n2.lat], 'k-', linewidth=0.5)
        plt.title("Map Graph")
        plt.axis('off') 
        plt.show()