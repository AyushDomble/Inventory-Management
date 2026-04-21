import sys
from utils.helpers import load_data
from graph.graph_builder import Graph
from algorithms.dijkstra import dijkstra
from algorithms.greedy import greedy_allocation
from algorithms.knapsack import adjust_capacity
from utils.helpers import compute_total_cost
from utils.evaluation import evaluate_solution
from algorithms.tabu_search import tabu_search
from algorithms.tsp_dp import compute_tsp_for_all_warehouses



def print_evaluation(label, cities, warehouses, allocation,
                     shipping_cost_matrix):
    """Reusable helper — prints full evaluation block for any allocation."""
    total_cost, warehouse_utilization, demand_ok, demand_details, cap_violations = \
        evaluate_solution(cities, warehouses, allocation, shipping_cost_matrix)

    print(f"\nTotal Shipping Cost: {total_cost}")

    print("\nWarehouse Utilization")
    for w, data in warehouse_utilization.items():
        flag = "  *** OVER CAPACITY ***" if data["over_capacity"] else ""
        print(
            f"  {w} → Used: {data['used']} / {data['capacity']} "
            f"({data['utilization_percent']}%){flag}"
        )

    # BUG FIX: evaluate_solution now returns per-city demand details and capacity
    # violations. main.py previously showed only a single "All satisfied" line
    # which masked both under- and over-allocation issues.
    print("\nDemand Satisfaction")
    if demand_ok and not cap_violations:
        print("  All city demands satisfied, all capacity constraints met.")
    else:
        if not demand_ok:
            for city_name, d in demand_details.items():
                if not d["satisfied"]:
                    status = "OVER-ALLOCATED" if d["over_allocated"] else "UNDER-ALLOCATED"
                    print(
                        f"  {city_name}: demand={d['demand']}, "
                        f"allocated={d['allocated']}  [{status}]"
                    )
        if cap_violations:
            print("\nCapacity Violations Detected:")
            for v in cap_violations:
                print(f"  {v}")

    return total_cost


def main():

    print("\n" + "="*50)
    print("E-COMMERCE INVENTORY PLACEMENT OPTIMIZATION SYSTEM")
    print("="*50)

    cities, warehouses, roads = load_data("data/sample_data.json")

    print("\n" + "="*40)
    print("INPUT DATA LOADED")
    print("="*40)

    print("\nCities:")
    for city in cities:
        print(f"  {city.name} (Demand: {city.demand})")

    print("\nWarehouses:")
    for wh in warehouses:
        print(f"  {wh.name} (Capacity: {wh.capacity})")

    print("\nRoad Network:")
    for r in roads:
        print(f"  {r[0]} → {r[1]} : {r[2]}")

    total_demand   = sum(city.demand for city in cities)
    total_capacity = sum(w.capacity for w in warehouses)

    print("\n" + "="*40)
    print("FEASIBILITY CHECK")
    print("="*40)
    print(f"Total Demand:             {total_demand}")
    print(f"Total Warehouse Capacity: {total_capacity}")
    if total_demand > total_capacity:
        shortfall = total_demand - total_capacity
        print(
        f"\nERROR: Dataset is INFEASIBLE.\n"
        f"Demand exceeds total warehouse capacity by {shortfall} units.\n"
        f"Optimization cannot proceed."
    )
        return

    # if total_demand > total_capacity:
    #     shortfall = total_demand - total_capacity
    #     print(f"WARNING: Demand exceeds capacity by {shortfall} units. "
    #           f"Some demand CANNOT be satisfied — results will be partial.")
    
    
    else:
        print(f"Capacity surplus: {total_capacity - total_demand} units available.")

    # BUILD GRAPH
    graph = Graph()
    for src, dest, dist in roads:
        graph.add_edge(src, dest, dist)

    print("\n" + "="*40)
    print("TRANSPORTATION GRAPH")
    print("="*40)
    graph.display()

    # DIJKSTRA
    print("\n" + "="*40)
    print("DIJKSTRA SHORTEST PATH RESULTS")
    print("="*40)

    shipping_cost_matrix = {}
    unreachable = []

    for city in cities:
        distances = dijkstra(graph, city.name)
        shipping_cost_matrix[city.name] = {}

        for warehouse in warehouses:
            cost = distances.get(warehouse.name, float('inf'))
            shipping_cost_matrix[city.name][warehouse.name] = cost
            print(f"  {city.name} → {warehouse.name} : {cost}")

            if cost == float('inf'):
                unreachable.append((city.name, warehouse.name))

    # BUG FIX: unreachable city-warehouse pairs were silently stored as inf
    # and later caused incorrect cost calculations (inf * units = inf total cost).
    # Now we warn explicitly so the dataset can be corrected.
    if unreachable:
        print("\nWARNING: The following city→warehouse pairs are UNREACHABLE "
              "(no path in road network):")
        for city_name, wh_name in unreachable:
            print(f"  {city_name} → {wh_name}")

    print("\n" + "="*40)
    print("SHIPPING COST MATRIX (TABLE FORMAT)")
    print("="*40)
    
    # Header row
    header = ["City/Warehouse"] + [w.name for w in warehouses]
    print("{:<15}".format(header[0]), end="")
    
    for h in header[1:]:
        print("{:<15}".format(h), end="")
    print()
    
    # Rows
    for city in cities:
        print("{:<15}".format(city.name), end="")
        
        for warehouse in warehouses:
            cost = shipping_cost_matrix[city.name][warehouse.name]
            
            # Handle infinite cost
            if cost == float('inf'):
                cost = "inf"
            
            print("{:<15}".format(cost), end="")
        
        print()

    # GREEDY ALLOCATION
    print("\n" + "="*40)
    print("GREEDY ALLOCATION RESULTS")
    print("="*40)
    allocation = greedy_allocation(cities, warehouses, shipping_cost_matrix)
    for city in allocation:
        print(f"  {city} → {allocation[city]}")

    # KNAPSACK ADJUSTMENT
    print("\n" + "="*40)
    print("FRACTIONAL KNAPSACK ADJUSTMENT")
    print("="*40)
    allocation, warehouse_usage = adjust_capacity(
        cities, warehouses, allocation, shipping_cost_matrix
    )

    print("\nUPDATED ALLOCATION AFTER SPLITTING")
    for city in allocation:
        print(f"  {city} → {allocation[city]}")

    print("\nFINAL WAREHOUSE USAGE")
    for warehouse in warehouses:
        used     = warehouse_usage[warehouse.name]
        capacity = warehouse.capacity
        flag     = "  *** OVER CAPACITY ***" if used > capacity else ""
        print(f"  {warehouse.name} → Used: {used} / Capacity: {capacity}{flag}")

    # EVALUATE BEFORE TABU
    print("\n" + "="*40)
    print("SOLUTION EVALUATION (pre-optimisation)")
    print("="*40)
    cost_before = print_evaluation(
        "pre-tabu", cities, warehouses, allocation, shipping_cost_matrix
    )

    # TABU SEARCH
    print("\n" + "="*40)
    print("TABU SEARCH OPTIMIZATION")
    print("="*40)
    optimized_allocation = tabu_search(
        cities, warehouses, allocation, shipping_cost_matrix
    )

    # EVALUATE AFTER TABU
    print("\n" + "="*40)
    print("SOLUTION EVALUATION (post-optimisation)")
    print("="*40)
    cost_after = print_evaluation(
        "post-tabu", cities, warehouses, optimized_allocation, shipping_cost_matrix
    )

    improvement = cost_before - cost_after
    pct         = round((improvement / cost_before) * 100, 2) if cost_before else 0
    print(f"\nImprovement from Tabu Search: {improvement} units cost "
          f"({pct}% reduction)")

    print("\nFINAL OPTIMIZED ALLOCATION")
    for city in optimized_allocation:
        print(f"  {city} → {optimized_allocation[city]}")


    # ── TSP DELIVERY ROUTE PLANNING (Held-Karp DP) ───────────────────────────
    print("\n" + "="*50)
    print("DELIVERY ROUTE PLANNING — TRAVELLING SALESMAN PROBLEM")
    print("(Held-Karp Exact Dynamic Programming Algorithm)")
    print("="*50)
 
    print("\nAlgorithm  : Held-Karp Bitmask DP")
    print("Objective  : Minimum-cost round-trip from each warehouse")
    print("             visiting every assigned city exactly once.")
 
    tsp_results = compute_tsp_for_all_warehouses(
        optimized_allocation, warehouses, graph
    )
 
    total_delivery_cost = 0
 
    for warehouse in warehouses:
        wh_name = warehouse.name
        cost, route = tsp_results[wh_name]
 
        print(f"\n{'─'*40}")
        print(f"Warehouse : {wh_name}")
 
        if len(route) <= 1:
            print("  No cities assigned — no delivery route needed.")
            continue
 
        num_cities = len(route) - 2       # exclude depot at start and end
        print(f"Cities served : {num_cities}")
 
        # Show units per stop (including split cities that also appear elsewhere)
        print("Delivery stops (units):")
        for city_name in route[1:-1]:                 # skip first/last depot
            units = optimized_allocation[city_name][wh_name]
            total_alloc = sum(optimized_allocation[city_name].values())
            split_note = ""
            if len(optimized_allocation[city_name]) > 1:
                split_note = f"  ← split city (total demand {total_alloc})"
            print(f"    {city_name}: {units} units{split_note}")
 
        route_str = " → ".join(route)
        print(f"Optimal route : {route_str}")
        print(f"Total distance: {cost}")
        total_delivery_cost += cost
 
    print(f"\n{'='*50}")
    print(f"TOTAL DELIVERY DISTANCE (all warehouses): {total_delivery_cost}")
    print("="*50)
 
 
if __name__ == "__main__":
    main()