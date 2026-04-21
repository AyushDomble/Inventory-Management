"""
tsp_dp.py — Travelling Salesman Problem via Held-Karp Dynamic Programming

Algorithm: Held-Karp (Bitmask DP)
Time  Complexity : O(n^2 * 2^n)   — exact optimal for small n
Space Complexity : O(n * 2^n)

How it fits into the pipeline
──────────────────────────────
After the final inventory allocation each warehouse has a set of
assigned cities.  TSP finds the minimum-cost delivery round-trip:

    Warehouse → city_1 → city_2 → ... → city_k → Warehouse

The "cost" between any two stops is the Dijkstra shortest-path
distance already computed and stored in the full distance matrix
(dist_between_stops[a][b]).

Public API
──────────
    solve_tsp_dp(warehouse_name, city_names, dist_matrix)
        → (optimal_cost, ordered_route_list)

    compute_tsp_for_all_warehouses(optimized_allocation, warehouses,
                                   cities, graph)
        → dict  { warehouse_name: (cost, route) }
"""

from algorithms.dijkstra import dijkstra


# ─────────────────────────────────────────────────────────────────────────────
# Core Held-Karp DP
# ─────────────────────────────────────────────────────────────────────────────

def solve_tsp_dp(warehouse_name: str,
                 city_names: list[str],
                 dist_matrix: dict[str, dict[str, float]]):
    """
    Held-Karp exact TSP for one warehouse and its assigned cities.

    Parameters
    ----------
    warehouse_name : str
        Starting/ending depot (e.g. "W1").
    city_names : list[str]
        Cities that must be visited (no duplicates, order irrelevant).
    dist_matrix : dict
        dist_matrix[a][b] = shortest distance from node a to node b.
        Must contain entries for the warehouse and all city names.

    Returns
    -------
    (min_cost, route)
        min_cost : float   — total round-trip distance
        route    : list    — [warehouse, c1, c2, ..., ck, warehouse]

    Edge cases
    ----------
    • 0 cities  → cost 0, route [warehouse]
    • 1 city    → cost = dist(W→c) + dist(c→W), route [W, c, W]
    • Unreachable leg → cost = inf, route still returned (best effort)
    """

    n = len(city_names)

    # ── trivial cases ────────────────────────────────────────────────────────
    if n == 0:
        return 0, [warehouse_name]

    if n == 1:
        c = city_names[0]
        d_out = dist_matrix.get(warehouse_name, {}).get(c, float('inf'))
        d_back = dist_matrix.get(c, {}).get(warehouse_name, float('inf'))
        cost = d_out + d_back
        return cost, [warehouse_name, c, warehouse_name]

    # ── build compact index ──────────────────────────────────────────────────
    # Index 0 = warehouse (depot), indices 1..n = cities
    nodes = [warehouse_name] + city_names          # length n+1
    idx   = {name: i for i, name in enumerate(nodes)}

    def dist(a: str, b: str) -> float:
        return dist_matrix.get(a, {}).get(b, float('inf'))

    # ── DP tables ────────────────────────────────────────────────────────────
    # dp[mask][i] = min cost to reach city i (1-based) having visited exactly
    #               the cities encoded in `mask` (bit j set ↔ city j visited),
    #               starting from the depot (node 0).
    #
    # mask is an integer over n bits (one per city, NOT the depot).
    # Bit j (0-indexed) corresponds to city_names[j] = nodes[j+1].

    FULL   = (1 << n) - 1          # all cities visited
    INF    = float('inf')

    dp     = [[INF] * n for _ in range(1 << n)]
    parent = [[-1]  * n for _ in range(1 << n)]

    # ── initialise: depot → each city directly ───────────────────────────────
    for j in range(n):
        city_j = nodes[j + 1]
        dp[1 << j][j] = dist(warehouse_name, city_j)

    # ── fill DP ──────────────────────────────────────────────────────────────
    for mask in range(1, 1 << n):
        for last in range(n):
            if not (mask & (1 << last)):   # last city not in this subset
                continue
            if dp[mask][last] == INF:
                continue

            last_city = nodes[last + 1]

            for nxt in range(n):
                if mask & (1 << nxt):      # nxt already visited
                    continue

                nxt_city  = nodes[nxt + 1]
                new_mask  = mask | (1 << nxt)
                new_cost  = dp[mask][last] + dist(last_city, nxt_city)

                if new_cost < dp[new_mask][nxt]:
                    dp[new_mask][nxt]     = new_cost
                    parent[new_mask][nxt] = last

    # ── find best last city before returning to depot ────────────────────────
    min_cost  = INF
    last_city_idx = -1

    for last in range(n):
        if dp[FULL][last] == INF:
            continue
        return_cost = dist(nodes[last + 1], warehouse_name)
        total       = dp[FULL][last] + return_cost

        if total < min_cost:
            min_cost      = total
            last_city_idx = last

    # ── reconstruct path ─────────────────────────────────────────────────────
    route_indices = []
    mask          = FULL
    cur           = last_city_idx

    while cur != -1:
        route_indices.append(cur)
        prev = parent[mask][cur]
        mask = mask ^ (1 << cur)
        cur  = prev

    route_indices.reverse()

    route = [warehouse_name] + [nodes[i + 1] for i in route_indices] + [warehouse_name]

    return min_cost, route


# ─────────────────────────────────────────────────────────────────────────────
# Helper: group cities by their primary warehouse
# ─────────────────────────────────────────────────────────────────────────────

def _group_cities_by_warehouse(optimized_allocation: dict,
                                warehouses) -> dict[str, list[str]]:
    """
    Build  { warehouse_name : [city1, city2, …] }  from the final allocation,
    fully respecting fractional splits.

    A city split across multiple warehouses (fractional knapsack) is added to
    EVERY warehouse it has a non-zero allocation in.  Each of those warehouses
    must physically deliver units to that city, so every one of them must
    include it in their delivery route.

    Example
    -------
    NagpurCity -> {W1: 35, W4: 10, W6: 20}
        W1 route includes NagpurCity  (35 units to deliver)
        W4 route includes NagpurCity  (10 units to deliver)
        W6 route includes NagpurCity  (20 units to deliver)
    """
    groups: dict[str, list[str]] = {w.name: [] for w in warehouses}

    for city_name, wh_dict in optimized_allocation.items():
        for wh_name, units in wh_dict.items():
            if units > 0 and wh_name in groups:
                groups[wh_name].append(city_name)

    return groups


# ─────────────────────────────────────────────────────────────────────────────
# Build a full pairwise distance matrix for TSP stops
# ─────────────────────────────────────────────────────────────────────────────

def _build_tsp_dist_matrix(stops: list[str], graph) -> dict[str, dict[str, float]]:
    """
    Run Dijkstra from every stop and keep only distances to other stops.
    This gives us the exact shortest-path cost between any two TSP nodes.
    """
    matrix: dict[str, dict[str, float]] = {}
    for s in stops:
        all_dist   = dijkstra(graph, s)
        matrix[s]  = {t: all_dist.get(t, float('inf')) for t in stops}
    return matrix


# ─────────────────────────────────────────────────────────────────────────────
# Top-level driver called from main.py
# ─────────────────────────────────────────────────────────────────────────────

def compute_tsp_for_all_warehouses(optimized_allocation: dict,
                                   warehouses,
                                   graph) -> dict[str, tuple]:
    """
    For every warehouse compute the optimal delivery route via Held-Karp DP.

    Parameters
    ----------
    optimized_allocation : dict
        { city_name : { warehouse_name : units, … } }   (post-Tabu Search)
    warehouses : list of Warehouse objects
    graph      : Graph object (used to re-run Dijkstra between TSP stops)

    Returns
    -------
    dict  { warehouse_name : (optimal_cost, route_list) }
        route_list = [W, c1, c2, …, ck, W]   (round-trip)
        Warehouses with no assigned cities have cost=0, route=[W].
    """
    groups  = _group_cities_by_warehouse(optimized_allocation, warehouses)
    results = {}

    for warehouse in warehouses:
        wh_name    = warehouse.name
        city_names = groups.get(wh_name, [])

        if not city_names:
            results[wh_name] = (0, [wh_name])
            continue

        # Build distance matrix covering the warehouse + its cities
        all_stops  = [wh_name] + city_names
        dist_matrix = _build_tsp_dist_matrix(all_stops, graph)

        cost, route = solve_tsp_dp(wh_name, city_names, dist_matrix)
        results[wh_name] = (cost, route)

    return results