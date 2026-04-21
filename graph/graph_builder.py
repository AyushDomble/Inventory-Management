class Graph:
    def __init__(self):
        self.adj_list = {}

    def add_edge(self, src, dest, weight):

        if src not in self.adj_list:
            self.adj_list[src] = []

        self.adj_list[src].append((dest, weight))

        # If roads are bidirectional add reverse edge
        if dest not in self.adj_list:
            self.adj_list[dest] = []

        self.adj_list[dest].append((src, weight))


    def get_neighbors(self, node):
        return self.adj_list.get(node, [])


    def display(self):
        for node in self.adj_list:
            print(f"{node} -> {self.adj_list[node]}")