import numpy as np

class Point:
    def __init__(self, position, index):
        self.position = np.array(position)
        self.index = index