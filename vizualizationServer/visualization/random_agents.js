"use strict";

import * as twgl from "twgl-base.js";
import GUI from "lil-gui";
import { M4 } from "../libs/3d-lib";
import { Scene3D } from "../libs/scene3d";
import { Object3D } from "../libs/object3d";
import { Camera3D } from "../libs/camera3d";

// Functions and arrays for the communication with the API
import {
  cars,
  obstacles,
  traffic_lights,
  roads,
  destinations,
  initAgentsModel,
  update,
  getObstacles,
  getCars,
  getRoad,
  getTrafficLights,
  getDestinations,
} from "../libs/api_connection.js";

// Define the shader code, using GLSL 3.00
import vsGLSL from "../assets/shaders/vs_color.glsl?raw";
import fsGLSL from "../assets/shaders/fs_color.glsl?raw";
import coralObj1 from "../obj/Coral1.obj?raw";
import coralObj2 from "../obj/Coral2.obj?raw";
import coralObj3 from "../obj/Coral3.obj?raw";
import coralObj4 from "../obj/Coral4.obj?raw";
import bigFanShellObj from "../obj/BigFanShell.obj?raw";
import starfishObj from "../obj/starfish.obj?raw";
import pezObj from "../obj/pez1.obj?raw";
import vsTexture from "../assets/shaders/vs_color_texture.glsl?raw";
import fsTexture from "../assets/shaders/fs_color_texture.glsl?raw";
import vsSkybox from "../assets/shaders/vs_skybox.glsl?raw";
import fsSkybox from "../assets/shaders/fs_skybox.glsl?raw";
import { cubeTextured, skyboxCube } from '../libs/shapes';
import starfishTextureUrl from "../textures/starfish.png";
import sandRoadTextureUrl from "../textures/sand.png";
import skyboxTextureUrl from "../textures/skyrender.png";

const scene = new Scene3D();


// Variable for slider settings
const settings = {
    // Simulation parameters
    simulationParameters: {
      spawn_time: 10,
      cars: 3000,
    }
};


// Global variables
let colorProgramInfo = undefined;
let textureProgramInfo = undefined;
let skyboxProgramInfo = undefined;
let starfishTexture = undefined;
let sandRoadTexture = undefined;
let carModel = undefined;
let gl = undefined;
const duration = 500; // ms // Speed de la simulación
let elapsed = 0;
let then = 0;

let lightDirection = [0.5, -1.0, 0.5]; // Dirección de la luz (como sol)
let lightColor = [1.0, 1.0, 1.0];     // Color de la luz (blanco)
let lightIntensity = 1;              // Intensidad de la luz


// Main function is async to be able to make the requests
async function main() {
  // Setup the canvas area
  const canvas = document.querySelector("canvas");
  gl = canvas.getContext("webgl2");
  twgl.resizeCanvasToDisplaySize(gl.canvas);
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

  // Prepare the program with the shaders
  colorProgramInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);
  textureProgramInfo = twgl.createProgramInfo(gl, [vsTexture, fsTexture]);
  skyboxProgramInfo = twgl.createProgramInfo(gl, [vsSkybox, fsSkybox]);

  starfishTexture = twgl.createTexture(gl, { src: starfishTextureUrl, flipY: 1 });
  sandRoadTexture = twgl.createTexture(gl, { src: sandRoadTextureUrl, flipY: 1 });

  // Prepare the user interface
  setupUI();

  // Initialize the agents model
  await initAgentsModel();

  // Get the agents and obstacles
  await getObstacles();
  await getCars();
  await getRoad();
  await getTrafficLights();
  await getDestinations();

  // Initialize the scene
  setupScene();

  /* Primero se inicia el modelo, se obtienen las caracteríticas de cada modelo, 
   y con esa información se dibuja la escena */

  // Position the objects in the scene
  setupObjects(scene, gl, colorProgramInfo, textureProgramInfo);

  // Fisrt call to the drawing loop
  drawScene();
}

function setupScene() {
  let camera = new Camera3D(
    0,
    25, // Distance to target
    4, // Azimut
    1, // Elevation
    [0, 0, 20], // Posición que cubra ambos grupos
    [5, 0, 5]
  );
  // These values are empyrical.
  // Maybe find a better way to determine them
  camera.panOffset = [0, 10, 2];
  scene.setCamera(camera);
  scene.camera.setupControls();
}

function setupObjects(scene, gl, programInfo, textureProgramInfo) {
  // Create VAOs for the different shapes
  const baseCube = new Object3D(-1);
  baseCube.prepareVAO(gl, programInfo);

  // Store the car model for later use
  const pezModel = new Object3D(-8, [0,0,0], [0,0,0], [0.5, 0.5, 0.5]);
  pezModel.prepareVAO(gl, programInfo, pezObj);
  carModel = pezModel;

  const coralModel1 = new Object3D(-2, [0,0,0], [0,0,0], [1.0, 3.0, 1.0]);
  coralModel1.prepareVAO(gl, programInfo, coralObj1);
  const coralModel2 = new Object3D(-3, [0,0,0], [0,0,0], [1.0, 5.0, 1.0]);
  coralModel2.prepareVAO(gl, programInfo, coralObj2);
  const coralModel3 = new Object3D(-4, [0,0,0], [0,0,0], [1.0, 3.0, 1.0]);
  coralModel3.prepareVAO(gl, programInfo, coralObj3);
  // const coralModel4 = new Object3D(-5, [0,0,0], [0,0,0], [0.5, 1.5, 0.5]);
  // coralModel4.prepareVAO(gl, programInfo, coralObj4);

  const coralModels = [coralModel1, coralModel2, coralModel3,];

  const bigFanShellModel = new Object3D(-6, [0,0,0], [0,0,0], [3.0, 4.0, 3.0]);
  bigFanShellModel.prepareVAO(gl, programInfo, bigFanShellObj);

  const starfishModel = new Object3D(-7, [0,0,0], [0,0,0], [0.2, 0.2, 0.2]);
  starfishModel.prepareVAO(gl, textureProgramInfo, starfishObj);
  starfishModel.texture = starfishTexture;

  const textureCubeArrays = cubeTextured(0.5);
  const textureCubeBufferInfo = twgl.createBufferInfoFromArrays(gl, textureCubeArrays);
  const textureCubeVAO = twgl.createVAOFromBufferInfo(gl, textureProgramInfo, textureCubeBufferInfo)

  const sandFloor = new Object3D(
      -1000,  // ID único para el piso
      [17, 0.9, 17],  // Posición: debajo de todo
      [0, 0, 0],   // Sin rotación
      [35, 0.1, 35],  // Escala
      [1, 1, 1, 1]  // Color blanco
  );
  
  // Asigna los buffers de textura
  sandFloor.arrays = textureCubeArrays;
  sandFloor.bufferInfo = textureCubeBufferInfo;
  sandFloor.vao = textureCubeVAO;
  sandFloor.texture = sandRoadTexture;
  sandFloor.texScale = 10;
  
  const skyboxTexture = twgl.createTexture(gl, { src: skyboxTextureUrl, flipY: 1 });
  
  const skyboxArrays = skyboxCube(0.5);
  const skyboxBufferInfo = twgl.createBufferInfoFromArrays(gl, skyboxArrays);
  const skyboxVAO = twgl.createVAOFromBufferInfo(gl, skyboxProgramInfo, skyboxBufferInfo);

  const skybox = new Object3D(
      -999, 
      [0, 0, 0], 
      [0, 0, 0], 
      [-100, -100, -100], 
      [1, 1, 1, 1]
  );
  skybox.arrays = skyboxArrays;
  skybox.bufferInfo = skyboxBufferInfo;
  skybox.vao = skyboxVAO;
  skybox.texture = skyboxTexture;
  scene.addObject(skybox);

  scene.addObject(sandFloor);

  // Copy the properties of the cars
  for (const car of cars) {
    car.arrays = carModel.arrays;
    car.bufferInfo = carModel.bufferInfo;
    car.vao = carModel.vao;
    car.scale = { ...carModel.scale };
    car.color = [Math.random(), Math.random(), Math.random(), 1.0];
    scene.addObject(car);
  }

  // Copy the properties of the obstacles
  for (const obstacle of obstacles) {
    const randomCoral = coralModels[Math.floor(Math.random() * coralModels.length)];
    obstacle.arrays = randomCoral.arrays;
    obstacle.bufferInfo = randomCoral.bufferInfo;
    obstacle.vao = randomCoral.vao;
    obstacle.scale = { ...randomCoral.scale };
    // Random color
    obstacle.color = [Math.random(), Math.random(), Math.random(), 1.0];
    
    // Random rotation
    obstacle.rotDeg.y = Math.random() * 360;
    obstacle.rotRad.y = obstacle.rotDeg.y * Math.PI / 180;

    scene.addObject(obstacle);
  }

  // Copy the properties of the road cells
  for (const road of roads) {
      road.arrays = textureCubeArrays;
      road.bufferInfo = textureCubeBufferInfo;
      road.vao = textureCubeVAO;
      road.texture = sandRoadTexture;        
      road.scale = { x: 2.0, y: 0.05, z: 2.0 };
      road.color = [1, 1, 1, 1];
      scene.addObject(road);
    }

  // Copy the properties of the traffic lights
  for (const tl of traffic_lights) {
    tl.arrays = bigFanShellModel.arrays;
    tl.isTrafficLight = true;
    tl.state = 'red';
    tl.bufferInfo = bigFanShellModel.bufferInfo;
    tl.vao = bigFanShellModel.vao;
    tl.scale = { ...bigFanShellModel.scale };
    tl.color = [1, 1, 1, 1.0]; // BLANCO
    scene.addObject(tl);
  }

  // Copy the properties of the destinations
  for (const des of destinations) {
    des.arrays = starfishModel.arrays;
    des.bufferInfo = starfishModel.bufferInfo;
    des.vao = starfishModel.vao;
    des.texture = starfishModel.texture;
    des.scale = { ...starfishModel.scale };
    des.color = [0, 1, 0, 1.0]; // VERDE (ignored if textured)

    des.rotDeg.x = -90;
    des.rotRad.x = des.rotDeg.x * Math.PI / 180;

    scene.addObject(des);
  }
}

// Draw an object with its corresponding transformations
// Draw an object with its corresponding transformations
function drawObject(gl, programInfo, object, viewProjectionMatrix, fract) {
  // Preparar vectores para translación y escala
  let v3_tra = object.posArray;
  let v3_sca = object.scaArray;
  // Aquí se hace el calculo de animación
  // Se usa fract (tiempo transcurrido entre 0 y 1)

  // Crear matrices de transformación individuales
  const scaMat = M4.scale(v3_sca);
  const rotXMat = M4.rotationX(object.rotRad.x);
  const rotYMat = M4.rotationY(object.rotRad.y);
  const rotZMat = M4.rotationZ(object.rotRad.z);
  const traMat = M4.translation(v3_tra);

  // Crear matriz compuesta con todas las transformaciones
  let transforms = M4.identity();
  transforms = M4.multiply(scaMat, transforms);
  transforms = M4.multiply(rotXMat, transforms);
  transforms = M4.multiply(rotYMat, transforms);
  transforms = M4.multiply(rotZMat, transforms);
  transforms = M4.multiply(traMat, transforms);

  object.matrix = transforms;

  // Aplicar la proyección para la matriz World-View-Projection
  const wvpMat = M4.multiply(viewProjectionMatrix, transforms);

  // Uniforms del modelo
  let objectUniforms = {
    u_transforms: wvpMat,
    u_world: transforms,  
    u_lightDirection: lightDirection,
    u_color: object.color,
  };
  
  // Agregar luz específica para semáforos
  if (object.isTrafficLight) {
    // Usar el estado real del semáforo
    const trafficLightColor = getTrafficLightColor(object.state);
    objectUniforms.u_lightColor = trafficLightColor;
    objectUniforms.u_lightIntensity = 2.0; // Más intenso para semáforos
    objectUniforms.u_objectColor = object.color;
  } else {
    // Luz normal para otros objetos
    objectUniforms.u_lightColor = lightColor;
    objectUniforms.u_lightIntensity = lightIntensity;
    objectUniforms.u_objectColor = [0, 0, 0, 0]; // Sin color específico
  }
  
  if (object.texture) {
    objectUniforms.u_texture = object.texture;
  }
  
  twgl.setUniforms(programInfo, objectUniforms);

  gl.bindVertexArray(object.vao);
  twgl.drawBufferInfo(gl, object.bufferInfo);
}

// Función auxiliar para obtener color del semáforo
function getTrafficLightColor(state) {
    if (!state) return [1.0, 1.0, 1.0]; // Color neutro por defecto
    
    switch(state.toLowerCase()) {
        case 'green': 
            return [0.0, 1.0, 0.0];    // Verde
        case 'red': 
        default: 
            return [1.0, 0.0, 0.0];    // Rojo
    }
}

// Function to do the actual display of the objects
async function drawScene() {
  // Compute time elapsed since last frame
  let now = Date.now();
  let deltaTime = now - then;
  elapsed += deltaTime;
  let fract = Math.min(1.0, elapsed / duration);
  then = now;

  // Clear the canvas
  gl.clearColor(0, 0, 0, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  // tell webgl to cull faces
  gl.enable(gl.CULL_FACE);
  gl.enable(gl.DEPTH_TEST);

  scene.camera.checkKeys();
  //console.log(scene.camera);
  const viewProjectionMatrix = setupViewProjection(gl);

  // Draw the objects
  for (let object of scene.objects) {
    let programInfo = object.texture ? textureProgramInfo : colorProgramInfo;
    
    // Use special shader for skybox
    if (object.id === -999) {
        programInfo = skyboxProgramInfo;
    }

    gl.useProgram(programInfo.program);
    drawObject(gl, programInfo, object, viewProjectionMatrix, fract);
  }

  // Update the scene after the elapsed duration
  if (elapsed >= duration) {
    elapsed = 0;
    await getTrafficLights()
    await update();
    syncSceneObjects();
  }

  requestAnimationFrame(drawScene);
}

function syncSceneObjects() {
  // Add new cars to the scene
  for (const car of cars) {
    const sceneCar = scene.objects.find(obj => obj.id == car.id);
    
    if (sceneCar) {
      // Si ya existe, verificar si se movió
      if (sceneCar.oldPos) {
        // Calcular cambio de posición
        const dx = car.position.x - sceneCar.oldPos.x;
        const dz = car.position.z - sceneCar.oldPos.z;
        
        // Rotar si se movió
        if (dx !== 0 || dz !== 0) {
          const angle = Math.atan2(-dx, -dz);  // Calcular ángulo hacia donde se mueve
          sceneCar.rotDeg.y = angle * (180 / Math.PI);
          sceneCar.rotRad.y = angle;           
        }
      }
      
      // Guardar posición actual como vieja para la próxima vez
      sceneCar.oldPos = {
        x: car.position.x,
        y: car.position.y, 
        z: car.position.z
      };
      
      // Actualizar posición en la escena
      sceneCar.position.x = car.position.x;
      sceneCar.position.y = car.position.y;
      sceneCar.position.z = car.position.z;
      
    } else if (car.vao == undefined && carModel != undefined) {
      // Nuevo pez
      car.arrays = carModel.arrays;
      car.bufferInfo = carModel.bufferInfo;
      car.vao = carModel.vao;
      car.scale = { ...carModel.scale };
      car.color = [Math.random(), Math.random(), Math.random(), 1.0];
      
      // Guardar posición inicial
      car.oldPos = {
        x: car.position.x,
        y: car.position.y,
        z: car.position.z
      };
      
      scene.addObject(car);
    }
  }
}

function setupViewProjection(gl) {
  // Field of view of 60 degrees vertically, in radians
  const fov = (60 * Math.PI) / 180;
  const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;

  // Matrices for the world view
  const projectionMatrix = M4.perspective(fov, aspect, 1, 200);

  const cameraPosition = scene.camera.posArray;
  const target = scene.camera.targetArray;
  const up = [0, 1, 0];

  const cameraMatrix = M4.lookAt(cameraPosition, target, up);
  const viewMatrix = M4.inverse(cameraMatrix);
  const viewProjectionMatrix = M4.multiply(projectionMatrix, viewMatrix);

  return viewProjectionMatrix;
}

// Setup a ui.
function setupUI() {
  
  const gui = new GUI();

  // Settings for the animation
  const simulationFolder = gui.addFolder('Simulation:');
  simulationFolder.add( settings.simulationParameters, 'spawn_time', 1, 20)
      .decimals(0)
      .name('Spawn time')
      .onChange(async (value) => {
          // Actualizar la variable global en api_connection.js
          if (window.apiSettings) {
              window.apiSettings.spawn_time = value;
          }
          // Reinicializar el modelo con el nuevo número de agentes
          await reinitializeModel();
      });
  simulationFolder.add( settings.simulationParameters, 'cars', 0, 300)
      .decimals(0)
      .name('Number of agents')
      .onChange(async (value) => {
          // Actualizar la variable global en api_connection.js
          if (window.apiSettings) {
              window.apiSettings.number_agents = value;
          }
          // Reinicializar el modelo con el nuevo número de agentes
          await reinitializeModel();
      });
}

async function reinitializeModel() {
  console.log(`Reinitializing model with ${settings.simulationParameters.cars} agents`);
  
  try {
    // Limpiar TODOS los arrays globales importados
    cars.length = 0;
    obstacles.length = 0;
    traffic_lights.length = 0;
    roads.length = 0;
    destinations.length = 0;
    
    // Limpiar la escena actual
    scene.objects = [];
    
    // Reinicializar el modelo
    await initAgentsModel();
    
    // Obtener los nuevos datos
    await getObstacles();
    await getCars();
    await getRoad();
    await getTrafficLights();
    await getDestinations();
    
    // Reconfigurar objetos
    setupObjects(scene, gl, colorProgramInfo, textureProgramInfo);
    
    console.log(`Model reinitialized. Cars: ${cars.length}, Obstacles: ${obstacles.length}`);
  } catch (error) {
    console.error("Error reinitializing model:", error);
  }
}

main();
