# IA

Taxi fleet management simulation system for the city of Braga, developed for an Artificial Intelligence course. The project implements multiple search algorithms (informed and uninformed) for route optimization, considering factors such as time, operational cost, environmental impact, and traffic/weather conditions.

<p align="center">
  <img src="assets/simulation.png" width="900"/>
</p>

## Grade

**Final Grade:** 17 / 20 ⭐

## Authors

- *Gabriel Dantas* -> [@gabil88](https://github.com/gabil88)
- *José Fernandes* -> [@JoseLourencoFernandes](https://github.com/JoseLourencoFernandes)
- *Simão Oliveira* -> [@SimaoOliveira05](https://github.com/SimaoOliveira05)
- *Luis Ferreira* -> [@1Plus0NE](https://github.com/1Plus0NE)


## Features

- 🚕 **Fleet Simulation** - Management of multiple vehicles (electric, combustion, hybrid)
- 🗺️ **Search Algorithms** - A*, Greedy, BFS, DFS, Uniform Cost
- 🎯 **Multiple Heuristics** - Distance, time, cost, environmental, traffic
- ⛽ **Refueling System** - Automatic fuel/battery management
- 🌧️ **Dynamic Events** - Weather and traffic affecting travel times
- 📊 **Visualization** - Real-time simulation animation

## Requirements

- Python 3.10+
- matplotlib
- OSMnx (for OpenStreetMap data)

## Installation

```bash
# Clone the repository
git clone https://github.com/1Plus0NE/UberUM.git
cd UberUM

# Install dependencies
pip install matplotlib osmnx
```

## Running

```bash
cd src
python3 main.py
```

## Implemented Algorithms

| Algorithm | Type | Description |
|-----------|------|-------------|
| A* | Informed | Uses g(n) + h(n) to find optimal path |
| Greedy | Informed | Uses only h(n), faster but suboptimal |
| BFS | Uninformed | Breadth-first search |
| DFS | Uninformed | Depth-first search |
| Uniform Cost | Uninformed | Expands by lowest accumulated cost |

## Available Heuristics

- **Euclidean Distance** - Straight-line distance
- **Estimated Time** - Considers speed and events
- **Operational Cost** - Fuel/energy spent
- **Environmental Impact** - CO₂ emissions
- **Traffic Avoidance** - Penalizes congested zones
- **Combined** - Weighted average of all
