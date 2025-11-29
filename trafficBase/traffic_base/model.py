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
        
        # DEBUG: Verificar el grafo
        print(f"DEBUG: Grafo creado con {len(self.graph)} nodos")
        if len(self.graph) > 0:
            sample_key = list(self.graph.keys())[0]
            print(f"DEBUG: Ejemplo - nodo {sample_key} tiene vecinos: {self.graph[sample_key]}")
        
        # Spawn del primer carro
        self.spawn_car()
        
        self.running = True
    
    def spawn_car(self):
        """Crear un carro en una esquina aleatoria"""
        if self.cars_spawned >= self.num_agents:
            return
        
        spawn_pos = self.random.choice(self.spawn_corners)
        cell_inicial = self.grid[spawn_pos]
        
        # Obtener destino aleatorio
        destination_pos = self.get_random_destination()
        
        if destination_pos is None:
            print("DEBUG: No se encontró destino válido")
            return
        
        # Convertir a coordenadas
        start_coords = spawn_pos
        goal_coords = self.get_coordinates_from_cell(destination_pos)
        
        print(f"DEBUG: Buscando ruta de {start_coords} a {goal_coords}")
        
        # Encontrar ruta
        path_to_follow = self.find_path(start_coords, goal_coords)
        
        # Crear carro CON la ruta
        agent = Car(self, cell=cell_inicial, path=path_to_follow)
        self.cars_spawned += 1
        
        print(f"Carro {self.cars_spawned} spawneado en {spawn_pos} con ruta: {'SÍ' if path_to_follow else 'NO'}")

    ###
    ### Sección de cálculo de rutas --- Algoritmo A *
    ###

    def get_coordinates_from_cell(self, cell):
        """Convert GridCell object to (x, y) coordinates"""
        # Dependiendo de cómo esté implementado GridCell en Mesa
        # Puede ser cell.pos, cell.coordinate, o simplemente la tupla
        if hasattr(cell, 'pos'):
            return cell.pos
        elif hasattr(cell, 'coordinate'):
            return cell.coordinate
        else:
            # Si es directamente una tupla
            return cell

    def create_graph(self):
        """Check the map and create a graph according to its road and destination cells"""
        graph = {}

        # Usar solo self.agents como en tu approach original
        #cells_with_destination = [agent for agent in self.agents if isinstance(agent, Destination)]
        cells_with_road = [agent for agent in self.agents if isinstance(agent, Road)]
        
        #nodes = cells_with_destination + cells_with_road
        nodes = cells_with_road


        # Crear un diccionario de posición a agente para búsqueda rápida
        self.position_to_agent = {}
        for agent in nodes:
            # Convertir GridCell a coordenadas
            pos = self.get_coordinates_from_cell(agent.cell)
            self.position_to_agent[pos] = agent

        for agent in nodes:
            pos = self.get_coordinates_from_cell(agent.cell)  # Convertir a coordenadas (x, y)
            neighbors = self.get_neighbors(pos)
            graph[pos] = neighbors
            
            # DEBUG para los primeros nodos
            if len(graph) <= 5:
                print(f"DEBUG: Nodo {pos} -> {len(neighbors)} vecinos: {neighbors}")

        return graph

    def get_neighbors(self, pos):
        """Get all valid neighbors for a given position usando solo self.agents"""
        # CORRECCIÓN: pos ya son coordenadas (x, y) gracias a get_coordinates_from_cell
        x, y = pos  # Desempaquetar las coordenadas directamente
        neighbors = []
        
        # Check all adjacent cells (up, down, left, right)
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

        print(f"DEBUG: find_path llamado con start={start_pos}, goal={goal_pos}")
        print(f"DEBUG: start_pos en grafo: {start_pos in self.graph}")
        print(f"DEBUG: goal_pos en grafo: {goal_pos in self.graph}")
        
        # Check if start and goal are valid positions
        if start_pos not in self.graph:
            print(f"DEBUG: start_pos {start_pos} no está en el grafo")
            return None
        
        if goal_pos not in self.graph:
            print(f"DEBUG: goal_pos {goal_pos} no está en el grafo")
            return None
        
        print("DEBUG: Ambas posiciones están en el grafo. Iniciando A*...")
        
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

        print(f"DEBUG: Nodo inicial: {start_node}")
        
        open_list.append(start_node)
        
        iterations = 0
        max_iterations = 1000
        
        while open_list and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f cost
            current_node = min(open_list, key=lambda x: x['f'])
            
            # Check if we reached the goal
            if current_node['position'] == goal_pos:
                print(f"DEBUG: Meta alcanzada después de {iterations} iteraciones")
                path = self.reconstruct_path(current_node)
                print(f"DEBUG: Camino encontrado: {len(path)} pasos")
                return path
            
            # Move current node from open to closed list
            open_list.remove(current_node)
            closed_list.add(current_node['position'])
            
            # Explore neighbors
            current_neighbors = self.graph.get(current_node['position'], [])
            
            for neighbor_pos in current_neighbors:
                if neighbor_pos in closed_list:
                    continue
                
                # Calculate tentative g score
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
        
        print(f"DEBUG: No se encontró camino después de {iterations} iteraciones")
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
            return destination_agent.cell  # Esto devuelve un GridCell
        return None
            
    def step(self):
        """Advance the model by one step."""
        self.steps_count += 1
        
        # Spawn de un nuevo carro cada 10 steps
        if self.steps_count % 10 == 0:
            self.spawn_car()
        
        self.agents.shuffle_do("step")