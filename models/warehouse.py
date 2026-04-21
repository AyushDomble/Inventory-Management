class Warehouse:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity

    def __repr__(self):
        return f"Warehouse(name={self.name}, capacity={self.capacity})"