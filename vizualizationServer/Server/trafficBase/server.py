from traffic_base.agent import *
from traffic_base.model import CityModel

from mesa.visualization import (
    Slider, 
    SolaraViz, 
    make_plot_component,
    make_space_component,
    SpaceRenderer)
from mesa.visualization.components import AgentPortrayalStyle

COLORS = {
    "Active_cars": "blue", 
    #"Arrived_per_step": "green", 
    "Total_arrived": "red",
    #"Total_spawned": "purple"
}
#"Average_moves": lambda m: self.aver

def agent_portrayal(agent):

    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        marker="s",
    )

    if isinstance(agent, Road):
        portrayal.color = "#aaa"

    if isinstance(agent, Destination):
        portrayal.color = "lightgreen"

    if isinstance(agent, Traffic_Light):
        portrayal.color = "red" if not agent.state else "green"

    if isinstance(agent, Obstacle):
        portrayal.color = "#555"

    return portrayal

def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Step")
    ax.set_ylabel("Count")

model = CityModel()

renderer = SpaceRenderer(
    model,
    backend="matplotlib",
)
renderer.draw_agents(agent_portrayal)
renderer.post_process = post_process_space

space_component = make_space_component(
    agent_portrayal,
    draw_grid=False,
)

# Se vinculan los mismos colores de los agentes en la visualización del plot
lineplot_component = make_plot_component(
    COLORS,
    post_process=post_process_lines,
)

model_params = {
    "N": Slider("Maximum agents", 5000, 1000, 10000),
    "spawn_time": Slider("Spawn Time", 10, 1, 20),
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
}

page = SolaraViz(
    model,
    renderer,
    components=[lineplot_component],
    model_params=model_params,
    name="City Model",
)

# grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

# server = ModularServer(CityModel, [grid], "Traffic Base", model_params)
                       
# server.port = 8522 # The default
# server.launch()