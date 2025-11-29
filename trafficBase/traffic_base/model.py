from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import *
import json

import random
import math
from collections import deque

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

        # Inicializar grafo con todos los nodos de camino y destino
        self.graph = self.create_graph()
        
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
        
        # Obtener destino aleatorio
        destination_pos = self.get_random_destination()
        
        # Convertir a coordenadas
        start_coords = spawn_pos
        goal_coords = self.get_coordinates_from_cell(destination_pos)
                
        # Determinar ruta
        path_to_follow = self.find_path(start_coords, goal_coords)
        
        # Crear carro con la ruta
        agent = Car(self, cell=cell_inicial, destination=destination_pos, path=path_to_follow)
        self.cars_spawned += 1
        
        print(f"Carro {self.cars_spawned} spawneado en {spawn_pos} con ruta: {'SÍ' if path_to_follow else 'NO'}")

    ###
    ### Sección de cálculo de rutas --- Algoritmo A *
    ###

    def get_coordinates_from_cell(self, cell):
        """Convert to coordinates"""
        return cell.coordinate

    def create_graph(self):
        """Check the map and create a graph according to its road and destination cells"""
        graph = {}

        # Calcular la ruta con todos los posibles caminos 
        # Después añadir destino
        cells_with_road = [agent for agent in self.agents if isinstance(agent, Road)]
        
        # nodes = cells_with_destination + cells_with_road
        nodes = cells_with_road

        # Crear un diccionario de posición a agente
        self.position_to_agent = {}
        for agent in nodes:
            pos = self.get_coordinates_from_cell(agent.cell)
            self.position_to_agent[pos] = agent

        for agent in nodes:
            pos = self.get_coordinates_from_cell(agent.cell) 
            neighbors = self.get_neighbors(pos)
            graph[pos] = neighbors
            
        return graph

    def get_neighbors(self, pos):
        """Get all valid neighbors for a given position usando solo self.agents"""
        x, y = pos  
        neighbors = []
        
        # Check all adjacent cells
        possible_moves = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
        
        for neighbor_pos in possible_moves:
            # Check if position is within grid bounds
            if (0 <= neighbor_pos[0] < self.width and 
                0 <= neighbor_pos[1] < self.height):
                
                # Usar el diccionario de posición a agente
                if neighbor_pos in self.position_to_agent:
                    neighbor_agent = self.position_to_agent[neighbor_pos]
                    if isinstance(neighbor_agent, (Road, Destination)):
                        neighbors.append(neighbor_pos)
        
        return neighbors

    def heuristic_function(self, pos1, pos2):
        """Calculate the heuristic function using Euclidean distance"""
        x1, y1 = pos1
        x2, y2 = pos2
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def find_path(self, start_pos, goal_pos):
        """Find the optimal path using A* algorithm"""
        
        # Crear una copia del grafo base y agregar el destino específico
        temp_graph = self.graph.copy()
        
        # Si el goal_pos no está en el grafo, agregarlo temporalmente
        if goal_pos not in temp_graph:
            temp_graph[goal_pos] = self.get_neighbors(goal_pos)
            
            # También agregar conexiones desde los vecinos hacia el destino
            for neighbor_pos in temp_graph[goal_pos]:
                if neighbor_pos in temp_graph:
                    if goal_pos not in temp_graph[neighbor_pos]:
                        temp_graph[neighbor_pos] = temp_graph[neighbor_pos] + [goal_pos]

        # Check if start and goal are valid positions
        if start_pos not in temp_graph:
            return None
        
        if goal_pos not in temp_graph:
            return None
                    
        # Initialize open and closed lists
        open_list = []
        closed_list = set()
        
        # Initialize start node
        start_node = {
            'position': start_pos,
            'g': 0,  # Cost from start to this node
            'h': self.heuristic_function(start_pos, goal_pos),
            'f': 0,  # Will be calculated as g + h
            'parent': None
        }
        start_node['f'] = start_node['g'] + start_node['h']
        
        open_list.append(start_node)
        
        iterations = 0
        max_iterations = 1000
        
        while open_list and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f cost
            current_node = min(open_list, key=lambda x: x['f'])
            
            # Check if we reached the goal
            if current_node['position'] == goal_pos:
                path = self.reconstruct_path(current_node)
                return path
            
            # Move current node from open to closed list
            open_list.remove(current_node)
            closed_list.add(current_node['position'])
            
            # Explore neighbors usando el grafo temporal
            current_neighbors = temp_graph.get(current_node['position'], [])
            
            for neighbor_pos in current_neighbors:
                if neighbor_pos in closed_list:
                    continue
                
                # Calculate g score
                tentative_g = current_node['g'] + 1
                
                # Check if neighbor is in open list
                neighbor_in_open = None
                for node in open_list:
                    if node['position'] == neighbor_pos:
                        neighbor_in_open = node
                        break
                
                if neighbor_in_open is None:
                    # New node discovered
                    neighbor_node = {
                        'position': neighbor_pos,
                        'g': tentative_g,
                        'h': self.heuristic_function(neighbor_pos, goal_pos),
                        'f': 0,
                        'parent': current_node
                    }
                    neighbor_node['f'] = neighbor_node['g'] + neighbor_node['h']
                    open_list.append(neighbor_node)
                    
                elif tentative_g < neighbor_in_open['g']:
                    # Found a better path to this neighbor
                    neighbor_in_open['g'] = tentative_g
                    neighbor_in_open['f'] = neighbor_in_open['g'] + neighbor_in_open['h']
                    neighbor_in_open['parent'] = current_node
        
        return None

    def reconstruct_path(self, node):
        """Reconstruct the path from goal to start"""
        path = []
        current = node
        
        while current is not None:
            path.append(current['position'])
            current = current['parent']
        
        # Reverse to get path from start to goal
        path.reverse()
        return path

    def get_random_destination(self):
        """Get a random destination position from the map usando solo self.agents"""
        destinations = [agent for agent in self.agents if isinstance(agent, Destination)]
        
        if destinations:
            destination_agent = self.random.choice(destinations)
            return destination_agent.cell 
        return None
            
    def step(self):
        """Advance the model by one step."""
        self.steps_count += 1
        
        # Spawn de un nuevo carro cada 10 steps
        if self.steps_count % 10 == 0:
            self.spawn_car()
        
        self.agents.shuffle_do("step")