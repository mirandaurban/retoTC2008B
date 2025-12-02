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

import starfishTextureUrl from "../textures/starfish.png";

const scene = new Scene3D();

/*
// Variable for the scene settings
const settings = {
    // Speed in degrees
    rotationSpeed: {
        x: 0,
        y: 0,
        z: 0,
    },
};
*/

// Global variables
let colorProgramInfo = undefined;
let textureProgramInfo = undefined;
let starfishTexture = undefined;
let carModel = undefined;
let gl = undefined;
const duration = 1000; // ms
let elapsed = 0;
let then = 0;

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

  starfishTexture = twgl.createTexture(gl, { src: starfishTextureUrl, flipY: 1 });

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

  // Prepare the user interface
  setupUI();

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
  const coralModel4 = new Object3D(-5, [0,0,0], [0,0,0], [0.5, 1.5, 0.5]);
  coralModel4.prepareVAO(gl, programInfo, coralObj4);

  const coralModels = [coralModel1, coralModel2, coralModel3, coralModel4];

  const bigFanShellModel = new Object3D(-6, [0,0,0], [0,0,0], [3.0, 4.0, 3.0]);
  bigFanShellModel.prepareVAO(gl, programInfo, bigFanShellObj);

  const starfishModel = new Object3D(-7, [0,0,0], [0,0,0], [0.2, 0.2, 0.2]);
  starfishModel.prepareVAO(gl, textureProgramInfo, starfishObj);
  starfishModel.texture = starfishTexture;

  /*
  // A scaled cube to use as the ground
  const ground = new Object3D(-3, [14, 0, 14]);
  ground.arrays = baseCube.arrays;
  ground.bufferInfo = baseCube.bufferInfo;
  ground.vao = baseCube.vao;
  ground.scale = {x: 50, y: 0.1, z: 50};
  ground.color = [0.6, 0.6, 0.6, 1];
  scene.addObject(ground);
  */

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

  // Copy the properties of the roads
  for (const road of roads) {
    road.arrays = baseCube.arrays;
    road.bufferInfo = baseCube.bufferInfo;
    road.vao = baseCube.vao;
    road.scale = { x: 0.5, y: 0.1, z: 0.5 };
    road.color = [0.2, 0.4, 0.8, 1.0]; // AZUL
    scene.addObject(road);
  }

  // Copy the properties of the traffic lights
  for (const tl of traffic_lights) {
    tl.arrays = bigFanShellModel.arrays;
    tl.bufferInfo = bigFanShellModel.bufferInfo;
    tl.vao = bigFanShellModel.vao;
    tl.scale = { ...bigFanShellModel.scale };
    tl.color = [1, 0.8, 0, 1.0]; // AMARILLO
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
function drawObject(gl, programInfo, object, viewProjectionMatrix, fract) {
  // Prepare the vector for translation and scale
  let v3_tra = object.posArray;
  let v3_sca = object.scaArray;

  /*
  // Animate the rotation of the objects
  object.rotDeg.x = (object.rotDeg.x + settings.rotationSpeed.x * fract) % 360;
  object.rotDeg.y = (object.rotDeg.y + settings.rotationSpeed.y * fract) % 360;
  object.rotDeg.z = (object.rotDeg.z + settings.rotationSpeed.z * fract) % 360;
  object.rotRad.x = object.rotDeg.x * Math.PI / 180;
  object.rotRad.y = object.rotDeg.y * Math.PI / 180;
  object.rotRad.z = object.rotDeg.z * Math.PI / 180;
  */

  // Create the individual transform matrices
  const scaMat = M4.scale(v3_sca);
  const rotXMat = M4.rotationX(object.rotRad.x);
  const rotYMat = M4.rotationY(object.rotRad.y);
  const rotZMat = M4.rotationZ(object.rotRad.z);
  const traMat = M4.translation(v3_tra);

  // Create the composite matrix with all transformations
  let transforms = M4.identity();
  transforms = M4.multiply(scaMat, transforms);
  transforms = M4.multiply(rotXMat, transforms);
  transforms = M4.multiply(rotYMat, transforms);
  transforms = M4.multiply(rotZMat, transforms);
  transforms = M4.multiply(traMat, transforms);

  object.matrix = transforms;

  // Apply the projection to the final matrix for the
  // World-View-Projection
  const wvpMat = M4.multiply(viewProjectionMatrix, transforms);

  // Model uniforms
  let objectUniforms = {
    u_transforms: wvpMat,
    u_color: object.color, // ✅ Pasar el color como uniform
  };
  if (object.texture) {
    objectUniforms.u_texture = object.texture;
  }
  twgl.setUniforms(programInfo, objectUniforms);

  gl.bindVertexArray(object.vao);
  twgl.drawBufferInfo(gl, object.bufferInfo);
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
    gl.useProgram(programInfo.program);
    drawObject(gl, programInfo, object, viewProjectionMatrix, fract);
  }

  // Update the scene after the elapsed duration
  if (elapsed >= duration) {
    elapsed = 0;
    await update();
    syncSceneObjects();
  }

  requestAnimationFrame(drawScene);
}

function syncSceneObjects() {
  // Add new cars to the scene
  for (const car of cars) {
    if (car.vao == undefined && carModel != undefined) {
      car.arrays = carModel.arrays;
      car.bufferInfo = carModel.bufferInfo;
      car.vao = carModel.vao;
      car.scale = { ...carModel.scale };
      car.color = [Math.random(), Math.random(), Math.random(), 1.0];
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
  /*
  const gui = new GUI();

  // Settings for the animation
  const animFolder = gui.addFolder('Animation:');
  animFolder.add( settings.rotationSpeed, 'x', 0, 360)
      .decimals(2)
  animFolder.add( settings.rotationSpeed, 'y', 0, 360)
      .decimals(2)
  animFolder.add( settings.rotationSpeed, 'z', 0, 360)
      .decimals(2)
  */
}

main();
