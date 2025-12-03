
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
