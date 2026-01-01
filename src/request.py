from graph.position import Position

class Request:
    '''
        Represents a request of a client of an Uber
        Args:
            id: unique identifier for the request
            start_point: position where the client will be picked up in the graph
            end_point: position where the client will be dropped in the graph
            requested_time: when the uber was requested
            multiple_people: if the client allows the uber to gather other people for the same trip
            passengers: number of passengers for the request
            eco_friendly: if the client prefers eco-friendly vehicles (electric only)
        
        Status possíveis:
            - 'pending': Request criado mas ainda não atribuído a nenhum veículo
            - 'assigned': Request atribuído a um veículo, veículo a caminho do pickup
            - 'picked_up': Cliente apanhado, veículo a caminho do destino
            - 'completed': Viagem concluída
    '''
    def __init__(self, start_point: Position, end_point: Position, requested_time, multiple_people: bool, passengers: int, eco_friendly: bool = False, id: int = None):
        self.id = id
        self.start_point = start_point
        self.end_point = end_point
        self.requested_time = requested_time
        self.multiple_people = multiple_people
        self.passengers = passengers
        self.eco_friendly = eco_friendly  # Preferência por veículos ecológicos (apenas elétricos)
        self.status = 'pending'  # 'pending', 'assigned', 'picked_up', 'completed'
        self.assigned_vehicle = None  # referência ao veículo atribuído
