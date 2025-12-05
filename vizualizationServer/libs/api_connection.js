/*
 * Functions to connect to an external API to get the coordinates of agents
 * Funciones para hacer llamadas al servidor
 *
 * Gilberto Echeverria
 * 2025-11-08
 */


'use strict';

import { Object3D } from '../libs/object3d';

// Define the agent server URI
const agent_server_uri = "http://localhost:8585/";

// Initialize arrays to store agents and obstacles
const obstacles = [];
const traffic_lights = [];
const roads = [];
const cars = [];
const destinations = [];

// Define the data object
/// Datos iniciales para la simulación
const initData = {
    NAgents: 20,
};

// En api_connection.js
const apiSettings = {
    number_agents: 5000,
    spawn_time: 2
};

// Hacerlo disponible globalmente
if (typeof window !== 'undefined') {
    window.apiSettings = apiSettings;
}


/* FUNCTIONS FOR THE INTERACTION WITH THE MESA SERVER */

/*
 * Initializes the agents model by sending a POST request to the agent server.
 * Envía un diccionario para que se inicialize en el servidor
 */
async function initAgentsModel() {
    const url = "http://localhost:8585/init";
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                NAgents: apiSettings.number_agents,
                STime: apiSettings.spawn_time
            })
        });
        
        const data = await response.json();
        console.log(data.message);
        return data;
    } catch (error) {
        console.error("Error initializing agents model:", error);
    }
}

/*
 * Retrieves the current positions of all agents from the agent server.
 * Contesta con todos los agentes que están en la simulación.
 * Regresa toda la infomación de los agentes (id, pos en x,y,z)
 * Aquí se debe de modificar si se requiere info extra
 */
async function getCars() {
    try {
        // Send a GET request to the agent server to retrieve the agent positions
        let response = await fetch(agent_server_uri + "getCars");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Log the agent positions
            //console.log("getAgents positions: ", result.positions)

            // Check if the agents array is empty
            // Poner la visualización inicial de los agentes
            // Se debe de cambiar esto para poder agregar nuevos agentes
            if (cars.length == 0) {
                // Create new agents and add them to the agents array
                for (const car of result.positions) {
                    const newCar = new Object3D(car.id, [car.x, car.y, car.z]);
                    // Store the initial position
                    newCar['oldPosArray'] = newCar.posArray;
                    cars.push(newCar);
                }
                // Log the agents array
                //console.log("Agents:", agents);

            } else { // Para iteraciones futuras, actualizar la posición
                // Get IDs from server response
                const serverCarIds = new Set(result.positions.map(c => c.id));
                
                // Remove cars that are no longer in the server response
                for (let i = cars.length - 1; i >= 0; i--) {
                    if (!serverCarIds.has(cars[i].id)) {
                        cars.splice(i, 1);
                    }
                }
                
                // Update the positions of existing agents
                // Sincronización entre el objeto de Mesa y el de WebGL
                for (const car of result.positions) {
                    const current_car = cars.find((object3d) => object3d.id == car.id);

                    // Check if the agent exists in the agents array
                    if(current_car != undefined){
                        // Update the agent's position
                        current_car.oldPosArray = current_car.posArray;
                        current_car.position = {x: car.x, y: car.y, z: car.z};
                    } else {
                        // Create new car if it doesn't exist
                        const newCar = new Object3D(car.id, [car.x, car.y, car.z]);
                        newCar['oldPosArray'] = newCar.posArray;
                        cars.push(newCar);
                    }

                    //console.log("OLD: ", current_agent.oldPosArray,
                    //            " NEW: ", current_agent.posArray);
                }
            }
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all obstacles from the agent server.
 * Obtiene la información de los obstáculos (id's, posiciones iniciales)
 */
async function getObstacles() {
    try {
        // Send a GET request to the agent server to retrieve the obstacle positions
        let response = await fetch(agent_server_uri + "getObstacles");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new obstacles and add them to the obstacles array
            for (const obstacle of result.positions) {
                const newObstacle = new Object3D(obstacle.id, [obstacle.x, obstacle.y, obstacle.z]);
                obstacles.push(newObstacle);
            }
            // Log the obstacles array
            //console.log("Obstacles:", obstacles);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all traffic lights from the agent server.
 * Obtiene la información de los semáforos (id's, posiciones iniciales)
 */
/*
 * Retrieves the current positions of all traffic lights from the agent server.
 * Obtiene la información de los semáforos (id's, posiciones iniciales)
 */
async function getTrafficLights() {
    try {
        let response = await fetch(agent_server_uri + "getTrafficLights");

        if (response.ok) {
            let result = await response.json();

            // Si es la primera vez, crea los semáforos
            if (traffic_lights.length == 0) {
                for (const tl of result.positions) {
                    const newTrafficLight = new Object3D(tl.id, [tl.x, tl.y, tl.z]);
                    newTrafficLight.state = tl.state || 'red';  // 'green' o 'red'
                    newTrafficLight.direction = tl.direction || null;
                    traffic_lights.push(newTrafficLight);
                }
            } else { 
                for (const tl of result.positions) {
                    const current_tl = traffic_lights.find((object3d) => object3d.id == tl.id);

                    if(current_tl != undefined){
                        current_tl.position = {x: tl.x, y: tl.y, z: tl.z};
                        // ACTUALIZAR ESTADO
                        current_tl.state = tl.state || 'red';
                        current_tl.direction = tl.direction || null;
                    } else {
                        // Crear nuevo semáforo si no existe
                        const newTrafficLight = new Object3D(tl.id, [tl.x, tl.y, tl.z]);
                        newTrafficLight.state = tl.state || 'red';
                        newTrafficLight.direction = tl.direction || null;
                        traffic_lights.push(newTrafficLight);
                    }
                }
            }
        }

    } catch (error) {
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all road cells from the agent server.
 * Obtiene la información de las celdas de camino (id's, posiciones iniciales)
 */
async function getRoad() {
    try {
        // Send a GET request to the agent server to retrieve the road positions
        let response = await fetch(agent_server_uri + "getRoad");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new road and add them to the road array
            for (const road of result.positions) {
                const newRoad = new Object3D(road.id, [road.x, road.y, road.z]);
                roads.push(newRoad);
            }
            // Log the obstacles array
            //console.log("Obstacles:", obstacles);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all destinations from the agent server.
 * Obtiene la información de los destinos (id's, posiciones iniciales)
 */
async function getDestinations() {
    try {
        // Send a GET request to the agent server to retrieve the obstacle positions
        let response = await fetch(agent_server_uri + "getDestinations");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new obstacles and add them to the obstacles array
            for (const destination of result.positions) {
                const newDestination = new Object3D(destination.id, [destination.x, destination.y, destination.z]);
                destinations.push(newDestination);
            }
            // Log the obstacles array
            //console.log("Obstacles:", obstacles);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

/*
 * Updates the agent positions by sending a request to the agent server.
 * Step del modelo y vuelve a llamar a GetAgents para ver sus nuevas posiciones
 */
async function update() {
    try {
        // Send a request to the agent server to update the agent positions
        let response = await fetch(agent_server_uri + "update");

        // Check if the response was successful
        if (response.ok) {
            // Retrieve the updated agent positions
            await getCars();
            await getTrafficLights();
            // Log a message indicating that the agents have been updated
            //console.log("Updated agents");
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

export {    obstacles, cars, traffic_lights, roads, destinations,
            initAgentsModel, update, 
            getObstacles, getCars, getTrafficLights, getRoad, getDestinations };
