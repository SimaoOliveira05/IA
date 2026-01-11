"""
Tipos de veículos (Elétrico, Combustão, Híbrido).
Define as diferentes fontes de energia e consumo dos veículos.
"""
from abc import ABC, abstractmethod

# Constantes importadas do config
try:
    from config import EMISSIONS_COMBUSTION_G_PER_KM, EMISSIONS_HYBRID_G_PER_KM
except ImportError:
    # Fallback se executado de outro diretório
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import EMISSIONS_COMBUSTION_G_PER_KM, EMISSIONS_HYBRID_G_PER_KM

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
    
    @abstractmethod
    def calculate_emissions(self, distance: float) -> float:
        """
        Calcula as emissões de CO₂ para uma dada distância.
        
        Args:
            distance: Distância em metros
            
        Returns:
            float: Emissões de CO₂ em gramas
        """
        pass
    
    @abstractmethod
    def get_emissions_rate(self) -> float:
        """
        Retorna a taxa de emissões do veículo.
        
        Returns:
            float: Emissões em g CO₂/km
        """
        pass


class Eletric(VehicleType):
    """
    Representa um veículo elétrico.
    Inclui atributos para capacidade de bateria, consumo e bateria atual.
    """
    
    def __init__(self, battery_capacity: float, battery_consumption: float, current_battery: float, 
                 average_speed: float = 50.0) -> None:
        self.battery_capacity: float = battery_capacity  # kWh
        self.battery_consumption: float = battery_consumption  # kWh/100km
        self.current_battery: float = current_battery
        self.average_speed: float = average_speed  # km/h

    def consume(self, distance: float) -> None:
        """
        Consome bateria baseado na distância percorrida.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        wasted_battery: float = (self.battery_consumption / 100) * distance_km
        self.current_battery = max(0.0, self.current_battery - wasted_battery)

    def has_enough_battery(self, distance: float) -> bool:
        """Verifica se tem bateria suficiente para a distância."""
        distance_km: float = distance / 1000
        needed_battery: float = (self.battery_consumption / 100) * distance_km
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
    
    def calculate_emissions(self, distance: float) -> float:
        """
        Veículos elétricos não têm emissões diretas.
        
        Args:
            distance: Distância em metros
            
        Returns:
            float: 0.0 (sem emissões)
        """
        return 0.0
    
    def get_emissions_rate(self) -> float:
        """
        Veículos elétricos não têm emissões diretas.
        
        Returns:
            float: 0.0 g CO₂/km
        """
        return 0.0

class Combustion(VehicleType):
    """
    Representa um veículo a combustão.
    Inclui atributos para capacidade de combustível, consumo e combustível atual.
    """
    
    def __init__(self, fuel_capacity: float, fuel_consumption: float, current_fuel: float,
                 average_speed: float = 50.0) -> None:
        self.fuel_capacity: float = fuel_capacity  # Litros
        self.fuel_consumption: float = fuel_consumption  # L/100km
        self.current_fuel: float = current_fuel
        self.average_speed: float = average_speed  # km/h

    def consume(self, distance: float) -> None:
        """
        Consome combustível baseado na distância percorrida.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        wasted_fuel: float = (self.fuel_consumption / 100) * distance_km
        self.current_fuel = max(0.0, self.current_fuel - wasted_fuel)

    def has_enough_fuel(self, distance: float) -> bool:
        """Verifica se tem combustível suficiente para a distância."""
        distance_km: float = distance / 1000
        needed_fuel: float = (self.fuel_consumption / 100) * distance_km
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
    
    def calculate_emissions(self, distance: float) -> float:
        """
        Calcula as emissões de CO₂ para veículos a combustão.
        Média de 120 g CO₂/km para veículos a gasolina.
        
        Args:
            distance: Distância em metros
            
        Returns:
            float: Emissões de CO₂ em gramas
        """
        distance_km = distance / 1000
        emissions_per_km = EMISSIONS_COMBUSTION_G_PER_KM  # g CO₂/km (média para gasolina)
        return emissions_per_km * distance_km
    
    def get_emissions_rate(self) -> float:
        """
        Retorna a taxa de emissões do veículo a combustão.
        
        Returns:
            float: 120.0 g CO₂/km
        """
        return EMISSIONS_COMBUSTION_G_PER_KM

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
        current_fuel: float,
        average_speed: float = 50.0
    ) -> None:
        self.battery_capacity: float = battery_capacity
        self.battery_consumption: float = battery_consumption  # kWh/100km
        self.fuel_capacity: float = fuel_capacity
        self.fuel_consumption: float = fuel_consumption  # L/100km
        self.current_fuel: float = current_fuel
        self.current_battery: float = current_battery
        self.average_speed: float = average_speed  # km/h
    
    def consume(self, distance: float) -> None:
        """
        Consome energia baseado na distância percorrida.
        Prioriza usar bateria primeiro, depois combustível.
        
        Args:
            distance: Distância em metros
        """
        distance_km: float = distance / 1000
        
        # Consumo por km (não por 100km) com fator de escala
        battery_consumption_per_km: float = (self.battery_consumption / 100) 
        fuel_consumption_per_km: float = (self.fuel_consumption / 100)
        
        # Tenta usar bateria primeiro
        needed_battery: float = battery_consumption_per_km * distance_km
        if self.current_battery >= needed_battery:
            # Usa apenas bateria
            self.current_battery = max(0.0, self.current_battery - needed_battery)
        else:
            # Usa bateria restante + combustível
            # Distância que consegue percorrer com bateria restante
            battery_distance_km: float = self.current_battery / battery_consumption_per_km if battery_consumption_per_km > 0 else 0
            remaining_distance_km: float = distance_km - battery_distance_km
            self.current_battery = 0.0
            
            needed_fuel: float = fuel_consumption_per_km * remaining_distance_km
            self.current_fuel = max(0.0, self.current_fuel - needed_fuel)
    
    def has_enough_energy(self, distance: float) -> bool:
        """Verifica se tem energia suficiente (bateria + combustível)."""
        distance_km: float = distance / 1000
        
        # Consumo por km (não por 100km) com fator de escala
        battery_consumption_per_km: float = (self.battery_consumption / 100) if self.battery_consumption > 0 else 0
        fuel_consumption_per_km: float = (self.fuel_consumption / 100) if self.fuel_consumption > 0 else 0
        
        # Calcula distância total que consegue percorrer
        battery_distance_km: float = self.current_battery / battery_consumption_per_km if battery_consumption_per_km > 0 else 0
        fuel_distance_km: float = self.current_fuel / fuel_consumption_per_km if fuel_consumption_per_km > 0 else 0
        total_distance_km: float = battery_distance_km + fuel_distance_km
        
        return total_distance_km >= distance_km
    
    def battery_percentage(self) -> float:
        """Retorna a percentagem de bateria restante."""
        return (self.current_battery / self.battery_capacity) * 100
    
    def fuel_percentage(self) -> float:
        """Retorna a percentagem de combustível restante."""
        return (self.current_fuel / self.fuel_capacity) * 100
    
    def get_energy_info(self) -> str:
        """Retorna informação sobre o estado da energia."""
        return f"Bateria: {self.battery_percentage():.1f}% | Combustível: {self.fuel_percentage():.1f}%"
    
    def calculate_emissions(self, distance: float) -> float:
        """
        Calcula as emissões de CO₂ para veículos híbridos.
        Apenas emite CO₂ quando usa combustível (após bateria acabar).
        
        Args:
            distance: Distância em metros
            
        Returns:
            float: Emissões de CO₂ em gramas
        """
        distance_km = distance / 1000
        
        # Consumo por km (não por 100km)
        battery_consumption_per_km = self.battery_consumption / 100 if self.battery_consumption > 0 else 0
        
        # Calcula quanto pode percorrer com bateria
        battery_distance_km = self.current_battery / battery_consumption_per_km if battery_consumption_per_km > 0 else 0
        
        # Se tem bateria suficiente, não emite
        if battery_distance_km >= distance_km:
            return 0.0
        
        # Se não, emite apenas pela parte em combustível
        fuel_distance_km = distance_km - battery_distance_km
        emissions_per_km = EMISSIONS_HYBRID_G_PER_KM  # g CO₂/km (híbridos são mais eficientes)
        return emissions_per_km * fuel_distance_km
    
    def get_emissions_rate(self) -> float:
        """
        Retorna a taxa média de emissões do veículo híbrido.
        Depende do estado da bateria.
        
        Returns:
            float: Emissões em g CO₂/km (0 se tem bateria, 90 se não)
        """
        # Se tem bateria, pode rodar sem emissões
        if self.current_battery > 0:
            return 0.0
        # Se não tem bateria, usa combustível
        return EMISSIONS_HYBRID_G_PER_KM
