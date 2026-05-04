![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135%2B-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-19%2B-61DAFB?style=for-the-badge&logo=react)
![Vite](https://img.shields.io/badge/Vite-8.0%2B-646CFF?style=for-the-badge&logo=vite)
![Dijkstra](https://img.shields.io/badge/Algorithm-Dijkstra-orange?style=for-the-badge)
![Tabu Search](https://img.shields.io/badge/Algorithm-Tabu%20Search-red?style=for-the-badge)
![TSP DP](https://img.shields.io/badge/Algorithm-TSP%20%7C%20DP-purple?style=for-the-badge)
![Knapsack](https://img.shields.io/badge/Algorithm-Knapsack-yellow?style=for-the-badge)
![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)

---

# 📦 E-Commerce Inventory Placement Optimization System

A full-stack *algorithmic optimization platform* built with *Python* and *React* to solve the warehouse inventory placement problem for e-commerce logistics. The system computes shortest delivery paths, allocates demand to warehouses, and benchmarks multiple optimization strategies — all through an interactive browser-based dashboard.

---

## ✨ Key Features

### 🗺️ Graph-Based Road Network
- *City & Warehouse Modelling:* Define cities with demand, warehouses with capacity, and road connections with distances.
- *Shortest Path Engine:* Dijkstra's algorithm computes the minimum-cost shipping path between any two nodes in the network.
- *Adjacency-List Graph:* Lightweight, directed graph data structure with fast neighbor lookups.

### 🤖 Multi-Algorithm Optimization
- *Greedy Allocation:* Rapid, heuristic-first inventory assignment that minimises immediate shipping cost at each step.
- *Knapsack Capacity Adjustment:* Dynamic programming-based rebalancing when warehouse utilisation violates capacity constraints.
- *Tabu Search:* Metaheuristic optimisation with short-term memory to escape local optima and refine allocations iteratively.
- *TSP with Dynamic Programming:* Computes optimal visitation order for all warehouses, providing a lower-bound tour cost per warehouse.

### 📊 Evaluation & Metrics
- *Total Shipping Cost:* Aggregate cost across all city-to-warehouse assignments.
- *Warehouse Utilisation:* Per-warehouse used vs. capacity, with over-capacity flagging.
- *Demand Satisfaction Audit:* Detects and reports under-allocated and over-allocated cities individually.
- *Algorithm Benchmarking:* Side-by-side comparison of Greedy, Tabu Search, and Knapsack strategies.

### 🖥️ Interactive React Dashboard
- *XLSX Import/Export:* Upload city, warehouse, and road data from Excel; export results as .xlsx.
- *Sample Data Loader:* Preloaded 20-city, 6-warehouse India logistics scenario for instant demos.
- *Live API Integration:* React frontend communicates with a FastAPI backend at localhost:8000.
- *Responsive Dark UI:* Custom design system with amber/teal accent palette, Syne + DM Sans typography, and Recharts visualisations.

---

## 📸 Dashboard Preview  

<p align="center">
  <a href="gui\preview\image01.png"><img src="gui\preview\image01.png" width="260"></a>
  <a href="gui\preview\image02.png"><img src="gui\preview\image02.png" width="260"></a>
  <a href="gui\preview\image03.png"><img src="gui\preview\image03.png" width="260"></a>
  <a href="gui\preview\image04.png"><img src="gui\preview\image04.png" width="260"></a> 
  <a href="gui\preview\image05.png"><img src="gui\preview\image05.png" width="260"></a>
  <a href="gui\preview\image06.png"><img src="gui\preview\image06.png" width="260"></a>
</p>

---

## 📂 Project Structure

```plaintext
inventory_placement_optimization/
├── 📂 algorithms/
│   ├── ⚡ dijkstra.py
│   ├── 🎯 greedy.py
│   ├── 🎒 knapsack.py
│   ├── 🔄 tabu_search.py
│   └── 🧠 tsp_dp.py
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── ⚛️ App.jsx
│   │   ├── 🚀 main.jsx
│   │   └── 🎨 index.css
│   ├── 📦 package.json
│   └── ⚙️ vite.config.js
├── 📂 graph/
│   └── 🕸️ graph_builder.py
├── 📂 gui/
│   └── 🖥️ dashboard.py
├── 📂 models/
│   ├── 🏙️ city.py
│   └── 🏭 warehouse.py
├── 📂 utils/
│   ├── 📊 evaluation.py
│   └── 🛠️ helpers.py
├── 🌐 api.py
├── 🎮 main.py
└── 📂 data/
    └── 💾 sample_data.json
```
---

## 🛠️ Tech Stack

*Backend / Core:*
- Language: Python 3.8+
- Web Framework: FastAPI + Uvicorn
- Graph Engine: Custom adjacency-list implementation
- Optimisation: Greedy, Knapsack DP, Tabu Search, TSP DP

*Frontend:*
- UI Framework: React 19 (Vite)
- Charts: Recharts
- Spreadsheet I/O: SheetJS (xlsx)

*Data:*
- Input format: JSON (CLI) / XLSX (web dashboard)

---

## ⚙️ How to Run Locally

*Clone the repository*
bash
git clone https://github.com/your-username/inventory-placement-optimization.git
cd inventory-placement-optimization


*Set up Python environment*
bash
python -m venv myenv
source myenv/bin/activate        # On Windows: myenv\Scripts\activate
pip install fastapi uvicorn


*Start the FastAPI backend*
bash
uvicorn api:app --reload --port 8000


*Run the CLI pipeline* (optional, no frontend required)
bash
python main.py


*Launch the React dashboard*
bash
cd frontend
npm install
npm run dev


Open http://localhost:5173 in your browser.

---

## 🚀 Usage Guide

1. *Load Data* — Click Load Sample for the built-in India scenario, or import your own .xlsx file with Cities, Warehouses, and Roads sheets.
2. *Configure* — Add or edit rows in the editable tables for cities (name, demand), warehouses (name, capacity), and roads (from, to, distance).
3. *Optimise* — Hit Run Optimization to send data to the backend. Results include shortest paths, allocations, and per-algorithm cost comparisons.
4. *Export* — Download the full solution as .xlsx for reporting.

---

## 📊 Algorithms Overview

| Algorithm | Type | Strength |
|---|---|---|
| Dijkstra | Graph shortest path | Exact minimum-cost routes |
| Greedy Allocation | Heuristic | Fast initial solution |
| Knapsack DP | Dynamic programming | Capacity constraint repair |
| Tabu Search | Metaheuristic | Escapes local optima |
| TSP + DP | Combinatorial exact | Optimal warehouse tour ordering |

---

## 📄 License
This project is licensed under the *MIT License*.  
See the [LICENSE](LICENSE) file for details.