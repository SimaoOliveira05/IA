"""
Algoritmos de procura para pathfinding no grafo.
Cada algoritmo tem a mesma interface: (start_pos, end_pos, graph) -> (cost, time, path)
"""

from collections import deque
import heapq


class SearchAlgorithm:
    """Classe base para algoritmos de procura."""
    
    @staticmethod
    def find_closest_node(graph, position):
        """Encontra o nó mais próximo de uma posição."""
        if not graph.nodes:
            return None
        
        closest_node = None
        min_distance = float('inf')
        
        for node in graph.nodes:
            dist = position.distance_to(node.position)
            if dist < min_distance:
                min_distance = dist
                closest_node = node.id
        
        return closest_node
    
    @staticmethod
    def calculate_path_metrics(graph, path):
        """
        Calcula tempo e distância total de um caminho.
        
        Args:
            graph: Grafo com arestas
            path: Lista de IDs de nós
            
        Returns:
            tuple: (total_distance, total_time)
        """
        total_time = 0
        total_distance = 0
        
        for i in range(len(path) - 1):
            node_from = path[i]
            node_to = path[i + 1]
            edges = graph.edges.get(node_from, [])
            
            for edge in edges:
                if edge["target"] == node_to:
                    total_time += edge["time"]
                    total_distance += edge["distance"]
                    break
        
        return total_distance, total_time


class DFS(SearchAlgorithm):
    """
    Depth-First Search (DFS).
    Rápido mas pode encontrar caminhos muito longos.
    NÃO RECOMENDADO para otimização de rotas.
    """
    
    @staticmethod
    def search(graph, start_node, end_node, max_depth=100):
        """Executa DFS para encontrar caminho."""
        visited = set()
        stack = [(start_node, [start_node])]
        
        while stack:
            current, path = stack.pop()
            
            if current == end_node:
                return path
            
            if current in visited or len(path) > max_depth:
                continue
            
            visited.add(current)
            
            edges = graph.edges.get(current, [])
            for edge in edges:
                # Ignora estradas fechadas
                if not edge.get("open", True):
                    continue
                if edge["target"] not in visited:
                    stack.append((edge["target"], path + [edge["target"]]))
        
        return None
    
    @classmethod
    def find_path(cls, start_position, end_position, graph):
        """
        Interface pública do DFS.
        
        Returns:
            tuple: (distance, time, path)
        """
        start_node = cls.find_closest_node(graph, start_position)
        end_node = cls.find_closest_node(graph, end_position)
        
        if start_node == end_node:
            return 0, 0, [start_node]
        
        path = cls.search(graph, start_node, end_node)
        
        if not path:
            print(f"DFS: Caminho não encontrado de {start_node} a {end_node}")
            return float('inf'), float('inf'), []
        
        distance, time = cls.calculate_path_metrics(graph, path)
        
        print(f"DFS: {start_node}→{end_node} | {len(path)} nós | {time:.2f}min | {distance:.0f}m")
        
        return distance, int(time), path


class BFS(SearchAlgorithm):
    """
    Breadth-First Search (BFS).
    Garante caminho com MENOR NÚMERO DE ARESTAS.
    Bom mas não considera peso das arestas.
    """
    
    @staticmethod
    def search(graph, start_node, end_node):
        """Executa BFS para encontrar caminho."""
        visited = set([start_node])
        queue = deque([(start_node, [start_node])])
        
        while queue:
            current, path = queue.popleft()
            
            if current == end_node:
                return path
            
            edges = graph.edges.get(current, [])
            for edge in edges:
                # Ignora estradas fechadas
                if not edge.get("open", True):
                    continue
                neighbor = edge["target"]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    @classmethod
    def find_path(cls, start_position, end_position, graph):
        """
        Interface pública do BFS.
        
        Returns:
            tuple: (distance, time, path)
        """
        start_node = cls.find_closest_node(graph, start_position)
        end_node = cls.find_closest_node(graph, end_position)
        
        if start_node == end_node:
            return 0, 0, [start_node]
        
        path = cls.search(graph, start_node, end_node)
        
        if not path:
            print(f"BFS: Caminho não encontrado de {start_node} a {end_node}")
            return float('inf'), float('inf'), []
        
        distance, time = cls.calculate_path_metrics(graph, path)
        
        print(f"BFS: {start_node}→{end_node} | {len(path)} nós | {time:.2f}min | {distance:.0f}m")
        
        return distance, int(time), path


class Dijkstra(SearchAlgorithm):
    """
    Algoritmo de Dijkstra.
    Encontra caminho com MENOR TEMPO TOTAL.
    RECOMENDADO para otimização de rotas de táxis.
    """
    
    @classmethod
    def find_path(cls, start_position, end_position, graph):
        """
        Interface pública do Dijkstra.
        
        Returns:
            tuple: (time, time, path) - custo é tempo neste caso
        """
        start_node = cls.find_closest_node(graph, start_position)
        end_node = cls.find_closest_node(graph, end_position)
        
        if start_node == end_node:
            return 0, 0, [start_node]
        
        # Inicialização
        distances = {node.id: float('inf') for node in graph.nodes}
        distances[start_node] = 0
        previous = {node.id: None for node in graph.nodes}
        
        pq = [(0, start_node)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Chegou ao destino
            if current == end_node:
                path = cls._reconstruct_path(previous, end_node)
                distance, _ = cls.calculate_path_metrics(graph, path)
                
                print(f"Dijkstra: {start_node}→{end_node} | {len(path)} nós | {current_dist:.2f}min | {distance:.0f}m ⭐")
                
                return current_dist, int(current_dist), path
            
            # Explora vizinhos
            edges = graph.edges.get(current, [])
            for edge in edges:
                # Ignora estradas fechadas
                if not edge.get("open", True):
                    continue
                    
                neighbor = edge["target"]
                if neighbor in visited:
                    continue
                
                new_dist = current_dist + edge["time"]
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        print(f"Dijkstra: Caminho não encontrado de {start_node} a {end_node}")
        return float('inf'), float('inf'), []
    
    @staticmethod
    def _reconstruct_path(previous, end_node):
        """Reconstrói o caminho a partir do dicionário previous."""
        path = []
        node = end_node
        while node is not None:
            path.append(node)
            node = previous[node]
        path.reverse()
        return path


# Dicionário para fácil acesso
ALGORITHMS = {
    'dfs': DFS.find_path,
    'bfs': BFS.find_path,
    'dijkstra': Dijkstra.find_path,
}
