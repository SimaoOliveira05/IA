from graph.node import Node
from graph.position import Position
import matplotlib.pyplot as plt

class Graph:
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

    def add_edge(self, id1, id2, distance=None, edge_speed=50,traffic_factor=1.0, open=True):
        """
        Adiciona uma aresta entre dois nós.

        Args:
            id1, id2 (int): IDs internos do primeiro nó e do segundo nó
            distance (float): Distância em metros.
            edge_speed (float): Velocidade da estrada em km/h.
            traffic_factor (float): Fator multiplicador do tempo devido ao trânsito.
            open (bool): Se a estrada está aberta. Default=True.
        """
        n1 = self.get_node(id1)
        n2 = self.get_node(id2)
        if not n1 or not n2: # nunca acontece mas quem sabe
            raise ValueError(f"Os nós {id1} e {id2} devem existir antes de criar uma aresta")

        # Calcula a distância se não for fornecida
        if distance is None:
            distance = n1.position.distance_to(n2.position)

        # Calcula o tempo em segundos
        time_hours = (distance * 0.001) / edge_speed
        time_minutes = time_hours * 60 * 60
        time = time_minutes * traffic_factor

        # Cria a aresta direta
        edge_info = {
            "target": id2,
            "distance": distance,
            "time": time,
            "traffic_factor": traffic_factor,
            "open": open
        }
        self.edges[id1].append(edge_info)

        # Cria a aresta reversa (i.e, contexto da estrada com dois sentidos)
        if not self.directed:
            reverse_info = {
                "target": id1,
                "distance": distance,
                "time": time,
                "traffic_factor": traffic_factor,
                "open": open
            }
        self.edges[id2].append(reverse_info)

    def plot(self, show_labels=True, show_distances=True, show_times=True):
        """
        Desenha o grafo com cores e estilos de acordo com o tipo de nó e o estado das arestas.
        """
        node_colors = {
            "pickup": "green",
            "charging": "orange",
            "fuel": "red",
            "depot": "blue",
            "generic": "gray"
        }

        edge_colors = {
            "open": "black",         # normal
            "closed": "red",         # bloqueada
            "traffic": "orange"      # congestionada
        }

        # Aumenta drasticamente o tamanho da figura para dar mais espaço
        plt.figure(figsize=(20, 18))
        
        # Para evitar desenhar distâncias duplicadas em grafos não direcionados
        drawn_edges = set()

        # Desenhar as arestas
        for node_id, edges in self.edges.items():
            n1 = self.get_node(node_id)
            if not n1:
                continue

            for edge in edges:
                n2 = self.get_node(edge["target"])
                if not n2:
                    continue

                # Evita duplicados em grafos não direcionados
                edge_pair = tuple(sorted((node_id, edge["target"])))
                
                # Escolher cor e estilo com base no estado
                if not edge.get("open", True):
                    color = edge_colors["closed"]
                    style = "--"
                elif edge.get("traffic_factor", 1.0) > 1.3:
                    color = edge_colors["traffic"]
                    style = "-"
                else:
                    color = edge_colors["open"]
                    style = "-"

                plt.plot(
                    [n1.position.x, n2.position.x],
                    [n1.position.y, n2.position.y],
                    linestyle=style,
                    color=color,
                    linewidth=0.5 * edge.get("traffic_factor", 1.0),
                    alpha=0.7,
                    zorder=1 # Coloca as arestas atrás dos nós
                )

                # Adicionar texto da distância
                if show_distances and edge_pair not in drawn_edges:
                    mid_x = (n1.position.x + n2.position.x) / 2
                    mid_y = (n1.position.y + n2.position.y) / 2
                    distance = edge.get("distance", 0)
                    plt.text(
                        mid_x,
                        mid_y,
                        f"{distance:.0f}m", # Arredonda para unidades
                        fontsize=5, # Fonte mais pequena para a distância
                        color="purple",
                        ha='center',
                        va='center',
                        bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.1')
                    )
                    drawn_edges.add(edge_pair)

                if show_times:
                    mid_x = (n1.position.x + n2.position.x) / 2
                    mid_y = (n1.position.y + n2.position.y) / 2 + 2  # Ajusta a posição para não sobrepor a distância
                    time = edge.get("time", 0)
                    plt.text(
                        mid_x,
                        mid_y,
                        f"{time:.1f}seg", # Arredonda para uma casa decimal
                        fontsize=5, # Fonte mais pequena para o tempo
                        color="blue",
                        ha='center',
                        va='center',
                        bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.1')
                    )
                    drawn_edges.add(edge_pair)


        # Desenhar os nós
        all_x = [node.position.x for node in self.nodes]
        all_y = [node.position.y for node in self.nodes]

        for node in self.nodes:
            color = node_colors.get(node.node_type, "black")
            # Reduz o tamanho base dos nós
            size = 30 + (node.capacity * 4 if hasattr(node, "capacity") else 0)

            plt.scatter(node.position.x, node.position.y, color=color, s=size, zorder=3, edgecolors='black', linewidth=0.5)
            ##if show_labels:
            #    plt.text(
            #        node.position.x,
            #        node.position.y + 0.6, # Ajusta a posição do texto
            #        str(node.id),
            #        fontsize=6, # Fonte mais pequena para o ID
            #        color="black",
            #        ha='center',
            #        zorder=4
            #    )
        # Ajustar o zoom (limites do gráfico) para a área dos nós
        if all_x and all_y:
            margin = 10  # Adiciona uma margem maior para garantir que nada é cortado
            plt.xlim(min(all_x) - margin, max(all_x) + margin)
            plt.ylim(min(all_y) - margin, max(all_y) + margin)


        plt.title("City Graph Representation (with dynamic edges)")
        plt.axis("equal")
        plt.axis("off")
        plt.show()