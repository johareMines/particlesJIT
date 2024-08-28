import numpy as np

class Point:
    def __init__(self, position, index):
        self.position = np.array(position)
        self.index = index
    
    
    def __eq__(self, other):
        return isinstance(other, Point) and self.index == other.index

    def __lt__(self, other):
        return isinstance(other, Point) and self.index < other.index

    def __hash__(self):
        return hash(self.index)

    def __repr__(self):
        return f"Point(index={self.index})"