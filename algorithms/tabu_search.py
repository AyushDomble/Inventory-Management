import copy
import random
from utils.helpers import compute_total_cost, compute_warehouse_usage


def tabu_search(
    cities,
    warehouses,
    allocation,
    shipping_cost_matrix,
    iterations=50,
    tabu_tenure=None,           # BUG FIX 1: was random.randint(7,15) evaluated ONCE at import
    unit_options=(5, 10, 20),
    max_candidates=120,
    max_moves_sample=800,
    diversification_threshold=10
):



    # BUG FIX 1: tabu_tenure default arg was evaluated once at module import,
    # so every run in the same session used the same random value.
    if tabu_tenure is None:
        tabu_tenure = random.randint(7, 15)
        print(f"Tabu tenure set to: {tabu_tenure}")

    current_solution = copy.deepcopy(allocation)
    best_solution    = copy.deepcopy(allocation)
    best_cost        = compute_total_cost(best_solution, shipping_cost_matrix)

    tabu_list          = {}
    warehouse_capacity = {w.name: w.capacity for w in warehouses}
    city_list          = [c.name for c in cities]
    no_improve_count   = 0

    for iteration in range(iterations):

        print(f"\nIteration {iteration + 1}")

        # BUG FIX 2: warehouse_usage recomputed each iteration from current_solution.
        # Previously the capacity checks in move generation could use stale data.
        warehouse_usage = compute_warehouse_usage(current_solution)

        candidate_moves = []

        # TRANSFER MOVES
        for city in cities:
            city_name = city.name
            if city_name not in current_solution:
                continue
            for src in list(current_solution[city_name]):
                available_units = current_solution[city_name][src]
                for dst in shipping_cost_matrix[city_name]:
                    if dst == src:
                        continue
                    if shipping_cost_matrix[city_name][dst] == float("inf"):
                        continue
                    for units in unit_options:
                        if units > available_units:
                            continue
                        if warehouse_usage.get(dst, 0) + units > warehouse_capacity[dst]:
                            continue
                        candidate_moves.append(("transfer", city_name, src, dst, units))

        # SWAP MOVES
        for i in range(len(city_list)):
            for j in range(i + 1, len(city_list)):
                cityA = city_list[i]
                cityB = city_list[j]
                if cityA not in current_solution or cityB not in current_solution:
                    continue
                for wa in list(current_solution[cityA]):
                    for wb in list(current_solution[cityB]):
                        if wa == wb:
                            continue
                        if shipping_cost_matrix[cityA][wb] == float("inf"):
                            continue
                        if shipping_cost_matrix[cityB][wa] == float("inf"):
                            continue
                        unitsA = current_solution[cityA][wa]
                        unitsB = current_solution[cityB][wb]
                        for units in unit_options:
                            if units > unitsA or units > unitsB:
                                continue
                            # BUG FIX 3: swap moves never validated capacity.
                            # After a swap, wa loses unitsA and gains units (from B),
                            # wb loses unitsB and gains units (from A).
                            if (warehouse_usage.get(wb, 0) - unitsB + units) > warehouse_capacity[wb]:
                                continue
                            if (warehouse_usage.get(wa, 0) - unitsA + units) > warehouse_capacity[wa]:
                                continue
                            candidate_moves.append(("swap", cityA, wa, cityB, wb, units))

        # CHAIN MOVES
        for i in range(len(city_list)):
            for j in range(len(city_list)):
                for k in range(len(city_list)):
                    if i == j or j == k or i == k:
                        continue
                    cityA = city_list[i]
                    cityB = city_list[j]
                    cityC = city_list[k]
                    if (cityA not in current_solution
                            or cityB not in current_solution
                            or cityC not in current_solution):
                        continue
                    for wa in list(current_solution[cityA]):
                        for wb in list(current_solution[cityB]):
                            for wc in list(current_solution[cityC]):
                                if len({wa, wb, wc}) < 3:
                                    continue
                                if shipping_cost_matrix[cityA][wb] == float("inf"):
                                    continue
                                if shipping_cost_matrix[cityB][wc] == float("inf"):
                                    continue
                                if shipping_cost_matrix[cityC][wa] == float("inf"):
                                    continue
                                unitsA = current_solution[cityA][wa]
                                unitsB = current_solution[cityB][wb]
                                unitsC = current_solution[cityC][wc]
                                for units in unit_options:
                                    if units > unitsA or units > unitsB or units > unitsC:
                                        continue
                                    candidate_moves.append((
                                        "chain",
                                        cityA, wa, cityB, wb, cityC, wc, units,
                                    ))

        print(f"Generated {len(candidate_moves)} raw moves")

        if len(candidate_moves) > max_moves_sample:
            candidate_moves = random.sample(candidate_moves, max_moves_sample)

        # CANDIDATE FILTERING
        # BUG FIX 4: old code kept ONLY the top-N cheapest moves (pure exploitation).
        # This blocked all uphill moves, preventing escape from local optima.
        # Fix: 80% best by delta (exploit) + 20% random from remainder (explore).
        scored_moves = []
        for move in candidate_moves:
            if move[0] == "transfer":
                _, city, src, dst, units = move
                delta = (shipping_cost_matrix[city][dst] - shipping_cost_matrix[city][src]) * units
            elif move[0] == "swap":
                _, cityA, wa, cityB, wb, units = move
                delta = (
                    (shipping_cost_matrix[cityA][wb] - shipping_cost_matrix[cityA][wa])
                    + (shipping_cost_matrix[cityB][wa] - shipping_cost_matrix[cityB][wb])
                ) * units
            else:
                _, cityA, wa, cityB, wb, cityC, wc, units = move
                delta = (
                    (shipping_cost_matrix[cityA][wb] - shipping_cost_matrix[cityA][wa])
                    + (shipping_cost_matrix[cityB][wc] - shipping_cost_matrix[cityB][wb])
                    + (shipping_cost_matrix[cityC][wa] - shipping_cost_matrix[cityC][wc])
                ) * units
            scored_moves.append((delta, move))

        scored_moves.sort(key=lambda x: x[0])

        exploit_count = int(max_candidates * 0.8)
        explore_count = max_candidates - exploit_count
        top_moves     = [m for _, m in scored_moves[:exploit_count]]
        rest_moves    = [m for _, m in scored_moves[exploit_count:]]
        random_sample = random.sample(rest_moves, min(explore_count, len(rest_moves)))
        candidate_moves = top_moves + random_sample

        print(f"Evaluating {len(candidate_moves)} filtered moves "
              f"({exploit_count} exploit + {len(random_sample)} explore)")

        # EVALUATE MOVES
        best_neighbor      = None
        best_neighbor_cost = float("inf")
        best_move          = None

        for move in candidate_moves:
            is_tabu = move in tabu_list and tabu_list[move] > iteration

            new_solution = copy.deepcopy(current_solution)

            if move[0] == "transfer":
                _, city, src, dst, units = move
                new_solution[city][src] -= units
                if new_solution[city][src] == 0:
                    del new_solution[city][src]
                new_solution[city][dst] = new_solution[city].get(dst, 0) + units

            elif move[0] == "swap":
                _, cityA, wa, cityB, wb, units = move
                new_solution[cityA][wa] -= units
                new_solution[cityB][wb] -= units
                if new_solution[cityA][wa] == 0:
                    del new_solution[cityA][wa]
                if new_solution[cityB][wb] == 0:
                    del new_solution[cityB][wb]
                new_solution[cityA][wb] = new_solution[cityA].get(wb, 0) + units
                new_solution[cityB][wa] = new_solution[cityB].get(wa, 0) + units

            elif move[0] == "chain":
                _, cityA, wa, cityB, wb, cityC, wc, units = move
                new_solution[cityA][wa] -= units
                new_solution[cityB][wb] -= units
                new_solution[cityC][wc] -= units
                if new_solution[cityA][wa] == 0:
                    del new_solution[cityA][wa]
                if new_solution[cityB][wb] == 0:
                    del new_solution[cityB][wb]
                if new_solution[cityC][wc] == 0:
                    del new_solution[cityC][wc]
                new_solution[cityA][wb] = new_solution[cityA].get(wb, 0) + units
                new_solution[cityB][wc] = new_solution[cityB].get(wc, 0) + units
                new_solution[cityC][wa] = new_solution[cityC].get(wa, 0) + units

            cost = compute_total_cost(new_solution, shipping_cost_matrix)

            if is_tabu and cost >= best_cost:
                continue

            if cost < best_neighbor_cost:
                best_neighbor_cost = cost
                best_neighbor      = new_solution
                best_move          = move

        # APPLY BEST MOVE
        if best_neighbor is None:
            print("No feasible move found")
            break

        current_solution = best_neighbor

        # BUG FIX 5: tabu_list grew unboundedly — expired entries were never pruned.
        tabu_list = {m: exp for m, exp in tabu_list.items() if exp > iteration}
        tabu_list[best_move] = iteration + tabu_tenure

        print(f"Applied Move: {best_move}")
        print(f"New Cost: {best_neighbor_cost}")

        if best_neighbor_cost < best_cost:
            best_cost        = best_neighbor_cost
            best_solution    = copy.deepcopy(best_neighbor)
            no_improve_count = 0
            print("New BEST cost:", best_cost)
        else:
            no_improve_count += 1

        # BUG FIX 6: no diversification existed — search stayed trapped in local optima.
        # Restart from best + small random perturbation after N stagnant iterations.
        if no_improve_count >= diversification_threshold:
            print(f"\n[Diversification] Stuck for {diversification_threshold} iterations "
                  f"— restarting from best with perturbation")
            current_solution = copy.deepcopy(best_solution)
            no_improve_count = 0

            wh_cap = {w.name: w.capacity for w in warehouses}
            usage  = compute_warehouse_usage(current_solution)
            moves_done = 0

            for city in cities:
                if moves_done >= 3:
                    break
                city_name = city.name
                if city_name not in current_solution:
                    continue
                warehouses_used = list(current_solution[city_name].keys())
                all_wh   = list(shipping_cost_matrix[city_name].keys())
                not_used = [w for w in all_wh
                            if w not in warehouses_used
                            and shipping_cost_matrix[city_name][w] != float("inf")]
                if not not_used:
                    continue
                src   = random.choice(warehouses_used)
                dst   = random.choice(not_used)
                avail = current_solution[city_name][src]
                room  = wh_cap[dst] - usage.get(dst, 0)
                units = min(10, avail, room)
                if units <= 0:
                    continue
                current_solution[city_name][src] -= units
                if current_solution[city_name][src] == 0:
                    del current_solution[city_name][src]
                current_solution[city_name][dst] = \
                    current_solution[city_name].get(dst, 0) + units
                usage[src] -= units
                usage[dst]  = usage.get(dst, 0) + units
                moves_done += 1

    print("\nFinal Best Cost:", best_cost)
    return best_solution