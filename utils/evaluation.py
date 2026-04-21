def evaluate_solution(cities, warehouses, allocation, shipping_cost_matrix):

    total_cost      = 0
    warehouse_usage = {w.name: 0 for w in warehouses}
    demand_details  = {}   # BUG FIX: was a single bool; now per-city detail

    for city in cities:
        city_name       = city.name
        demand          = city.demand
        allocated_units = 0

        if city_name in allocation:
            for warehouse, units in allocation[city_name].items():
                cost_per_unit = shipping_cost_matrix[city_name][warehouse]
                total_cost   += units * cost_per_unit
                warehouse_usage[warehouse] += units
                allocated_units += units

        demand_details[city_name] = {
            "demand":    demand,
            "allocated": allocated_units,
            "satisfied": allocated_units == demand,
            # BUG FIX 1: original code only checked allocated == demand, so a city
            # that was over-allocated (e.g. 130 allocated for 95 demand) would
            # incorrectly show as unsatisfied rather than over-allocated.
            "over_allocated": allocated_units > demand,
        }

    # BUG FIX 2: capacity violations were not reported by evaluate_solution at all.
    # The function printed utilization% but never flagged warehouses exceeding 100%.
    warehouse_utilization = {}
    capacity_violations   = []

    for warehouse in warehouses:
        used     = warehouse_usage[warehouse.name]
        capacity = warehouse.capacity
        pct      = round((used / capacity) * 100, 2) if capacity > 0 else 0

        warehouse_utilization[warehouse.name] = {
            "used":                used,
            "capacity":            capacity,
            "utilization_percent": pct,
            "over_capacity":       used > capacity,   # NEW explicit flag
        }

        if used > capacity:
            capacity_violations.append(
                f"{warehouse.name}: {used}/{capacity} ({pct}%)"
            )

    all_satisfied = all(v["satisfied"] for v in demand_details.values())

    return total_cost, warehouse_utilization, all_satisfied, demand_details, capacity_violations