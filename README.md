# 🚗 Reto TC2008B 🚦

El reto de esta materia consiste en proponer una solución a un problema de movilidad al buscar reducir la congestión vehicular al simular de manera gráfica el tráfico, representando la salida de un sistema multi agentes.

## 👥 Team

- Miranda Urban Solano A01752391
- Katia Abigail Álvarez Contreras A01781097

## Video de la simulación

Link al video con la simulación funcional: https://youtu.be/BxmnKqYgP5I?si=ZGG-IiHtl6M8TeWL

# Simulación de Tráfico con Sistemas Multiagentes

Este proyecto propone una solución a un problema de movilidad urbana mediante la simulación del tráfico con un **modelo multiagente basado en Mesa**.  
La visualización combina:

- Un **backend en Flask** que expone los datos de la simulación.
- Un **servidor Solara** para análisis y visualización científica.
- Un **cliente WebGL con Vite** para representar la ciudad y los agentes.

---

## Componentes del sistema

El proyecto utiliza **tres servidores** que trabajan simultáneamente:

1. **Servidor Flask (traffic_server.py)**  
   Expone el modelo como API para la visualización WebGL.

2. **Servidor Solara (server.py)**  
   Permite visualizar el modelo en 2D y graficar métricas en tiempo real.

3. **Cliente WebGL con Vite**  
   Renderiza la ciudad y los agentes en un entorno 3D.

---

# Prerrequisitos

### ✔️ Python 3.11

### ✔️ Node.js + npm

### ✔️ Crear y activar ambiente virtual

````bash
python3.11 -m venv .agents
source .agents/bin/activate

## Instalar dependencias del modelo

```bash
pip install -U "mesa[all]"
pip install flask flask_cors

---


# Terminal 1 — Servidor Flask (Modelo + API WebGL)

**Ruta:**
`retoTC2008B/vizualizationServer/Server/trafficBase`

**Ejecutar:**

```bash
python3 traffic_server.py

### Este servidor:

- Inicializa el modelo `CityModel`.
- Ejecuta el método `step()` para avanzar la simulación.
- Expone información en formato JSON a través de endpoints como:
  - `/init` → Inicializa el modelo
  - `/update` → Avanza un paso
  - `/getCars` → Posiciones de autos
  - `/getObstacles` → Obstáculos
  - `/getRoad` → Calles
  - `/getTrafficLights` → Semáforos con estado
  - `/getDestinations` → Destinos

Toda esta información es consumida desde la visualización WebGL.

**Puerto de ejecución:**
`http://localhost:8585`

---

## Terminal 2 — Servidor Solara (Visualización científica Mesa)

**Ruta:**
`retoTC2008B/vizualizationServer/Server/trafficBase`

**Ejecutar:**

```bash
solara run server.py

### Este servidor provee una interfaz visual generada por Mesa y Solara:

- Muestra un **grid** del modelo.
- Dibuja agentes como:
  - carreteras
  - obstáculos
  - semáforos
  - destinos
  - autos
- Grafica métricas como:
  - **Active Cars**
  - **Arrived per step**
  - **Total Arrived**
  - **Total Spawned**
- Permite modificar parámetros desde sliders:
  - número máximo de agentes
  - `spawn time`
  - `seed` aleatoria

---

## Terminal 3 — Cliente WebGL con Vite (Visualización 3D)

**Ruta:**
`retoTC2008B/vizualizationServer`

**Ejecutar:**

```bash
npx vite
````

### Este servidor:

- Levanta la aplicación WebGL.
- Consume los endpoints del servidor Flask para obtener:
  - posiciones de autos
  - obstáculos
  - carreteras
  - semáforos
  - destinos
- Renderiza la ciudad en un entorno 3D utilizando WebGL.
- Actualiza la escena a medida que el servidor Flask avanza el modelo.

# Arquitectura del Sistema — Simulación de Tráfico TC2008B

Este documento describe la arquitectura general del sistema utilizado para la simulación de tráfico del proyecto TC2008B.  
El sistema está compuesto por **tres servidores principales** que trabajan de manera simultánea para generar, procesar y visualizar datos en tiempo real.

---

## Resumen de la arquitectura

La aplicación funciona mediante la interacción entre:

1. **Un modelo multiagente (Mesa) ejecutado por Flask**
2. **Una interfaz científica de análisis (Solara/Mesa Viz)**
3. **Una visualización 3D en WebGL servida por Vite**

Cada componente cumple un rol específico y se comunican entre sí para producir una visualización dinámica del tráfico.

---

# Diagrama General de Arquitectura

     ┌──────────────────────────┐
     │     Solara / Mesa Viz    │
     │     server.py            │
     │  (Visualización 2D y UI) │
     └──────────────▲───────────┘
                    │
                    │ (interacción directa con el modelo)
                    │
     ┌──────────────┴───────────┐
     │        CityModel          │
     │ (Simulación multiagente)  │
     └──────────────▲───────────┘
                    │
                    │ API REST (JSON)
                    │
     ┌──────────────┴───────────┐
     │ Flask Server              │
     │ traffic_server.py         │
     │ (Endpoints: /getCars,     │
     │  /update, /getRoad, etc.) │
     └──────────────▲───────────┘
                    │
                    │ HTTP GET requests
                    │
     ┌──────────────┴───────────┐
     │  WebGL Client + Vite      │
     │  (visualización 3D)       │
     └───────────────────────────┘
