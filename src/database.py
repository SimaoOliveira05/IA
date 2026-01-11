import json

from graph.position import Position
from location import create_location_graph
from vehicle import Vehicle, Eletric, Combustion, Hybrid, Vehicle_Status
from request import Request
from events import load_events_from_config

class Database:
    '''
    Represents the current database of a simulation
    '''
    def __init__(self, vehicles, graph, fuel_stations=None, charging_stations=None, event_manager=None):
        self.vehicles = vehicles
        self.graph = graph
        self.fuel_stations = fuel_stations if fuel_stations is not None else []
        self.charging_stations = charging_stations if charging_stations is not None else []
        self.event_manager = event_manager

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
                battery_consumption = vehicle["battery_consumption"],
                average_speed = vehicle.get("average_speed", 50.0)
            )

        elif vehicle["type"] == "combustion":
            vehicle_type = Combustion(
                fuel_capacity = vehicle["fuel_capacity"],
                current_fuel = vehicle["current_fuel"],
                fuel_consumption = vehicle["fuel_consumption"],
                average_speed = vehicle.get("average_speed", 50.0)
            )

        elif vehicle["type"] == "hybrid":
            vehicle_type = Hybrid(
                battery_capacity = vehicle["battery_capacity"],
                current_battery = vehicle["current_battery"],
                battery_consumption = vehicle["battery_consumption"],
                fuel_capacity = vehicle["fuel_capacity"],
                current_fuel = vehicle["current_fuel"],
                fuel_consumption = vehicle["fuel_consumption"],
                average_speed = vehicle.get("average_speed", 50.0)
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
            multiple_people="false",
            passengers=req["passengers"],
            eco_friendly=req.get("eco_friendly", False),  # Preferência ambiental (padrão: False)
            id=req.get("id", None)
        ))
    
    

    # Marcar nós das estações no grafo
    fuel_stations = dataset.get("fuel_stations", [])
    charging_stations = dataset.get("charging_stations", [])
    for fs in fuel_stations:
        node = graph.get_node(fs["node_id"])
        if node:
            node.node_type = "fuel"
    for cs in charging_stations:
        node = graph.get_node(cs["node_id"])
        if node:
            node.node_type = "charging"

    db = Database(vehicles, graph, fuel_stations=fuel_stations, charging_stations=charging_stations)
    db.requests = requests  # Adiciona requests ao objeto Database

    # Carrega eventos (clima e estradas fechadas) se existirem no dataset
    events_config = dataset.get("events", {})
    if events_config:
        db.event_manager = load_events_from_config(graph, events_config)

    return db