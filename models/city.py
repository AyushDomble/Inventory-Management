class City:
    def __init__(self, name, demand):
        self.name = name
        self.demand = demand

    def __repr__(self):
        return f"City(name={self.name}, demand={self.demand})"