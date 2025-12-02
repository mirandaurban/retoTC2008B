from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import *
import json
import random
import math

class CityModel(Model):
    """
    Creates a model based on a city map with directional roads.
    """
    
    def __init__(self, N, seed=42):
        super().__init__(seed=seed)
        
        # Load the map dictionary
        dataDictionary = json.load(open("city_files/mapDictionary.json"))
        
        self.num_agents = N
        self.traffic_lights = []
        self.cars_spawned = 0
        self.steps_count = 0
        
        # Load the map file
        with open("city_files/2025_base.txt") as baseFile:
            lines = baseFile.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            
            self.width = len(lines[0])
            self.height = len(lines)
            
            self.grid = OrthogonalMooreGrid(
                [self.width, self.height], capacity=100, torus=False, random=self.random
            )
            
            # Store map characters for graph creation
            self.map_grid = {}
            
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    y_coord = self.height - r - 1
                    self.map_grid[(c, y_coord)] = col
                    
                    cell = self.grid[(c, y_coord)]
                    
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
                        #print(f"semáforo en {cell}")
                        self.traffic_lights.append(agent)
                    
                    elif col == "#":
                        agent = Obstacle(self, cell)
                    
                    elif col == "D":
                        agent = Destination(self, cell)
        
        # Definir las esquinas de spawn
        self.spawn_corners = [
            (0, 0),                           # Esquina inferior izquierda
            (self.width - 1, 0),              # Esquina inferior derecha
            (0, self.height - 1),             # Esquina superior izquierda
            (self.width - 1, self.height - 1) # Esquina superior derecha
        ]

        # Inicializar grafo 
        self.graph = self.create_directional_graph()
        
        self.running = True

    def get_directions_from_symbol(self, symbol):
        """Get allowed movement directions from a map symbol"""
        directions_map = {
            ">": ["Right"],
            "<": ["Left"], 
            "v": ["Down"],
            "^": ["Up"],
            "A": ["Up", "Right"],
            "B": ["Up", "Left"],
            "C": ["Down", "Right"],
            "E": ["Down", "Left"],
            "F": ["Right", "Up"],
            "G": ["Right", "Down"],
            "H": ["Left", "Up"],
            "J": ["Left", "Down"],
            "r": ["Right"],
            "R": ["Right"],
            "l": ["Left"],
            "L": ["Left"],
            "u": ["Up"],
            "U": ["Up"],
            "d": ["Down"],
            "W": ["Down"],
            "D": ["Up", "Down", "Left", "Right"],  # Destinations allow all directions
        }
        return directions_map.get(symbol, [])

    def get_move_from_direction(self, direction, current_pos):
        """Convert direction to coordinate movement"""
        x, y = current_pos
        moves = {
            "Up": (x, y + 1),
            "Down": (x, y - 1),
            "Left": (x - 1, y),
            "Right": (x + 1, y)
        }
        return moves.get(direction)

    def get_valid_directions(self, current_pos, symbol):
        """Get directions that are possible from current position """
        allowed_directions = self.get_directions_from_symbol(symbol)
        valid_directions = []
        
        x, y = current_pos
        
        for direction in allowed_directions:
            next_pos = self.get_move_from_direction(direction, current_pos)
            next_x, next_y = next_pos
            
            # Check if movement is within bounds
            if (0 <= next_x < self.width and 0 <= next_y < self.height):
                # Check if target cell is not an obstacle
                next_symbol = self.map_grid.get(next_pos, "#")
                if next_symbol != "#":
                    valid_directions.append(direction)
        
        return valid_directions

    def create_directional_graph(self):
        """Create a directed graph that respects road directions"""
        graph = {}
        
        print("Creando grafo direccional")
        
        # Para cada posición en el mapa, determinar conexiones salientes
        for current_pos, symbol in self.map_grid.items():
            if symbol == "#":  # Saltar obstáculos
                continue
                
            graph[current_pos] = []
            
            # Obtener direcciones válidas
            valid_directions = self.get_valid_directions(current_pos, symbol)
            
            # Para cada dirección válida, crear la conexión SIN validación bidireccional
            for direction in valid_directions:
                next_pos = self.get_move_from_direction(direction, current_pos)
                next_symbol = self.map_grid.get(next_pos, "#")
                
                # Si podemos movernos ahí y no es obstáculo -> crar la conexión
                if next_symbol != "#":
                    cost = self.calculate_cost(symbol, next_symbol)
                    graph[current_pos].append((next_pos, cost))
        
        # Verificar y agregar conexiones para destinos
        self.add_destination_connections(graph)
        
        return graph

    def add_destination_connections(self, graph):
        """Ensure destinations can be reached from adjacent roads"""
        for pos, symbol in self.map_grid.items():
            if symbol == "D":
                # Para cada destino, verificar celdas adyacentes que puedan llegar a él
                x, y = pos
                adjacent_positions = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
                
                for adj_pos in adjacent_positions:
                    if adj_pos in graph:  # Si la celda adyacente está en el grafo
                        # Verificar si la celda adyacente puede moverse hacia el destino
                        if self.can_move_to(adj_pos, pos):
                            # Agregar conexión desde la celda adyacente al destino
                            if pos not in [conn[0] for conn in graph[adj_pos]]:
                                graph[adj_pos].append((pos, 1))

    def can_move_to(self, from_pos, to_pos):
        """Check if the actual cell can reach the nex cell based on road directions"""
        from_symbol = self.map_grid.get(from_pos, "#")
        if from_symbol == "#":
            return False
            
        # Determinar la dirección del movimiento
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        direction = None
        if to_x == from_x + 1 and to_y == from_y:
            direction = "Right"
        elif to_x == from_x - 1 and to_y == from_y:
            direction = "Left"
        elif to_x == from_x and to_y == from_y + 1:
            direction = "Up"
        elif to_x == from_x and to_y == from_y - 1:
            direction = "Down"
        else:
            return False
            
        # Verificar si from_pos permite moverse en esa dirección
        return direction in self.get_directions_from_symbol(from_symbol)

    def calculate_cost(self, from_symbol, to_symbol):
        """Calculate movement cost between cells"""
        base_cost = 1
        
        # Costos más altos para semáforos
        traffic_light_cost = {
            "r": 3, "l": 3, "u": 3, "d": 3,  # Semáforos cortos
            "R": 5, "L": 5, "U": 5, "W": 5   # Semáforos largos
        }
        
        cost = base_cost
        if from_symbol in traffic_light_cost:
            cost += traffic_light_cost[from_symbol]
        if to_symbol in traffic_light_cost:
            cost += traffic_light_cost[to_symbol]
            
        return cost

    def print_graph_info(self):
        """Print information about the graph"""
        print(f"Tamaño del grafo: {len(self.graph)} nodos")
        
        # Verificar conectividad general
        total_connections = sum(len(connections) for connections in self.graph.values())
        nodes_with_connections = sum(1 for connections in self.graph.values() if connections)
        
        print(f"\nEstadísticas del grafo:")
        print(f"  Conexiones totales: {total_connections}")
        print(f"  Nodos con conexiones: {nodes_with_connections}/{len(self.graph)}")
        print(f"  Promedio de conexiones por nodo: {total_connections/len(self.graph):.2f}")

    def spawn_car(self):
        """Crear un carro en una esquina aleatoria"""
        if self.cars_spawned >= self.num_agents:
            return 
        
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            valid_spawns = []
            for corner in self.spawn_corners:
                if corner in self.graph and self.graph[corner]:
                    if not any(isinstance(agent, Car) for agent in self.grid[corner].agents):
                        valid_spawns.append(corner)
            
            if not valid_spawns:
                road_cells = [pos for pos, sym in self.map_grid.items() 
                            if sym not in ["#", "D"] and pos in self.graph and self.graph[pos]]
                road_cells = [pos for pos in road_cells 
                            if not any(isinstance(agent, Car) for agent in self.grid[pos].agents)]
                if road_cells:
                    emergency_spawn = self.random.choice(road_cells)
                    valid_spawns = [emergency_spawn]
                else:
                    continue
            
            spawn_pos = self.random.choice(valid_spawns)
            destination_pos = self.get_random_destination()
            if not destination_pos:
                continue
                
            path_to_follow = self.find_path(spawn_pos, destination_pos)
            
            if path_to_follow:
                cell_inicial = self.grid[spawn_pos]
                destination_cell = self.grid[destination_pos]
                
                agent = Car(self, cell=cell_inicial, destination=destination_cell, path=path_to_follow)
                self.cars_spawned += 1
                # print(f"✓ Carro {self.cars_spawned} en {spawn_pos} -> {destination_pos} ({len(path_to_follow)} pasos)")
                return
        
        print(f"No se pudo spawnear carro")

    def heuristic_function(self, pos1, pos2):
        """Euclidean distance heuristic for grid"""
        x1, y1 = pos1
        x2, y2 = pos2
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def find_path(self, start_pos, goal_pos):
        """Find optimal path using A* with directional graph"""
        if start_pos not in self.graph:
            # print(f"ERROR: Start position {start_pos} not in graph")
            return None
            
        if goal_pos not in self.graph:
            # print(f"ERROR: Goal position {goal_pos} not in graph")
            return None
            
        # Initialize open and closed lists
        open_list = []
        closed_list = set()
        
        # Initialize start node
        start_node = {
            'position': start_pos,
            'g': 0,
            'h': self.heuristic_function(start_pos, goal_pos),
            'f': 0,
            'parent': None
        }
        start_node['f'] = start_node['g'] + start_node['h']
        
        open_list.append(start_node)
        
        iterations = 0
        max_iterations = 10000
        
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
            
            # Explore neighbors using directional graph
            for neighbor_pos, cost in self.graph.get(current_node['position'], []):
                if neighbor_pos in closed_list:
                    continue
                
                # Calculate g score (considering directional costs)
                tentative_g = current_node['g'] + cost
                
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
        
        # print(f"  Nodos explorados: {len(closed_list)}")
        return None

    def reconstruct_path(self, node):
        """Reconstruct the path from goal to start"""
        path = []
        current = node
        
        while current is not None:
            path.append(current['position'])
            current = current['parent']
        
        path.reverse()
        return path

    def get_random_destination(self):
        """Get a random destination position that's in the graph"""
        destinations = []
        for pos, symbol in self.map_grid.items():
            if symbol == "D" and pos in self.graph:
                # Verificar que el destino sea alcanzable (tenga conexiones entrantes)
                has_incoming = any(pos in [conn[0] for conn in connections] 
                                 for connections in self.graph.values())
                if has_incoming:
                    destinations.append(pos)
        
        return self.random.choice(destinations) if destinations else None
            
    def step(self):
        """Advance the model by one step."""
        self.steps_count += 1
        
        active_cars = sum(1 for agent in self.agents if isinstance(agent, Car) and agent.state != "In destination")
      
        if self.steps_count % 10 == 0 and self.cars_spawned < self.num_agents:
            self.spawn_car()
        
        self.agents.shuffle_do("step")