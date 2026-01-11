from graph.position import Position

class Node:
    def __init__(self, id, position: Position, node_type="generic"):
        """
        Representa um ponto da cidade.
        
        Args:
            id: Identificador único do nodo
            position: Posição no mapa (Position com x, y em metros)
            node_type: Tipo do nó ('pickup', 'charging', 'fuel', 'depot', 'generic')
        """
        self.id = id
        self.position = position
        self.node_type = node_type

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id
