# Classe nodo para definiçao dos nodos

class Node:
    def __init__(self, name, lat=None, lon=None):     #  construtor do nodo....."
        self.m_id = id
        self.m_name = str(name)
        self.lat = lat
        self.lon = lon

    def setId(self, id):
        self.m_id = id

    def getId(self):
        return self.m_id

    def __eq__(self, other):
        return self.m_name == other.m_name  

    def __repr__(self):
        return f"Node({self.m_name}, lat={self.lat}, lon={self.lon})"