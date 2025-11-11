from enum import Enum

class Vehicle_Status(Enum):
    ''' Represents the current status of the vehicle '''
    IDLE = 0
    TRAVELING = 1
    REFUELING = 2
    RECHARGING = 3

class Eletric:
    ''' 
        Represents an eletric vehicle 
        Includes attributes for battery capacity, battery consumption and its current battery
    '''
    def __init__(self, battery_capacity, battery_consumption, current_battery):
        
        self.battery_capacity = battery_capacity
        self.battery_consumption = battery_consumption
        self.current_battery = current_battery

class Combustion:
    ''' 
        Represents a combustion vehicle 
        Includes attributes for fuel capacity, fuel consumption and its current fuel
    '''
    def __init__(self, fuel_capacity, fuel_consumption, current_fuel):
        
        self.fuel_capacity = fuel_capacity
        self.fuel_consumption = fuel_consumption
        self.current_fuel = current_fuel

class Hybrid:
    ''' 
        Represents a hybrid vehicle 
        Includes attributes from an eletric vehicle and a combustion vehicle
    '''
    def __init__(self, battery_capacity, battery_consumption, fuel_capacity, fuel_consumption, current_battery, current_fuel):
        
        self.battery_capacity = battery_capacity
        self.battery_consumption = battery_consumption
        self.fuel_capacity = fuel_capacity
        self.fuel_consumption = fuel_consumption

        self.current_fuel = current_fuel
        self.current_battery = current_battery

class Vehicle:
    '''
    Represents an individual vehicle
    '''
    def __init__(self, id, name, vehicle_type, capacity, driver, status):
    
        self.id = id
        self.name = name
        self.vehicle_type = vehicle_type
        self.capacity = capacity
        self.driver = driver          
        self.status = status

        self.start_point = None              # por definir a posição por defeito dos veículos
        self.end_point = None                # vai receber o seu end_point depois de um pedido de um cliente
        self.passengers = 0