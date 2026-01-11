from graph.node import Node
from graph.position import Position
import matplotlib.pyplot as plt

class Graph:
    def calculate_path_metrics(self, path):
        """
        Calcula a distância e tempo total de um caminho (lista de IDs de nós).
        Args:
            path (List[int]): Lista de IDs de nós representando o caminho
        Returns:
            Tuple[float, float]: (distância total em metros, tempo total em minutos)
        """
        total_distance = 0.0
        total_time = 0.0
        if not path or len(path) < 2:
            return total_distance, total_time
        for i in range(len(path) - 1):
            node_id = path[i]
            next_id = path[i + 1]
            # Procura a aresta entre node_id e next_id
            edge = next((e for e in self.edges[node_id] if e["target"] == next_id), None)
            if edge:
                total_distance += edge["distance"]
                total_time += edge.get("time", 0.0)
        return total_distance, total_time
    
    def find_closest_node(self, position):
        """Retorna o nó mais próximo da posição dada."""
        min_dist = float('inf')
        closest = None
        for node in self.nodes:
            dist = node.position.distance_to(position)
            if dist < min_dist:
                min_dist = dist
                closest = node
        return closest
    
    def __init__(self, directed=False):
        self.nodes = []
        self.edges = {}
        self.directed = directed
        self.next_id = 0

    def add_node(self, x, y, node_type="generic", capacity=0):
        position = Position(x, y)
        node = Node(self.next_id, position, node_type=node_type, capacity=capacity)
        node.set_id(self.next_id)

        self.nodes.append(node)
        self.edges[self.next_id] = []

        self.next_id += 1
        return node
    
    def get_node(self, node_id):
        """Retorna o nó correspondente ao ID interno (int)."""
        if isinstance(node_id, int) and 0 <= node_id < len(self.nodes):
            return self.nodes[node_id]
        return None

    def add_edge(self, id1, id2, distance=None, edge_speed=50, travel_time=None, open=True):
        """
        Adiciona uma aresta entre dois nós.

        Args:
            id1, id2 (int): IDs internos do primeiro nó e do segundo nó
            distance (float): Distância em metros.
            edge_speed (float): Velocidade da estrada em km/h (usado se travel_time não for fornecido).
            travel_time (float): Tempo de viagem em segundos (se fornecido, usa este em vez de calcular).
            open (bool): Se a estrada está aberta. Default=True.
        """
        n1 = self.get_node(id1)
        n2 = self.get_node(id2)
        if not n1 or not n2: # nunca acontece mas quem sabe
            raise ValueError(f"Os nós {id1} e {id2} devem existir antes de criar uma aresta")

        # Calcula a distância se não for fornecida
        if distance is None:
            distance = n1.position.distance_to(n2.position)

        # Usa o travel_time fornecido (já em segundos) ou calcula
        if travel_time is not None:
            # Usa o tempo fornecido pelo OSMnx (em segundos)
            time_seconds = travel_time
        else:
            # Calcula o tempo baseado na velocidade
            time_hours = (distance * 0.001) / edge_speed
            time_seconds = time_hours * 3600
        
        # TRANSFORMAÇÃO DE ESCALA: multiplica por 10 para simular área maior
        # 200m reais → 2000m (2km) na simulação
        # 20s reais → 200s na simulação (convertido para minutos: 200/60 ≈ 3.3 min)
        SCALE_FACTOR = 15
        scaled_distance = distance * SCALE_FACTOR
        scaled_time_minutes = (time_seconds * SCALE_FACTOR) / 60.0  # segundos → minutos

        # Cria a aresta direta
        edge_info = {
            "target": id2,
            "distance": scaled_distance,
            "time": scaled_time_minutes,  # Tempo em minutos de simulação
            "open": open
        }
        self.edges[id1].append(edge_info)

        # Cria a aresta reversa (i.e, contexto da estrada com dois sentidos)
        if not self.directed:
            reverse_info = {
                "target": id1,
                "distance": scaled_distance,
                "time": scaled_time_minutes,
                "open": open
            }
            self.edges[id2].append(reverse_info)

    def get_edge_time(self, node1_id, node2_id):
        """
        Obtém o tempo atual de uma aresta (já com eventos aplicados).
        
        Args:
            node1_id: ID do primeiro nó
            node2_id: ID do segundo nó
            
        Returns:
            float: Tempo em minutos, ou None se aresta não existe
        """
        if node1_id in self.edges:
            for edge in self.edges[node1_id]:
                if edge["target"] == node2_id:
                    return edge.get("time", 0)
        return None

    
    def draw(self, ax, show_labels=True, requests=None):
        """
        Desenha o grafo num eixo fornecido (ax), sem criar nova figura.
        Usado para animação/live plot.
        
        Args:
            ax: Eixo matplotlib onde desenhar
            show_labels: Mostrar IDs dos nós
            requests: Lista de requests (opcional)
            
        Returns:
            dict: Dicionário com referências às labels das arestas para atualização
        """
        node_colors = {
            "pickup": "green",
            "charging": "orange",
            "fuel": "red",
            "depot": "blue",
            "generic": "gray"
        }

        edge_colors = {
            "open": "black",
            "closed": "red",
        }

        drawn_edges = set()
        edge_labels = {}  # Guarda referências às labels para atualização

        # Desenhar arestas
        for node_id, edges in self.edges.items():
            n1 = self.get_node(node_id)
            if not n1:
                continue
            for edge in edges:
                n2 = self.get_node(edge["target"])
                if not n2:
                    continue
                edge_pair = tuple(sorted((node_id, edge["target"])))
                
                if not edge.get("open", True):
                    color = edge_colors["closed"]
                    style = "--"

                else:
                    color = edge_colors["open"]
                    style = "-"

                ax.plot([n1.position.x, n2.position.x], [n1.position.y, n2.position.y], 
                       linestyle=style, color=color, linewidth=0.5, 
                       alpha=0.7, zorder=1)

                # Mostrar distância e tempo na mesma label (duas linhas)
                if edge_pair not in drawn_edges:
                    mid_x = (n1.position.x + n2.position.x) / 2
                    mid_y = (n1.position.y + n2.position.y) / 2
                    
                    distance = edge.get("distance", 0)
                    time = edge.get("time", 0)
                    label_text = f"{distance:.0f}m\n{time:.1f}min"
                    
                    text_obj = ax.text(mid_x, mid_y, label_text, fontsize=5, color="darkblue", 
                           ha='center', va='center', 
                           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))
                    
                    # Guarda referência à label para atualização posterior
                    edge_labels[edge_pair] = {
                        'text_obj': text_obj,
                        'distance': distance
                    }
                    drawn_edges.add(edge_pair)

        # Desenhar nós
        for node in self.nodes:
            color = node_colors.get(node.node_type, "black")
            size = 30 + (node.capacity * 4 if hasattr(node, "capacity") else 0)
            
            # Desenha o nó com forma especial dependendo do tipo
            if node.node_type == "fuel":
                # Bomba de gasolina - quadrado vermelho
                ax.scatter(node.position.x, node.position.y, color='red', s=size*1.5, 
                          marker='s', zorder=3, edgecolors='darkred', linewidth=2)
                # Adiciona texto "GAS"
                ax.text(node.position.x, node.position.y - 4, 'GAS', 
                       fontsize=6, color='darkred', ha='center', va='top',
                       fontweight='bold', zorder=5,
                       bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', 
                                boxstyle='round,pad=0.2', linewidth=1))
            elif node.node_type == "charging":
                # Posto de carregamento - triângulo laranja
                ax.scatter(node.position.x, node.position.y, color='orange', s=size*1.5, 
                          marker='^', zorder=3, edgecolors='darkorange', linewidth=2)
                # Adiciona texto "CHG"
                ax.text(node.position.x, node.position.y - 4, 'CHG', 
                       fontsize=6, color='darkorange', ha='center', va='top',
                       fontweight='bold', zorder=5,
                       bbox=dict(facecolor='white', alpha=0.9, edgecolor='orange', 
                                boxstyle='round,pad=0.2', linewidth=1))
            else:
                # Nó genérico
                ax.scatter(node.position.x, node.position.y, color=color, s=size, zorder=3, 
                          edgecolors='black', linewidth=0.5)
            
            # Colocar ID dos nós - destacado e legível
            if show_labels:
                # Para fuel e charging stations, coloca o ID acima do label
                if node.node_type in ["fuel", "charging"]:
                    y_offset = 6  # Posiciona acima do GAS/CHG
                else:
                    y_offset = 0
                    
                ax.text(
                    node.position.x, 
                    node.position.y + y_offset, 
                    str(node.id), 
                    fontsize=4,  # Diminuído para ficar mais discreto
                    color="black", 
                    ha='center', 
                    va='center',  # Centralizado no nodo
                    zorder=5,  # Por cima do nodo
                    fontweight='bold',  # Negrito para destaque
                    bbox=dict(
                        facecolor='white', 
                        alpha=0.85,  # Fundo branco semi-transparente
                        edgecolor='black',  # Borda preta
                        linewidth=0.8,  # Borda fina
                        boxstyle='round,pad=0.3'  # Cantos arredondados
                    )
                )

        # Ajustar limites
        all_x = [node.position.x for node in self.nodes]
        all_y = [node.position.y for node in self.nodes]
        if all_x and all_y:
            margin = 10
            ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
            ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        
        
        # Desenhar requests, se fornecidos
        if requests:
            for req in requests:
                status = getattr(req, 'status', 'pending')
                
                # Se pending, desenhar pickup point (azul)
                if status == 'pending':
                    start_pos = req.start_point
                    if start_pos:
                        ax.scatter(start_pos.x, start_pos.y, color='blue', s=150, 
                                 marker='*', zorder=7, edgecolors='white', linewidth=1.5, label='Pickup')
                        ax.text(start_pos.x, start_pos.y + 3, f"P{getattr(req, 'id', '?')}", 
                               fontsize=8, ha='center', zorder=8, color='blue', fontweight='bold')
                
                # Se picked_up, desenhar dropoff point (laranja)
                elif status == 'picked_up':
                    end_pos = req.end_point
                    if end_pos:
                        ax.scatter(end_pos.x, end_pos.y, color='orange', s=150, 
                                 marker='*', zorder=7, edgecolors='white', linewidth=1.5, label='Dropoff')
                        ax.text(end_pos.x, end_pos.y + 3, f"D{getattr(req, 'id', '?')}", 
                               fontsize=8, ha='center', zorder=8, color='orange', fontweight='bold')

        ax.set_aspect('equal')
        ax.axis('off')
        
        return edge_labels