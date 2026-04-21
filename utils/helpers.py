import json
from models.city import City
from models.warehouse import Warehouse


def load_data(file_path):

    with open(file_path, "r") as f:
        data = json.load(f)

    cities = []
    warehouses = []
    roads = []

    for c in data["cities"]:
        cities.append(City(c["name"], c["demand"]))

    for w in data["warehouses"]:
        warehouses.append(Warehouse(w["name"], w["capacity"]))

    for r in data["roads"]:
        roads.append((r["from"], r["to"], r["distance"]))

    return cities, warehouses, roads

def compute_total_cost(allocation, shipping_cost_matrix):

    total_cost = 0

    for city in allocation:

        for warehouse, units in allocation[city].items():

            cost_per_unit = shipping_cost_matrix[city][warehouse]

            total_cost += units * cost_per_unit

    return total_cost


def compute_warehouse_usage(allocation):

    usage = {}

    for city in allocation:
        for w, units in allocation[city].items():
            usage[w] = usage.get(w, 0) + units

    return usage


def check_capacity_feasible(allocation, warehouses):

    usage = compute_warehouse_usage(allocation)

    capacity = {w.name: w.capacity for w in warehouses}

    for w in usage:
        if usage[w] > capacity[w]:
            return False

    return True