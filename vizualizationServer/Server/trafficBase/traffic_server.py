# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python flask server to interact with webGL.
# Octavio Navarro. 2024

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from traffic_base.model import CityModel
from traffic_base.agent import Car, Traffic_Light, Destination, Obstacle, Road

# Size of the board:
# Declarar variables globales cin características del agente y dónde se guarda el modelo
number_agents = 10
width = 28
height = 28
randomModel = None
currentStep = 0

########################################################################
### Initialize the interaction between the simulation and the server ###
########################################################################

# This application will be used to interact with WebGL
# Flask es una librería que permite hacer un servidor 
app = Flask("Traffic example")
cors = CORS(app, origins=['http://localhost'])

# This route will be used to send the parameters of the simulation to the server.
# The servers expects a POST request with the parameters in a.json.
@app.route('/init', methods=['GET', 'POST'])
@cross_origin()
def initModel():
    global currentStep, randomModel, number_agents, width, height

    if request.method == 'POST':
        try:
            number_agents = int(request.json.get('NAgents'))
            width = int(request.json.get('width'))
            height = int(request.json.get('height'))
            currentStep = 0

        except Exception as e:
            print(e)
            return jsonify({"message": "Error initializing the model"}), 500

    print(f"Model parameters:{number_agents, width, height}")

    # Create the model using the parameters sent by the application
    randomModel = CityModel(number_agents)

    # Return a message to saying that the model was created successfully
    return jsonify({"message": f"Parameters recieved, model initiated.\nSize: {width}x{height}"})


####################################
### Get info from all the agents ###
####################################

# This route will be used to get the positions of the agent car
@app.route('/getCars', methods=['GET'])
@cross_origin()
def getCars():
    global randomModel

    if request.method == 'GET':
        # Get the positions of the agents and return them to WebGL in JSON.json.t.
        # Note that the positions are sent as a list of dictionaries, where each dictionary has the id and position of an agent.
        # The y coordinate is set to 1, since the agents are in a 3D world. The z coordinate corresponds to the row (y coordinate) of the grid in mesa.
        try:
            carCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Car) for obj in cell.agents)
            ).cells
            # print(f"CELLS: {agentCells}")

            cars = [
                (cell.coordinate, agent)
                for cell in carCells
                for agent in cell.agents
                if isinstance(agent, Car)
            ]
            # print(f"AGENTS: {cars}")

            carPositions = [
                {"id": str(car.unique_id), "x": coordinate[0], "y": 1, "z": coordinate[1]}
                for (coordinate, car) in cars
            ]
            # print(f"AGENT POSITIONS: {carPositions}")

            return jsonify({'positions': carPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with the agent positions"}), 500

# This route will be used to get the positions of the obstacles
@app.route('/getObstacles', methods=['GET'])
@cross_origin()
def getObstacles():
    global randomModel

    if request.method == 'GET':
        # Get the positions of the agents and return them to WebGL in JSON.json.t.
        # Note that the positions are sent as a list of dictionaries, where each dictionary has the id and position of an agent.
        # The y coordinate is set to 1, since the agents are in a 3D world. The z coordinate corresponds to the row (y coordinate) of the grid in mesa.
        try:
            obstacleCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Obstacle) for obj in cell.agents)
            ).cells
            # print(f"CELLS: {obstacleCells}")

            obstacles = [
                (cell.coordinate, agent)
                for cell in obstacleCells
                for agent in cell.agents
                if isinstance(agent, Obstacle)
            ]
            # print(f"AGENTS: {obstacles}")

            obstaclePositions = [
                {"id": str(obs.unique_id), "x": coordinate[0], "y": 1, "z": coordinate[1]}
                for (coordinate, obs) in obstacles
            ]
            # print(f"AGENT POSITIONS: {obstaclePositions}")

            return jsonify({'positions': obstaclePositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with the agent positions"}), 500

# This route will be used to get the positions of the road
@app.route('/getRoad', methods=['GET'])
@cross_origin()
def getRoad():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the road and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of a car.

            roadCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Road) for obj in cell.agents)
            )
            #print(f"CELLS: {roadCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in roadCells
                for agent in cell.agents
                if isinstance(agent, Road)
            ]
            # print(f"AGENTS: {roadCells}")

            roadPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":1, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            #print(f"ROAD POSITIONS: {roadPositions}")

            return jsonify({'positions': roadPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with road positions"}), 500

# This route will be used to get the positions of the traffic lights
@app.route('/getTrafficLights', methods=['GET'])
@cross_origin()
def getTrafficLights():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the traffic lights and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of a traffic lights.

            trafficLightsCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Traffic_Light) for obj in cell.agents)
            )
            # print(f"CELLS: {trafficLightsCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in trafficLightsCells
                for agent in cell.agents
                if isinstance(agent, Traffic_Light)
            ]
            # print(f"AGENTS: {trafficLightsCells}")

            trafficLightsPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":1, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            # print(f"TRAFFIC LIGHTS POSITIONS: {trafficLightsPositions}")

            return jsonify({'positions': trafficLightsPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with car positions"}), 500

# This route will be used to get the positions of the road
@app.route('/getDestinations', methods=['GET'])
@cross_origin()
def getDestinations():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the road and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of a car.

            destinationCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Destination) for obj in cell.agents)
            )
            #print(f"CELLS: {roadCells}")

            destinations = [
                (cell.coordinate, agent)
                for cell in destinationCells
                for agent in cell.agents
                if isinstance(agent, Destination)
            ]
            # print(f"AGENTS: {roadCells}")

            destinationPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":1, "z":coordinate[1]}
                for (coordinate, a) in destinations
            ]
            #print(f"ROAD POSITIONS: {destinationPositions}")

            return jsonify({'positions': destinationPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with road positions"}), 500


# This route will be used to update the model
# Hace el step del modelo
@app.route('/update', methods=['GET'])
@cross_origin()
def updateModel():
    global currentStep, randomModel
    if request.method == 'GET':
        try:
        # Update the model and return a message to WebGL saying that the model was updated successfully
            randomModel.step()
            currentStep += 1
            return jsonify({'message': f'Model updated to step {currentStep}.', 'currentStep':currentStep})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error during step."}), 500


if __name__=='__main__':
    # Run the flask server in port 8585
    app.run(host="localhost", port=8585, debug=True)
