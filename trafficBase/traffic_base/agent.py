from mesa.discrete_space import CellAgent, FixedAgent
from math import sqrt
import random
from math import sqrt

class Car(CellAgent):
    """
    State:
        - "In destination" (highest priority)
        - "Waiting traffic light"
             - Communicating with cooldown 
        - "Waiting other car"
            - Communicating with cooldown - Cantidad de interacción entre coches - cada n tiempo no pasar por ahí
        - "Following_route" 
        - "Recalculating route"
        - "Exploring" -> Following route (default state, lower priority)
    """
    def __init__(self, model, cell, destination, path):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
            path: La ruta calculada por A* como lista de coordenadas (x, y)
        """
        super().__init__(model)
        self.cell = cell
        self.initial_direction = "Left" # Posición inicial default (cambiar después)
        self.current_direction = "Left" 
        self.state = "Following_route"
        self.destination = destination
        self.path = path  # Guardar la ruta
        self.path_index = 0  # Índice actual en la ruta

    def assign_random_destination(self):
        """
        Assign a random destination from all available destinations in the model
        """
        # Obtener todas las celdas del grid
        all_cells = self.model.grid.all_cells
        
        # Filtrar celdas que contienen objetos Destination
        destination_cells = [
            cell for cell in all_cells 
            if any(isinstance(agent, Destination) for agent in cell.agents)
        ]
        
        if destination_cells:
            # Seleccionar un destino aleatorio
            chosen_destination = random.choice(destination_cells)
            
            # Obtener el agente Destination de esa celda
            for agent in chosen_destination.agents:
                if isinstance(agent, Destination):
                    return chosen_destination
        
        return None

    def follow_path(self):
        """
        Follow the route obtained by using the algorithm A*
        """
        if not self.path:
            print("No hay ruta")
            self.state = "Exploring"
            return False
        if self.path_index >= len(self.path) - 1:
            print("Ruta completada")
            return False
        
        # Obtener la siguiente posición en la ruta
        next_coords = self.path[self.path_index + 1]
        next_cell = self.model.grid[next_coords]
        
        # Verificar si el movimiento a la siguiente celda es básico
        if self.can_move_to_cell(next_cell):
            old_position = self.cell.coordinate
            self.cell = next_cell
            self.path_index += 1
            self.update_direction(next_cell)
                        
            # Verificar si llegó al destino
            if self.check_if_reached_destination():
                self.state = "In destination"
                return True
            return True
        else:
            self.state = "Recalculating route"
            return False

    def can_move_to_cell(self, next_cell):
        """
        Check if the cell can move to an specific locatiom
        """
        # Verificar obstáculos
        if any(isinstance(agent, Obstacle) for agent in next_cell.agents):
            return False
        
        # Verificar otros carros
        if any(isinstance(agent, Car) for agent in next_cell.agents):
            return False
        
        # Verificar semáforo
        if not self.evaluate_traffic_light(next_cell):
            return False
        
        # Verificar que sea carretera o destino
        if not any(isinstance(agent, (Road, Destination, Traffic_Light)) for agent in next_cell.agents):
            return False
        
        return True

    def recalculate_route(self):
        """
        Recalculating the route using A*
        """
        if self.destination is None:
            print("No hay destino, no se puede recalcular ruta")
            self.state = "Exploring"
            return
        
        current_coords = self.cell.coordinate
        destination_coords = self.destination.coordinate
                
        new_path = self.model.find_path(current_coords, destination_coords)
        
        if new_path:
            self.path = new_path
            self.path_index = 0
            self.state = "Following_route"
        else:
            self.state = "Exploring"

    def step(self):
        """ 
        Uses a state machine to control the movements of the car
        """
        if self.state == "In destination":
            self.remove()
            return
        
        if self.state == "Following_route":
            success = self.follow_path()
            if not success:
                self.state = "Recalculating route"
        
        elif self.state == "Recalculating route":
            self.recalculate_route()
        
        elif self.state == "Exploring":
            self.move()
            
            # Recalcular ruta mientras explora
            if self.model.steps_count % 5 == 0 and self.destination:
                current_coords = self.cell.coordinate
                destination_coords = self.destination.coordinate
                new_path = self.model.find_path(current_coords, destination_coords)
                if new_path:
                    self.path = new_path
                    self.path_index = 0
                    self.state = "Following_route"

    def check_if_reached_destination(self):
        """
        Verifica si el carro ha llegado a su destino
        """
        if self.destination is None:
            return False
        
        # CORRECCIÓN: Comparar coordenadas en lugar de objetos completos
        if isinstance(self.destination, tuple):
            # Si destination es una tupla (x, y)
            return self.cell.coordinate == self.destination
        else:
            # Si destination es un objeto Cell
            return self.cell.coordinate == self.destination.coordinate

    def evaluate_traffic_light(self, next_cell):
        """
        Evaluates whether there is a traffic light in the next cell or in adjacent cells.
        When Traffic_Light state:
        - True: Green traffic light, proceed
        - False: Red traffic light, stop
        """
        # Check if there's a traffic light in the next cell
        for agent in next_cell.agents:
            ##print(agent)
            if isinstance(agent, Traffic_Light):
                # If there's a traffic light, check its state
                # state = True means green (can pass)
                # state = False means red (cannot pass)
                ##print(agent.state)
                return agent.state
        
        # If there's no traffic light, the car can proceed
        return True

    def is_cells_a_destination(self):
        """
        Return an array with the position of each near cell with destinations 
        (radius: 2)
        """
        cells_with_destination = self.cell.get_neighborhood(2, False).select(
            lambda cell: any(isinstance(obj, Destination) for obj in cell.agents)
        )
        return cells_with_destination

    def is_cells_with_traffic_light(self):
        """
       Return an array with the position of each near cell with traffic lights 
       (radius: 2)
        """
        cells_with_traffic_light = self.cell.get_neighborhood(2, False).select(
            lambda cell: any(isinstance(obj, Traffic_Light) for obj in cell.agents)
        )
        return cells_with_traffic_light

    def is_cells_without_obstacles(self):
        """
        Return an array with the position of each near cell without obstacles 
        (radius: 2)
        """
        cells_without_obstacles = self.cell.get_neighborhood(2, False).select(
            lambda cell: not any(isinstance(obj, Obstacle) for obj in cell.agents)
        )
        return cells_without_obstacles

    def is_cells_a_road(self):
        """
        Return an array with the position of each near cell with road 
        (radius: 1)
        """
        cells_with_road = self.cell.neighborhood.select(
            lambda cell: any(isinstance(obj, (Road, Traffic_Light)) for obj in cell.agents)
        )
        return cells_with_road

    def get_road_direction(self, cell):
        """
        Obtains the direction expected by the road
        """
        for agent in cell.agents:
            if isinstance(agent, Road):
                # Si tiene segunda dirección (intersección), retornar tupla
                if agent.direction2:
                    return (agent.direction, agent.direction2)
                else:
                    return agent.direction
            elif isinstance(agent, Traffic_Light):
                return agent.direction
        return None
    
    def validate_road_direction(self, current_cell, next_cell):
        """ Validate if the agent movement is correct according to the road direction """
        
        # Obtain coordinates of the current and next cell
        x1, y1 = current_cell.coordinate
        x2, y2 = next_cell.coordinate

        # Obtain the direction of my cell
        my_direction = self.get_road_direction(self.cell)
        ##print(f"mi dir: {my_direction}")

        # Obtain the direction of the destiny cell
        rd = self.get_road_direction(next_cell)

        if isinstance(my_direction, tuple) and len(my_direction) > 1:
            # Si rd también es tupla → intersección
            if isinstance(rd, tuple):
                road_direction = rd[1]  # segunda dirección del destino
            else:
                road_direction = rd     # rd es string → usar completo
        else:
            road_direction = rd

        if not road_direction:
            return False

        ##print(f"Road direction: {road_direction}")

        if isinstance(my_direction, tuple) and len(my_direction) > 1:
            # Hay más de una dirección en mi dirección ->  usa la segunda
            direction_to_check = my_direction[1]
            ##print(f"Dirección a checar {direction_to_check}")
            
            if direction_to_check == "Up":
                return x1 == x2 and y1 == y2 - 1
            elif direction_to_check == "Down":
                return x1 == x2 and y1 == y2 + 1
            elif direction_to_check == "Right":
                return y1 == y2 and x1 == x2 - 1
            elif direction_to_check == "Left":
                return y1 == y2 and x1 == x2 + 1
            
        elif (isinstance(my_direction, tuple) and len(my_direction) > 1) and (isinstance(rd, tuple)):
            # Hay más de una dirección en mi dirección y en la dirección a donde voy ->  usa la segunda
            road_direction = rd[0]
            direction_to_check = my_direction[1]

            if (direction_to_check == "Up") and (road_direction == "Up"):
                return x1 == x2 and y1 == y2 - 1
            elif direction_to_check == "Down" and (road_direction == "Down"):
                return x1 == x2 and y1 == y2 + 1
            elif direction_to_check == "Right" and (road_direction == "Right"):
                return y1 == y2 and x1 == x2 - 1
            elif direction_to_check == "Left" and (road_direction == "Left"):
                return y1 == y2 and x1 == x2 + 1

        else:
            # Hay más de una dirección a donde voy
            if my_direction == "Up":
                return x1 == x2 and y1 == y2 - 1
            elif my_direction == "Down":
                return x1 == x2 and y1 == y2 + 1
            elif my_direction == "Right":
                return y1 == y2 and x1 == x2 - 1
            elif my_direction == "Left":
                return y1 == y2 and x1 == x2 + 1

        return False

    def move(self):
        """
        Move the car according to the road directions
        """
        # Check if the current cell has road
        current_road_direction = self.get_road_direction(self.cell)        
        
        # Obtain all the neighbor cells (radio 1)
        neighbor_cells = self.cell.neighborhood
        
        # Filter cells to find just the valid ones
        possible_cells = []

        road_cells = self.is_cells_a_road()
        non_obstacles_cells = self.is_cells_without_obstacles()
        destination = [self.destination]
      
        for cell in neighbor_cells:
            #print(f"\n  Evaluando celda {cell.coordinate}:")

            # Check if it is road
            if cell not in road_cells:
                #print(f"No es carretera")
                continue
            ##print(f"Es carretera")
                
            # Check if has obstacles            
            if cell not in non_obstacles_cells:
                ##print(f"Tiene obstáculo")
                continue
            ##print(f"Sin obstáculos")
                
            # Check if it has other cars
            has_cars = any(isinstance(agent, Car) for agent in cell.agents)
            
            if has_cars:
                ##print(f"Tiene otro carro")
                continue
            ##print(f"Sin carros")

            can_pass_traffic_light = self.evaluate_traffic_light(cell)
            #Check traffic light state before adding to possible cells
        
            if not can_pass_traffic_light:
                ##print(f"Semáforo en rojo")
                continue
            ##print(f"Semáforo permite pasar")

            if cell in destination:
                #print("No es mi destino")
                continue
            #print("Es mi destino")

            # Check if the movement is valid according to the direction of the road

            cd = self.get_road_direction(cell)
            if isinstance(cd, tuple):
                cell_direction = cd[1]
            else:
                cell_direction = cd
            #print(f"Dirección de la celda destino: {cell_direction}")
            
            # Check if the movement is valid according to the direction of the road
            is_valid_move = self.validate_road_direction(self.cell, cell)
            #print(f"    {'si' if is_valid_move else 'x'} Movimiento {'válido' if is_valid_move else 'inválido'}")
        
            if is_valid_move:
                possible_cells.append(cell)

        #print(f"Celdas posibles finales: {[cell.coordinate for cell in possible_cells]}")

        # Move to the first cell, if possible
        if possible_cells:
            new_cell = possible_cells[0]
            #print(f" Moviendo a {new_cell.coordinate}")
            self.update_direction(new_cell)
            old_position = self.cell.coordinate
            self.cell = new_cell

            if self.check_if_reached_destination():
                # Detener la simulación
                self.model.running = False
                #print(f"Simulación detenida - Carro llegó a su destino")
        #else:
            #print(f"No hay celdas posibles: El carro está atascado en {self.cell.coordinate}")

    def update_direction(self, next_cell):
        """
        Update direction according to the movement
        """
        x1, y1 = self.cell.coordinate
        x2, y2 = next_cell.coordinate
        
        direction_map = {
            (0, -1): "Up",    # y disminuye
            (0, 1): "Down",   # y aumenta  
            (1, 0): "Right",  # x aumenta
            (-1, 0): "Left"   # x disminuye
        }
        
        dx = x2 - x1
        dy = y2 - y1
        
        self.current_direction = direction_map.get((dx, dy), self.current_direction)


class Traffic_Light(FixedAgent):
    """
    Traffic light. Where the traffic lights are in the grid.
    """
    def __init__(self, model, cell, state = False, timeToChange = 10, direction=None):
        """
        Creates a new Traffic light.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
            state: Whether the traffic light is green or red
            timeToChange: After how many step should the traffic light change color 
            direction: Direction allowed for traffic ("Right", "Left", "Up", "Down")
        """
        super().__init__(model)
        self.cell = cell
        self.state = state
        self.timeToChange = timeToChange
        self.direction = direction

    def step(self):
        """ 
        To change the state (green or red) of the traffic light in case you consider the time to change of each traffic light.
        """
        if self.model.steps % self.timeToChange == 0:
            self.state = not self.state

class Destination(FixedAgent):
    """
    Destination agent. Where each car should go.
    """
    def __init__(self, model, cell):
        """
        Creates a new destination agent
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell

class Obstacle(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        """
        Creates a new obstacle.
        
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell

class Road(FixedAgent):
    """
    Road agent. Determines where the cars can move, and in which direction.
    """
    def __init__(self, model, cell, direction= "Left", direction2 = None):
        """
        Creates a new road.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
            direction: The direction of that cell road (Right, Left, Up, Down)
        """
        super().__init__(model)
        self.cell = cell
        self.direction = direction
        self.direction2 = direction2
