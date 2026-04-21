def adjust_capacity(cities, warehouses, allocation, shipping_cost_matrix):

    warehouse_usage    = {w.name: 0 for w in warehouses}
    warehouse_capacity = {w.name: w.capacity for w in warehouses}

    for city in allocation:
        for w, units in allocation[city].items():
            warehouse_usage[w] += units

    # BUG FIX 1: The original loop processed warehouses in list order.
    # If W1 overflows into W2, and W2 already overflows, W2's overflow is
    # handled later — but the units just moved from W1 are not re-evaluated
    # as candidates for moving again. This caused "Cannot resolve overflow"
    # warnings even when a valid multi-hop path existed.
    # Fix: repeat passes over all warehouses until no overflow remains.

    max_passes   = len(warehouses) * 2   # safety ceiling to avoid infinite loops
    changed      = True
    passes       = 0
    knapsack_log = []

    while changed and passes < max_passes:
        changed = False
        passes += 1

        for warehouse in warehouses:
            w_name = warehouse.name

            while warehouse_usage[w_name] > warehouse_capacity[w_name]:
                changed  = True
                overflow = warehouse_usage[w_name] - warehouse_capacity[w_name]

                print(f"\nOverflow detected at {w_name}: {overflow} units")

                best_move    = None
                best_penalty = float("inf")

                for city in cities:
                    city_name  = city.name
                    city_alloc = allocation[city_name]

                    if w_name not in city_alloc:
                        continue

                    movable_units = city_alloc[w_name]
                    current_cost  = shipping_cost_matrix[city_name][w_name]
                    costs         = shipping_cost_matrix[city_name]

                    for alt in costs:
                        if alt == w_name:
                            continue
                        alt_cost = costs[alt]
                        if alt_cost == float("inf"):
                            continue

                        remaining_capacity = (
                            warehouse_capacity[alt] - warehouse_usage[alt]
                        )
                        if remaining_capacity <= 0:
                            continue

                        penalty = alt_cost - current_cost

                        if penalty < best_penalty:
                            best_penalty = penalty
                            best_move = {
                                "city": city_name,
                                "from": w_name,
                                "to":   alt,
                                "movable_units":      movable_units,
                                "remaining_capacity": remaining_capacity,
                            }
                        elif penalty == best_penalty and best_move is not None:
                            if movable_units < best_move["movable_units"]:
                                best_move = {
                                    "city": city_name,
                                    "from": w_name,
                                    "to":   alt,
                                    "movable_units":      movable_units,
                                    "remaining_capacity": remaining_capacity,
                                }

                if best_move is None:
                    # BUG FIX 2: original code printed WARNING and silently continued,
                    # leaving the allocation in an over-capacity state with no indication
                    # of which cities are unresolved.
                    print(f"ERROR: Cannot resolve overflow at {w_name} "
                          f"— {overflow} units unplaceable. "
                          f"Total demand likely exceeds total capacity.")
                    break

                city_name          = best_move["city"]
                src                = best_move["from"]
                dst                = best_move["to"]
                movable_units      = best_move["movable_units"]
                remaining_capacity = best_move["remaining_capacity"]

                move_units = min(movable_units, overflow, remaining_capacity)

                print(
                    f"Moving {move_units} units of {city_name} "
                    f"from {src} → {dst} "
                    f"(penalty per unit = {best_penalty})"
                )

                knapsack_log.append({"city": city_name, "from": src, "to": dst, "units": move_units, "penalty": best_penalty})

                allocation[city_name][src] -= move_units
                if allocation[city_name][src] == 0:
                    del allocation[city_name][src]
                allocation[city_name][dst] = (
                    allocation[city_name].get(dst, 0) + move_units
                )
                warehouse_usage[src] -= move_units
                warehouse_usage[dst] += move_units

    # BUG FIX 3: return value used warehouse_usage from the original single-pass loop.
    # Now we recompute from the final allocation so the returned usage is always
    # consistent with what's actually in the allocation dict.
    final_usage = {w.name: 0 for w in warehouses}
    for city in allocation:
        for w, units in allocation[city].items():
            final_usage[w] += units

    return allocation, final_usage, knapsack_log