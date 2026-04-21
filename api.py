from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List

from models.city import City
from models.warehouse import Warehouse
from graph.graph_builder import Graph
from algorithms.dijkstra import dijkstra
from algorithms.greedy import greedy_allocation
from algorithms.knapsack import adjust_capacity
from algorithms.tabu_search import tabu_search
from algorithms.tsp_dp import compute_tsp_for_all_warehouses   # ← NEW
from utils.evaluation import evaluate_solution

# ─────────────────────────────────────────
#  App setup
# ─────────────────────────────────────────
app = FastAPI(title="Inventory Placement Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
#  Request models
# ─────────────────────────────────────────
class CityInput(BaseModel):
    name: str
    demand: int

class WarehouseInput(BaseModel):
    name: str
    capacity: int

class RoadInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: str = Field(alias="from")
    to: str
    distance: float

class OptimizeRequest(BaseModel):
    cities: List[CityInput]
    warehouses: List[WarehouseInput]
    roads: List[RoadInput]

# ─────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────
def build_cost_matrix(cities, warehouses, graph):
    matrix, unreachable = {}, []
    for city in cities:
        distances = dijkstra(graph, city.name)
        matrix[city.name] = {}
        for wh in warehouses:
            cost = distances.get(wh.name, float("inf"))
            matrix[city.name][wh.name] = cost
            if cost == float("inf"):
                unreachable.append({"city": city.name, "warehouse": wh.name})
    return matrix, unreachable

def serialize_alloc(alloc):
    return {city: {wh: int(u) for wh, u in wh_map.items()} for city, wh_map in alloc.items()}

def serialize_eval(eval_result):
    total_cost, wutil, all_satisfied, demand_details, cap_violations = eval_result
    return {
        "totalCost": total_cost if total_cost != float("inf") else -1,
        "allSatisfied": all_satisfied,
        "demandDetails": {
            city: {
                "demand":        int(d["demand"]),
                "allocated":     int(d["allocated"]),
                "satisfied":     bool(d["satisfied"]),
                "overAllocated": bool(d["over_allocated"]),
            }
            for city, d in demand_details.items()
        },
        "warehouseUtilization": {
            wh: {
                "used":           int(data["used"]),
                "capacity":       int(data["capacity"]),
                "utilizationPct": float(data["utilization_percent"]),
                "overCapacity":   bool(data["over_capacity"]),
            }
            for wh, data in wutil.items()
        },
        "capacityViolations": cap_violations,
    }

def serialize_tsp(tsp_results):
    """Convert TSP output to JSON-safe format."""
    out = {}
    for wh, (cost, route) in tsp_results.items():
        out[wh] = {
            "cost":       cost if cost != float("inf") else -1,
            "route":      route,
            "numStops":   len(route) - 2,   # exclude depot at start and end
        }
    return out

# ─────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Inventory Optimizer API is running"}


@app.post("/optimize")
def optimize(request: OptimizeRequest):
    # Parse inputs
    cities     = [City(c.name.strip(), c.demand)        for c in request.cities     if c.name.strip()]
    warehouses = [Warehouse(w.name.strip(), w.capacity)  for w in request.warehouses if w.name.strip()]
    roads      = [(r.from_.strip(), r.to.strip(), r.distance)
                  for r in request.roads if r.from_.strip() and r.to.strip()]

    if not cities or not warehouses:
        return {"error": "Must provide at least one city and one warehouse."}

    # Feasibility check
    total_demand   = sum(c.demand for c in cities)
    total_capacity = sum(w.capacity for w in warehouses)

    if total_capacity < total_demand:
        return {
            "feasible":      False,
            "totalDemand":   total_demand,
            "totalCapacity": total_capacity,
            "error": f"Infeasible: demand exceeds capacity by {total_demand - total_capacity} units.",
        }

    # Build graph
    graph = Graph()
    for src, dest, dist in roads:
        graph.add_edge(src, dest, dist)

    # Dijkstra cost matrix
    cost_matrix, unreachable = build_cost_matrix(cities, warehouses, graph)

    cost_matrix_json = {
        city: {wh: (c if c != float("inf") else None) for wh, c in wh_costs.items()}
        for city, wh_costs in cost_matrix.items()
    }

    # Greedy → Knapsack → Tabu
    greedy_alloc                    = greedy_allocation(cities, warehouses, cost_matrix)
    knapsack_alloc, warehouse_usage, knapsack_log = adjust_capacity(cities, warehouses, greedy_alloc, cost_matrix)
    pre_tabu_eval                   = serialize_eval(evaluate_solution(cities, warehouses, knapsack_alloc, cost_matrix))
    optimized_alloc                 = tabu_search(cities, warehouses, knapsack_alloc, cost_matrix)
    post_tabu_eval                  = serialize_eval(evaluate_solution(cities, warehouses, optimized_alloc, cost_matrix))

    # ── TSP delivery routes (NEW) ──────────────────────────────────────────
    tsp_raw     = compute_tsp_for_all_warehouses(optimized_alloc, warehouses, graph)
    tsp_results = serialize_tsp(tsp_raw)
    tsp_total   = sum(v["cost"] for v in tsp_results.values() if v["cost"] >= 0)

    # Cost improvement
    pre_cost        = pre_tabu_eval["totalCost"]
    post_cost       = post_tabu_eval["totalCost"]
    improvement     = pre_cost - post_cost
    improvement_pct = round((improvement / pre_cost) * 100, 2) if pre_cost > 0 else 0

    return {
        "feasible":            True,
        "totalDemand":         total_demand,
        "totalCapacity":       total_capacity,
        "surplus":             total_capacity - total_demand,
        "unreachablePairs":    unreachable,
        "costMatrix":          cost_matrix_json,
        "greedyAllocation":    serialize_alloc(greedy_alloc),
        "knapsackAllocation":  serialize_alloc(knapsack_alloc),
        "knapsackLog":         knapsack_log,
        "preTabuEval":         pre_tabu_eval,
        "optimizedAllocation": serialize_alloc(optimized_alloc),
        "postTabuEval":        post_tabu_eval,
        "improvement":         improvement,
        "improvementPct":      improvement_pct,
        "tspRoutes":           tsp_results,      # ← NEW
        "tspTotalCost":        tsp_total,         # ← NEW
    }