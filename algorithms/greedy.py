def greedy_allocation(cities, warehouses, shipping_cost_matrix):

    allocation = {}

    for city in cities:

        city_name = city.name
        demand = city.demand

        costs = shipping_cost_matrix[city_name]

        best_warehouse = min(costs, key=costs.get)

        allocation[city_name] = {best_warehouse: demand}

    return allocation