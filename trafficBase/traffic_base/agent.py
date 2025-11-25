from mesa.discrete_space import CellAgent, FixedAgent

class Car(CellAgent):
    """
    Agent that moves randomly.
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
        self.known_destinations = [cell] # To keep a list of the known destinations of each car
        self.initial_direction = "Right" # Posición inicial default (cambiar después)
        self.current_direction = "Right"  

    def evaluate_traffic_light(self, cells_with_traffic_light):
        return 0

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
            lambda cell: any(isinstance(obj, Road) for obj in cell.agents)
        )
        return cells_with_road

    def get_road_direction(self, cell):
        """
        Obtains the direction expected by the road
        """
        for agent in cell.agents:
            if isinstance(agent, Road):
                return agent.direction
        return None

    def validate_road_direction(self, current_cell, next_cell):
        """
        Validate if the agent movement is correct according to the road direction
        """
        # Obtain coordindates of the current and next cell
        x1, y1 = current_cell.coordinate
        x2, y2 = next_cell.coordinate

        # Obtain the direction of the destiny cell
        road_direction = self.get_road_direction(next_cell)

        if not road_direction:
            return False

        if road_direction == "Down":
            # X remains equal, while y1 must be greater than y2
            return x1 == x2 and y1 == y2 + 1
        elif road_direction == "Up":
            # X remains equal, while y1 must be less than y2
            return x1 == x2 and y1 == y2 - 1
        elif road_direction == "Right":
            # y reamins equal, while x1 must be less than x2
            return y1 == y2 and x1 == x2 + 1
        elif road_direction == "Left":
            # y reamins equal, while x1 must be greater than x2
            return y1 == y2 and x1 == x2 - 1

        return False # If there is no cell that have those attributes


    def move(self):
        """
        Move the car according to the road directions
        """
        # Check if the current cell has road
        current_road_direction = self.get_road_direction(self.cell)        
        print(f"Carro en celda {self.cell.coordinate} con dirección de carretera: {current_road_direction}")
        
        # Obtain all the neighbor cells (radio 1)
        neighbor_cells = self.cell.neighborhood
        # print(f"Celdas vecinas: {[cell.coordinate for cell in neighbor_cells]}")
        
        # Filter cells to find just the valid ones
        possible_cells = []

        road_cells = self.is_cells_a_road()
        non_obstacles_cells = self.is_cells_without_obstacles()

        for cell in neighbor_cells:

            # Check if it is road
            if cell not in road_cells:
                continue
                
            # Check if has obstacles            
            if cell not in non_obstacles_cells:
                continue
                
            # Check if it has other cars
            has_cars = any(isinstance(agent, Car) for agent in cell.agents)
            
            if has_cars:
                continue
            
            # Check if the movement is valid according to the direction of the road
            is_valid_move = self.validate_road_direction(self.cell, cell)
            
            if is_valid_move:
                possible_cells.append(cell)
                
        # Move to the first cell, if possible
        if possible_cells:
            new_cell = possible_cells[0]
            self.update_direction(new_cell)
            old_position = self.cell.coordinate
            self.cell = new_cell

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
        self.move()


class Traffic_Light(FixedAgent):
    """
    Traffic light. Where the traffic lights are in the grid.
    """
    def __init__(self, model, cell, state = False, timeToChange = 10):
        """
        Creates a new Traffic light.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
            state: Whether the traffic light is green or red
            timeToChange: After how many step should the traffic light change color 
        """
        super().__init__(model)
        self.cell = cell
        self.state = state
        self.timeToChange = timeToChange

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
    def __init__(self, model, cell, direction= "Left"):
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
