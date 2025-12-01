// /*
//  * Script to read a model stored in Wavefront OBJ format
//  *
//  * Gilberto Echeverria
//  * 2025-07-29
//  */

// 'use strict';

// // Global variable for all materials loaded
// // NOTE: This is a bad idea. When materials have the same names,
// // it could cause confusion in the scene.
// let materials = {};
// let materialInUse = undefined;

// /*
//  * Extract the elements in a face as encoded in an OBJ file
//  * As faces are read, pass the information into the array that will be used
//  * to draw the object in WebGL
//  */
// function parseFace(parts, objData, arrays) {
//     // This will produce an array of arrays
//     // Each arrays corresponds has the vertices
//     // Each vertex is an array with its vertex, texture and normal indices
//     let faceVerts = parts.slice(1).map(face => face.split('/'));
//     faceVerts.forEach(vert => {
//         const vertex = vert != '' ? Number(vert) : undefined
//         if (vertex != undefined) {
//             // console.log(objData.vertices[vert[0]])

//             // First element is the vertex index
//             arrays.a_position.data.push(...objData.vertices[vert[0]]);
//             // Second element is the texture index
//             if (vert.length > 1 && vert[1] != "") {
//                 arrays.a_texCoord.data.push(...objData.textures[vert[1]]);
//             }
//             // Third element is the normal index
//             if (vert.length > 2 && vert[2] != "") {
//                 arrays.a_normal.data.push(...objData.normals[vert[2]]);
//             }

//             if (materialInUse) {
//                 arrays.a_color.data.push(...materialInUse['Kd'], 1);
//             } else {
//                 // Force a color for each vertex
//                 arrays.a_color.data.push(0.4, 0.4, 0.4, 1);
//             }
//             // This is not really necessary, but just in case
//             objData.faces.push({v: vert[0], t: vert[1], n: vert[2]});
//         }
//     });
// }

// /*
//  * Read the contents of an OBJ file received as a string
//  * Return an object called arrays, with the arrays necessary to build a
//  * Vertex Array Object (VAO) for WebGL.
//  */
// function loadObj(objString) {

//     // Initialize a dummy item in the lists as index 0
//     // This will make it easier to handle indices starting at 1 as used by OBJ
//     let objData = {
//         vertices: [ [0, 0, 0] ],
//         normals: [ [0, 0, 0] ],
//         textures: [ [0, 0, 0] ],
//         faces: [ ],
//     };

//     // The array with the attributes that will be passed to WebGL
//     let arrays = {
//         a_position: {
//             numComponents: 3,
//             data: [ ]
//         },
//         a_color: {
//             numComponents: 4,
//             data: [ ]
//         },
//         a_normal: {
//             numComponents: 3,
//             data: [ ]
//         },
//         a_texCoord: {
//             numComponents: 2,
//             data: [ ]
//         }
//     };

//     let partInfo;
//     let lines = objString.split('\n');
//     lines.forEach(line => {
//         let parts = line.split(/\s+/);
//         switch (parts[0]) {
//             case 'v':
//                 // Ignore the first part (the keyword),
//                 // remove any empty elements and convert them into a number
//                 partInfo = parts.slice(1).filter(v => v != '').map(Number);
//                 objData.vertices.push(partInfo);
//                 break;
//             case 'vn':
//                 partInfo = parts.slice(1).filter(vn => vn != '').map(Number);
//                 objData.normals.push(partInfo);
//                 break;
//             case 'vt':
//                 partInfo = parts.slice(1).filter(f => f != '').map(Number);
//                 objData.textures.push(partInfo);
//                 break;
//             case 'f':
//                 parseFace(parts, objData, arrays);
//                 break;
//             case 'usemtl':
//                 if (materials.hasOwnProperty(parts[1])) {
//                     materialInUse = materials[parts[1]];
//                 }
//                 break;
//         }
//     });

//     console.log("ATTRIBUTES:")
//     console.log(arrays);

//     console.log("OBJ DATA:")
//     console.log(objData);

//     return arrays;
// }

// /*
//  * Read the contents of an MTL file received as a string
//  * Return an object containing all the materials described inside,
//  * with their illumination attributes.
//  */
// function loadMtl(mtlString) {

//     let currentMtl = {};

//     let partInfo;
//     let lines = mtlString.split('\n');
//     lines.forEach(line => {
//         let parts = line.split(/\s+/);
//         switch (parts[0]) {
//             case 'newmtl':
//                 // Add a new entry into the object
//                 materials[parts[1]] = {};
//                 currentMtl = materials[parts[1]];
//                 break;
//             case 'Ns':  // Specular coefficient ("Shininess")
//                 currentMtl['Ns'] = Number(parts[1]);
//                 break;
//             case 'Kd':  // The specular color
//                 partInfo = parts.slice(1).filter(v => v != '').map(Number);
//                 currentMtl['Kd'] = partInfo;
//                 break;
//         }
//     });

//     return materials;
// }

// export { loadObj, loadMtl };

/*
 * OBJ + MTL Loader corregido y mejorado
 * Compatible con WebGL
 * Gilberto Echeverria + ajustes 2025
 */

"use strict";

// Materiales cargados
let materials = {};
let materialInUse = undefined;

/*
 * Triangulación en abanico para cualquier polígono
 */
function triangulateFace(faceVerts) {
  const triangles = [];
  for (let i = 1; i < faceVerts.length - 1; i++) {
    triangles.push([faceVerts[0], faceVerts[i], faceVerts[i + 1]]);
  }
  return triangles;
}

/*
 * Procesar una cara del archivo OBJ
 */
function parseFace(parts, objData, arrays) {
  // Crear arreglo con cada vértice de la cara
  const faceVerts = parts.slice(1).map((face) => {
    const fields = face.split("/");
    return [
      fields[0] ? Number(fields[0]) : undefined, // índice de vértice
      fields[1] ? Number(fields[1]) : undefined, // índice de textura
      fields[2] ? Number(fields[2]) : undefined, // índice de normal
    ];
  });

  // Triangulación (si la cara ya es triángulo, esto no la altera)
  const triangles = triangulateFace(faceVerts);

  triangles.forEach((tri) => {
    tri.forEach((v) => {
      const [vIdx, tIdx, nIdx] = v;

      // Vértice (obligatorio)
      if (vIdx !== undefined) {
        arrays.a_position.data.push(...objData.vertices[vIdx]);
      }

      // Coordenadas de textura
      if (tIdx !== undefined && objData.textures[tIdx]) {
        arrays.a_texCoord.data.push(...objData.textures[tIdx]);
      } else {
        arrays.a_texCoord.data.push(0, 0);
      }

      // Normales
      if (nIdx !== undefined && objData.normals[nIdx]) {
        arrays.a_normal.data.push(...objData.normals[nIdx]);
      } else {
        arrays.a_normal.data.push(0, 0, 0);
      }

      // Color del material
      if (materialInUse && materialInUse.Kd) {
        arrays.a_color.data.push(...materialInUse.Kd, 1);
      } else {
        arrays.a_color.data.push(0.4, 0.4, 0.4, 1);
      }

      objData.faces.push({ v: vIdx, t: tIdx, n: nIdx });
    });
  });
}

/*
 * Cargar archivo OBJ
 */
function loadObj(objString) {
  let objData = {
    vertices: [[0, 0, 0]],
    normals: [[0, 0, 0]],
    textures: [[0, 0]], // OBJ usa 2 componentes (u, v)
    faces: [],
  };

  let arrays = {
    a_position: { numComponents: 3, data: [] },
    a_color: { numComponents: 4, data: [] },
    a_normal: { numComponents: 3, data: [] },
    a_texCoord: { numComponents: 2, data: [] },
  };

  let lines = objString.split("\n");

  lines.forEach((line) => {
    line = line.trim();
    if (line === "" || line.startsWith("#")) return; // ignorar

    let parts = line.split(/\s+/);

    switch (parts[0]) {
      case "v":
        objData.vertices.push(parts.slice(1).map(Number));
        break;

      case "vn":
        objData.normals.push(parts.slice(1).map(Number));
        break;

      case "vt":
        objData.textures.push(parts.slice(1, 3).map(Number)); // solo u,v
        break;

      case "f":
        parseFace(parts, objData, arrays);
        break;

      case "usemtl":
        materialInUse = materials[parts[1]] || undefined;
        break;

      case "mtllib":
        console.warn(
          "OBJ: mtllib encontrado. Debes cargar el MTL manualmente antes."
        );
        break;
    }
  });

  return arrays;
}

/*
 * Cargar archivo MTL
 */
function loadMtl(mtlString) {
  let currentMtl = null;

  let lines = mtlString.split("\n");
  lines.forEach((line) => {
    line = line.trim();
    if (line === "" || line.startsWith("#")) return;

    let parts = line.split(/\s+/);

    switch (parts[0]) {
      case "newmtl":
        currentMtl = {};
        materials[parts[1]] = currentMtl;
        break;

      case "Ka":
      case "Kd":
      case "Ks":
      case "Ke":
        currentMtl[parts[0]] = parts.slice(1).map(Number);
        break;

      case "Ns":
      case "Ni":
      case "d":
      case "Tr":
      case "illum":
        currentMtl[parts[0]] = Number(parts[1]);
        break;

      case "map_Kd":
        currentMtl["map_Kd"] = parts[1];
        break;
    }
  });

  return materials;
}

export { loadObj, loadMtl };
