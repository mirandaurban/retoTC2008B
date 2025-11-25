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
        self.initial_direction = "<"

    def evaluate_traffic_light(self, cells_with_traffic_light):
        return 0

    # Return an array with the position of each near cell with destinations (radius: 2)
    def is_cells_a_destination(self):
        cells_with_destination = self.cell.get_neighborhood(2, False).select(
            lambda cell: any(isinstance(obj, Destination) for obj in cell.agents)
        )
        return cells_with_destination

    # Return an array with the position of each near cell with traffic lights (radius: 2)
    def is_cells_with_traffic_light(self):
        cells_with_traffic_light = self.cell.get_neighborhood(2, False).select(
            lambda cell: any(isinstance(obj, Traffic_Light) for obj in cell.agents)
        )
        return cells_with_traffic_light

    # Return an array with the position of each near cell without obstacles (radius: 2)
    def is_cells_without_obstacles(self):
        cells_without_obstacles = self.cell.get_neighborhood(2, False).select(
            lambda cell: not any(isinstance(obj, Obstacle) for obj in cell.agents)
        )
        return cells_without_obstacles

    # Return an array with the position of each near cell with road (radius: 1)
    def is_cells_a_road(self):
        cells_with_road = self.cell.neighborhood.select(
            lambda cell: any(isinstance(obj, Road) for obj in cell.agents)
        )
        return cells_with_road

    def direction_car(self, cell_inicial, cell_next, current_direction):
        x1 = cell_inicial.coordinate[0]
        y1 = cell_inicial.coordinate[1]
        x2 = cell_next.coordinate[0] 
        y2 = cell_next.coordinate[1] 


    def move(self):
        possible_cells = []

        cells_without_obstacles = self.is_cells_without_obstacles()
        cells_with_traffic_light = self.is_cells_with_traffic_light()
        cells_with_destination = self.is_cells_a_destination()
        cells_with_road = self.is_cells_a_road()

        print("Celdas con obs")
        print(cells_without_obstacles)
        print("Celdas con camino")
        print(cells_with_road)

        # Filtra las posibles celdas considerando que formen parte del camino, semáforos y destinos, pero que no tengan obstáculos
        for cells in cells_without_obstacles:
            if cells in cells_with_road or cells_with_traffic_light or cells_with_destination:
                possible_cells.append(cells)
            
        print("Possible cells")
        print(possible_cells)




        new_cell = possible_cells[0]
        self.cell = new_cell

        # Checks which grid cells are empty
        

    def step(self):
        """ 
        Determines the new direction it will take, and then moves
        """
        self.move()
        pass

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
        """
        super().__init__(model)
        self.cell = cell
        self.direction = direction
