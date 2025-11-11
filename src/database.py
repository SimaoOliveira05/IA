import json

from location import create_location_graph
from vehicle import Vehicle, Eletric, Combustion, Hybrid, Vehicle_Status

class Database:
    '''
    Represents the current database of a simulation
    '''
    def __init__(self, vehicles, graph):
        self.vehicles = vehicles
        self.graph = graph
    
    '''
    Lists all vehicles in the database 
    '''
    def list_vehicles(self):
        print("\n--- Lista de Veículos ---\n")
        for v in self.vehicles:
            print(f"[{v.id}] {v.name} ({v.vehicle_type.__class__.__name__}) - Condutor: {v.driver}")
        print(f"\nTotal: {len(self.vehicles)} veículos\n")

def load_dataset(dataset_path):
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
                battery_capacity=vehicle["battery_capacity"],
                current_battery=vehicle["current_battery"],
                battery_consumption=vehicle["battery_consumption"]
            )

        elif vehicle["type"] == "combustion":
            vehicle_type = Combustion(
                fuel_capacity=vehicle["fuel_capacity"],
                current_fuel=vehicle["current_fuel"],
                fuel_consumption=vehicle["fuel_consumption"]
            )

        elif vehicle["type"] == "hybrid":
            vehicle_type = Hybrid(
                battery_capacity=vehicle["battery_capacity"],
                current_battery=vehicle["current_battery"],
                battery_consumption=vehicle["battery_consumption"],
                fuel_capacity=vehicle["fuel_capacity"],
                current_fuel=vehicle["current_fuel"],
                fuel_consumption=vehicle["fuel_consumption"]
            )
        else:
            raise ValueError(f"Unknown vehicle type: {vehicle['type']}")

        # Creates the vehicle
        vehicle = Vehicle(
            id=vehicle["id"],
            name=vehicle["name"],
            vehicle_type=vehicle_type,
            capacity=vehicle["capacity"],
            driver=vehicle["driver"],
            status=Vehicle_Status[vehicle["status"]]
        )

        vehicles.append(vehicle)

    return Database(vehicles, graph)