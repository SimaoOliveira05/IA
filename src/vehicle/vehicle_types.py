"""
Tipos de veículos (Elétrico, Combustão, Híbrido).
Define as diferentes fontes de energia e consumo dos veículos.
"""
from abc import ABC, abstractmethod


class VehicleType(ABC):
    """Classe base abstrata para tipos de veículos."""
    
    @abstractmethod
    def consume(self, distance: float) -> None:
        """Consome energia/combustível baseado na distância percorrida."""
        pass
    
    @abstractmethod
    def has_enough_energy(self, distance: float) -> bool:
        """Verifica se tem energia suficiente para a distância."""
        pass
    
    @abstractmethod
    def get_energy_info(self) -> str:
        """Retorna informação sobre o estado da energia."""
        pass


class Eletric(VehicleType):
    """
    Representa um veículo elétrico.
    Inclui atributos para capacidade de bateria, consumo e bateria atual.
    """
    
    def __init__(self, battery_capacity: float, battery_consumption: float, current_battery: float) -> None:
        self.battery_capacity: float = battery_capacity  # kWh
        self.battery_consumption: float = battery_consumption  # kWh/km
        self.current_battery: float = current_battery

    def consume(self, distance: float) -> None:
        """
        Consome bateria baseado na distância percorrida.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        wasted_battery: float = self.battery_consumption * distance_km
        self.current_battery = max(0.0, self.current_battery - wasted_battery)

    def has_enough_battery(self, distance: float) -> bool:
        """Verifica se tem bateria suficiente para a distância."""
        distance_km: float = distance / 1000
        needed_battery: float = self.battery_consumption * distance_km
        return self.current_battery >= needed_battery
    
    def has_enough_energy(self, distance: float) -> bool:
        """Verifica se tem energia suficiente para a distância."""
        return self.has_enough_battery(distance)
    
    def battery_percentage(self) -> float:
        """Retorna a percentagem de bateria restante."""
        return (self.current_battery / self.battery_capacity) * 100
    
    def get_energy_info(self) -> str:
        """Retorna informação sobre o estado da energia."""
        return f"Bateria: {self.battery_percentage():.1f}%"


class Combustion(VehicleType):
    """
    Representa um veículo a combustão.
    Inclui atributos para capacidade de combustível, consumo e combustível atual.
    """
    
    def __init__(self, fuel_capacity: float, fuel_consumption: float, current_fuel: float) -> None:
        self.fuel_capacity: float = fuel_capacity  # Litros
        self.fuel_consumption: float = fuel_consumption  # L/km
        self.current_fuel: float = current_fuel

    def consume(self, distance: float) -> None:
        """
        Consome combustível baseado na distância percorrida.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        wasted_fuel: float = self.fuel_consumption * distance_km
        self.current_fuel = max(0.0, self.current_fuel - wasted_fuel)

    def has_enough_fuel(self, distance: float) -> bool:
        """Verifica se tem combustível suficiente para a distância."""
        distance_km: float = distance / 1000
        needed_fuel: float = self.fuel_consumption * distance_km
        return self.current_fuel >= needed_fuel
    
    def has_enough_energy(self, distance: float) -> bool:
        """Verifica se tem energia suficiente para a distância."""
        return self.has_enough_fuel(distance)
    
    def fuel_percentage(self) -> float:
        """Retorna a percentagem de combustível restante."""
        return (self.current_fuel / self.fuel_capacity) * 100
    
    def get_energy_info(self) -> str:
        """Retorna informação sobre o estado da energia."""
        return f"Combustível: {self.fuel_percentage():.1f}%"


class Hybrid(VehicleType):
    """
    Representa um veículo híbrido.
    Inclui atributos de um veículo elétrico e de combustão.
    Prioriza o uso de bateria antes do combustível.
    """
    
    def __init__(
        self, 
        battery_capacity: float, 
        battery_consumption: float, 
        fuel_capacity: float,
        fuel_consumption: float, 
        current_battery: float, 
        current_fuel: float
    ) -> None:
        self.battery_capacity: float = battery_capacity
        self.battery_consumption: float = battery_consumption  # kWh/km
        self.fuel_capacity: float = fuel_capacity
        self.fuel_consumption: float = fuel_consumption  # L/km
        self.current_fuel: float = current_fuel
        self.current_battery: float = current_battery
    
    def consume(self, distance: float) -> None:
        """
        Consome energia baseado na distância percorrida.
        Prioriza usar bateria primeiro, depois combustível.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        
        # Tenta usar bateria primeiro
        needed_battery: float = self.battery_consumption * distance_km
        if self.current_battery >= needed_battery:
            # Usa apenas bateria
            self.current_battery = max(0.0, self.current_battery - needed_battery)
        else:
            # Usa bateria restante + combustível
            remaining_distance_km: float = (needed_battery - self.current_battery) / self.battery_consumption
            self.current_battery = 0.0
            
            needed_fuel: float = self.fuel_consumption * remaining_distance_km
            self.current_fuel = max(0.0, self.current_fuel - needed_fuel)
    
    def has_enough_energy(self, distance: float) -> bool:
        """Verifica se tem energia suficiente (bateria + combustível)."""
        distance_km: float = distance / 1000
        
        # Calcula energia total disponível equivalente
        battery_distance: float = self.current_battery / self.battery_consumption
        fuel_distance: float = self.current_fuel / self.fuel_consumption
        total_distance: float = battery_distance + fuel_distance
        
        return total_distance >= distance_km
    
    def battery_percentage(self) -> float:
        """Retorna a percentagem de bateria restante."""
        return (self.current_battery / self.battery_capacity) * 100
    
    def fuel_percentage(self) -> float:
        """Retorna a percentagem de combustível restante."""
        return (self.current_fuel / self.fuel_capacity) * 100
    
    def get_energy_info(self) -> str:
        """Retorna informação sobre o estado da energia."""
        return f"Bateria: {self.battery_percentage():.1f}% | Combustível: {self.fuel_percentage():.1f}%"
