import json

from graph.position import Position
from location import create_location_graph
from vehicle.vehicle import Vehicle, Eletric, Combustion, Hybrid, Vehicle_Status
from request import Request
from events import load_events_from_config

class Database:
    '''
    Represents the current database of a simulation
    '''
    def __init__(self, vehicles, graph, event_manager=None):
        self.vehicles = vehicles
        self.graph = graph
        self.event_manager = event_manager
        #self.requests = requests
    

def get_position_from_node_id(graph, node_id: int) -> Position:
    node = graph.get_node(node_id)
    if node is None:
        raise ValueError(f"Node id {node_id} not found in graph")
    return node.position

def load_dataset(dataset_path) -> Database:
    """
    Loads and processes the dataset to initialize the database of the simulation.
    
    :param dataset_path: Path to the JSON dataset file
    :return: An instance of the Database class representing the simulation
    """

    with open(dataset_path, 'r') as file:
        dataset = json.load(file)

    location = dataset['location']
    graph = create_location_graph(location)

    vehicles = []

    for vehicle in dataset["vehicles"]:
        # Creates the vehicle type according to its type
        if vehicle["type"] == "eletric":
            vehicle_type = Eletric(
                battery_capacity = vehicle["battery_capacity"],
                current_battery = vehicle["current_battery"],
                battery_consumption = vehicle["battery_consumption"]
            )

        elif vehicle["type"] == "combustion":
            vehicle_type = Combustion(
                fuel_capacity = vehicle["fuel_capacity"],
                current_fuel = vehicle["current_fuel"],
                fuel_consumption = vehicle["fuel_consumption"]
            )

        elif vehicle["type"] == "hybrid":
            vehicle_type = Hybrid(
                battery_capacity = vehicle["battery_capacity"],
                current_battery = vehicle["current_battery"],
                battery_consumption = vehicle["battery_consumption"],
                fuel_capacity = vehicle["fuel_capacity"],
                current_fuel = vehicle["current_fuel"],
                fuel_consumption = vehicle["fuel_consumption"]
            )
        else:
            raise ValueError(f"Unknown vehicle type: {vehicle['type']}")

        # start_point agora é o id do nó
        start_point_pos = get_position_from_node_id(graph, vehicle["start_point"])
        vehicle = Vehicle(
            id = vehicle["id"],
            name = vehicle["name"],
            vehicle_type = vehicle_type,
            capacity = vehicle["capacity"],
            driver = vehicle["driver"],
            status = Vehicle_Status[vehicle["status"]],
            start_point = start_point_pos,
        )

        vehicles.append(vehicle)

    requests = []
    for req in dataset.get("requests", []):
        start_pos = get_position_from_node_id(graph, req["start_point"])
        end_pos = get_position_from_node_id(graph, req["end_point"])
        requests.append(Request(
            start_point=start_pos,
            end_point=end_pos,
            requested_time=req["requested_time"],
            multiple_people=req["multiple_people"],
            passengers=req["passengers"],
            id=req.get("id", None)
        ))

    db = Database(vehicles, graph)
    db.requests = requests  # Adiciona requests ao objeto Database
    
    # Marca nós como fuel stations (bombas de gasolina)
    fuel_stations = dataset.get("fuel_stations", [])
    for station in fuel_stations:
        node_id = station["node_id"]
        node = graph.get_node(node_id)
        if node:
            node.node_type = "fuel"
            print(f"✓ Nó {node_id} marcado como bomba de gasolina")
    
    # Marca nós como charging stations (postos de carregamento)
    charging_stations = dataset.get("charging_stations", [])
    for station in charging_stations:
        node_id = station["node_id"]
        node = graph.get_node(node_id)
        if node:
            node.node_type = "charging"
            print(f"✓ Nó {node_id} marcado como posto de carregamento")
    
    # Carrega eventos (clima e estradas fechadas) se existirem no dataset
    events_config = dataset.get("events", {})
    if events_config:
        db.event_manager = load_events_from_config(graph, events_config)
    
    return db