from mesa.discrete_space import CellAgent, FixedAgent
import random

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
    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell
        self.initial_direction = "Left" # Posición inicial default (cambiar después)
        self.current_direction = "Left" 
        self.state = "Exploring"
        self.destination = self.assign_random_destination()
        print(f"Carro creado en {self.cell.coordinate} con destino en {self.destination.coordinate if self.destination else 'N/A'}")
    
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
            import random
            chosen_destination = random.choice(destination_cells)
            
            # Obtener el agente Destination de esa celda
            for agent in chosen_destination.agents:
                if isinstance(agent, Destination):
                    
                    return chosen_destination
        
        return None

    def check_if_reached_destination(self):
        """
        Verifica si el carro ha llegado a su destino
        """
        if self.destination is None:
            return False
        
        # Verificar si la celda actual es el destino
        if self.cell.coordinate == self.destination.coordinate:
            print(f"Destino alcanzado, carro llegó a {self.cell.coordinate}")
            self.state = "In_destination"
            return True
        
        return False

    def evaluate_traffic_light(self, next_cell):
        """
        Evaluates whether there is a traffic light in the next cell or in adjacent cells.
        When Traffic_Light state:
        - True: Green traffic light, proceed
        - False: Red traffic light, stop
        """
        # Check if there's a traffic light in the next cell
        for agent in next_cell.agents:
            #print(agent)
            if isinstance(agent, Traffic_Light):
                # If there's a traffic light, check its state
                # state = True means green (can pass)
                # state = False means red (cannot pass)
                if agent.state == True:
                    self.state = "Exploring"
                else: 
                    self.state = "Waiting_traffic_light"
                #print(agent.state)
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
        #print(f"mi dir: {my_direction}")

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

        #print(f"Road direction: {road_direction}")

        if isinstance(my_direction, tuple) and len(my_direction) > 1:
            # Hay más de una dirección en mi dirección ->  usa la segunda
            direction_to_check = my_direction[1]
            #print(f"Dirección a checar {direction_to_check}")
            
            if direction_to_check == "Up":
                return x1 == x2 and y1 == y2 - 1
            elif direction_to_check == "Down":
                return x1 == x2 and y1 == y2 + 1
            elif direction_to_check == "Right":
                return y1 == y2 and x1 == x2 - 1
            elif direction_to_check == "Left":
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
        # Devuelve direccion (Up, down, rigth, left) o para de direcciones (de donde viene, a donde va) si es intersección
        current_road_direction = self.get_road_direction(self.cell) 
        # Devuelve todos mis vecinos en radio 1 (array)
        neighbor_cells = self.cell.neighborhood
        # Devuelve todas las celdas vecinas que son calles (array)
        road_cells = self.is_cells_a_road() 
        # Devuelve todas las celdas vecinas que no son osbstaculos
        non_obstacles_cells = self.is_cells_without_obstacles() 
        # Coordenada de mi celda destino
        destination = self.destination.coordinate 

        # Si mi destino está en radio de 1 (neighbor_cells) -> avanzo a destino
        for neighbor in neighbor_cells:
            if neighbor.coordinate == destination:
                # Verificar que no haya obstáculos
                if neighbor in non_obstacles_cells:
                    self.cell = neighbor
                    self.check_if_reached_destination()
                    return
        
        # Si no tengo mi destino cerca, continúo por las calles
        # Filtrar celdas válidas: deben ser calles Y no tener obstáculos
        valid_cells = [cell for cell in road_cells if cell in non_obstacles_cells]
        
        if not valid_cells:
            # No hay celdas válidas para moverse
            self.state = "Stuck"
            return
        
        # Determinar la mejor celda siguiendo la dirección del camino
        next_cell = None
        
        if isinstance(current_road_direction, tuple):
            # Es una intersección, tengo dos direcciones posibles
            direction1, direction2 = current_road_direction
            for cell in valid_cells:
                cell_direction = self.get_road_direction(cell)
                # Puedo moverme en cualquiera de las dos direcciones de la intersección
                if cell_direction == direction1 or cell_direction == direction2:
                    # Verificar semáforo antes de avanzar
                    if self.evaluate_traffic_light(cell):
                        next_cell = cell
                        break
                    else:
                        # Semáforo en rojo
                        self.state = "Waiting_traffic_light"
                        return
        else:
            # Es una calle normal, solo una dirección
            for cell in valid_cells:
                cell_direction = self.get_road_direction(cell)
                if cell_direction == current_road_direction:
                    # Verificar semáforo antes de avanzar
                    if self.evaluate_traffic_light(cell):
                        next_cell = cell
                        break
                    else:
                        # Semáforo en rojo
                        self.state = "Waiting_traffic_light"
                        return
        
        # Mover el carro si encontramos una celda válida
        if next_cell:
            self.cell = next_cell
            self.state = "Exploring"
        else:
            # No hay movimiento válido
            self.state = "Stuck"
        

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

    def step(self):
        """ 
        Determines the new direction it will take, and then moves
        """

        if self.state == "In_destination":
            self.remove()

        # # 2. máquina de estados
        # if state == "Following_route":
        #     self.following_path()
            

        elif self.state == "Waiting_traffic_light":
            # Cambiar intervalo a counter semaforo
            check_interval = 5
            if self.model.step_count % check_interval == 0:
                self.state = "Exploring"
                self.move()


        elif self.state == "Waiting_car":
            check_interval = 1
            if self.model.step_count % check_interval == 0:
                self.state = "Exploring"
                self.move()

        # elif state == "Recalculating_route":
        #     a_estrella()
        #     if success: state = "Following_route"
        #     else: state = "Exploring"

        elif self.state == "Exploring":
            self.move()


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
