from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import *
import json
import random


class CityModel(Model):
    """
    Creates a model based on a city map.
    
    Args:
        N: Number of agents in the simulation
        seed: Random seed for the model
    """
    
    def __init__(self, N, seed=42):
        
        super().__init__(seed=seed)
        
        # Load the map dictionary
        dataDictionary = json.load(open("city_files/mapDictionary.json"))
        
        self.num_agents = N
        self.traffic_lights = []
        self.cars_spawned = 0  # Contador de carros creados
        self.steps_count = 0   # Contador de steps
        
        # Load the map file
        with open("city_files/2025_base.txt") as baseFile:
            lines = baseFile.readlines()
            # Limpiar cada línea de saltos de línea y espacios
            lines = [line.strip() for line in lines if line.strip()]
            
            self.width = len(lines[0])
            self.height = len(lines)
            
            self.grid = OrthogonalMooreGrid(
                [self.width, self.height], capacity=100, torus=False
            )
            
            # Goes through each character in the map file and creates the corresponding agent.
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    
                    cell = self.grid[(c, self.height - r - 1)]
                    
                    if col in ["v", "^", ">", "<"]:
                        agent = Road(self, cell, dataDictionary[col])
                        
                    elif col in ["A", "B", "C", "E", "F", "G", "H", "J"]:
                        direction1 = dataDictionary[col][0]
                        direction2 = dataDictionary[col][1]
                        agent = Road(self, cell, direction1, direction2)
                    
                    # Traffic lights with road
                    elif col in ["r", "R", "l", "L", "u", "U", "d", "W"]:
                        direction = dataDictionary[col][0]
                        duration = dataDictionary[col][1]
                        starts_green = col.islower()
                        agent = Traffic_Light(
                            self,
                            cell,
                            starts_green,
                            duration,
                            direction
                        )
                        self.traffic_lights.append(agent)
                    
                    elif col == "#":
                        agent = Obstacle(self, cell)
                    
                    elif col == "D":
                        agent = Destination(self, cell)
        
        # Definir las esquinas de spawn (coordenadas de las 4 esquinas)
        self.spawn_corners = [
            (0, 0),                          # Esquina inferior izquierda
            (self.width - 1, 0),             # Esquina inferior derecha
            (0, self.height - 1),            # Esquina superior izquierda
            (self.width - 1, self.height - 1) # Esquina superior derecha
        ]
        
        # Spawn del primer carro
        self.spawn_car()
        
        self.running = True
    
    def spawn_car(self):
        """Crear un carro en una esquina aleatoria"""
        if self.cars_spawned >= self.num_agents:
            return  # Ya se alcanzó el número máximo de carros
        
        # Elegir una esquina aleatoria
        spawn_pos = self.random.choice(self.spawn_corners)
        cell_inicial = self.grid[spawn_pos]
        
        # Crear el carro
        agent = Car(self, cell=cell_inicial)
        self.cars_spawned += 1
        
        print(f"Carro {self.cars_spawned} spawneado en posición {spawn_pos}")
    
    def step(self):
        """Advance the model by one step."""
        self.steps_count += 1
        
        # Spawn de un nuevo carro cada 10 steps
        if self.steps_count % 10 == 0:
            self.spawn_car()
        
        self.agents.shuffle_do("step")