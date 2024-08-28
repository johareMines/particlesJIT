import numpy as np
import time
import collections
import constants
from constants import Constants
import threading
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
import logging
from sortedcontainers import SortedSet
from particles import Particles
from point import Point




class Quadtree:
    def __init__(self, boundary, capacity=5, depth=0, max_depth=20, insertionOrder=None):
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth

        self.points = []
        self.is_leaf = True
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

        self.insertionOrder = SortedSet(key=lambda p: p.index)


        # self.insertionOrder = insertionOrder if insertionOrder is not None else []
        # self.lock = RLock()#threading.Lock()


    # def clear(self):
    #     self.points = []
    #     self.insertionOrder.clear()
    #     self.divided = False
    #     self.is_leaf = True
    #     self.nw = None
    #     self.ne = None
    #     self.sw = None
    #     self.se = None

    def insert(self, point):
        try:
            # print(f"Attempting to insert point {point.position} at depth {self.depth}")
            if not self.boundary.contains(point.position):
                # print(f"Point {point.position} is outside the boundary {self.boundary}")
                return False

            
            # print(f"Node at depth {self.depth} has {len(self.points)} points with capacity {self.capacity}")
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append(point)
                self.insertionOrder.add(point)
                # print(f"Point {point.position} inserted at depth {self.depth}")
                return True

            if self.is_leaf:
                # print(f"Node at depth {self.depth} is full, subdividing...")
                self.subdivide()

            # Redistribute points to child nodes
            inserted = False
            for child in (self.nw, self.ne, self.sw, self.se):
                if child.insert(point):
                    inserted = True
                    break


            if inserted:
                # Append the point to the insertion order only if successfully inserted into a child
                self.insertionOrder.add(point)
            else:
                print(f"Failed to insert point {point.index}")

            return inserted
        except Exception as e:
            print(f"Error in insert: {e}")
            raise  # Re-raise the exception to propagate it upwards

    def batchInsert(self, positions):
        for i, pos in enumerate(positions):
            inputPos = pos[:]
            p = Point(inputPos, i)
            self.insert(p)
        
    # def update(self, point):
    #     if self.remove(point):
    #         return self.insert(point)
    #     return False

    def update(self, point):
        newPos = np.copy(Particles.positions[point.index])
        

        # If the current node is not a leaf, delegate the update to the appropriate child node
        if not self.is_leaf:
            # Update in the correct child node
            for child in (self.nw, self.ne, self.sw, self.se):
                if child.boundary.contains(point.position):
                    child.update(point)
                    return
            # If the point doesn't fit in any child (which shouldn't happen), handle it here
            print(f"Point {point.index} at position {newPos} doesn't fit into any child node. ISSUE.")
            exit(0)
        else:
            # If the point is still within the current node's boundary, just update its position
            if self.boundary.contains(newPos):
                # print(f"Normal movement {point.index} from {point.position} to {newPos} is still within boundary({self.boundary.toString()})")
                point.position = newPos
            else:  # Handle reinsertion
                print(f"Update reinsert of point {point.index} at {point.position}, moving to new position {newPos}")
                Constants.PARTICLE_QUADTREE.remove(point)
                
                # print(f"Points in quadran {self.boundary.toString()} after removal")
                # for p in self.points:
                #     print(f"{p.index}: {p.position}")
                # for p in self.insertionOrder:
                #     print(f"Insertion order: {p.index}")
                
                # Update the point's position to the new one
                point.position = newPos
                
                # Reinsert the point into the quadtree, it will automatically find the correct node
                insertWorked = Constants.PARTICLE_QUADTREE.insert(point)
                if not insertWorked:
                    print(f"!!! ISSUE Insert didn't work after removal for particle {point.index}")



    # Update all points
    def batchUpdate(self):
        for p in list(self.insertionOrder):  # list to avoid modification during iteration
            self.update(p)
        

    def remove(self, point):
        # if not Constants.PARTICLE_QUADTREE.boundary.contains(point.position):
        #     return False
        
        # if point in Constants.PARTICLE_QUADTREE.points
        if not self.boundary.contains(point.position):
            return False

        if point in self.points:
            
            print(f"Attempting removal on point {point.index} in boundary {self.boundary.toString()}. It currently contains:")
            for p in self.insertionOrder:
                print(f"{p.index} | {p.position}")
            print(f"Actual points list is")
            for p in self.points:
                print(f"!{p.index} | {p.position}")
            
            self.points.remove(point)
            self.insertionOrder.remove(point)
            print(f"Len after deletion is {len(self.points)} | {len(self.insertionOrder)}")
            # else:
            #     print(f"!!!Warning: Point {point.index} not found in insertionOrder during removal.")
            return True

        if not self.is_leaf:
            return any(child.remove(point) for child in (self.nw, self.ne, self.sw, self.se))

        return False

    def query(self, region):
        if not self.boundary.intersects(region):
            return []

        results = []
        for point in self.points:
            if region.contains(point.position):
                results.append(point)

        if not self.is_leaf:
            results.extend(self.nw.query(region))
            results.extend(self.ne.query(region))
            results.extend(self.sw.query(region))
            results.extend(self.se.query(region))

        return results

    def subdivide(self):
        # print(f"Subdividing at depth {self.depth} with {len(self.points)} points")
        if not self.is_leaf:
            # print("Already subdivided, returning")
            return
        
        print(f"SUBDIVIDING")
        for p in self.points:
            print (f"{p.index} | {p.position}")
        min_x, min_y, max_x, max_y = self.boundary.min_x, self.boundary.min_y, self.boundary.max_x, self.boundary.max_y
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        print(f"Boundaries: {min_x}, {max_x}, {min_y}, {max_y}")
        self.nw = Quadtree(Rectangle(min_x, min_y, mid_x, mid_y), self.capacity, self.depth + 1, self.max_depth, self.insertionOrder)
        self.ne = Quadtree(Rectangle(mid_x, min_y, max_x, mid_y), self.capacity, self.depth + 1, self.max_depth, self.insertionOrder)
        self.sw = Quadtree(Rectangle(min_x, mid_y, mid_x, max_y), self.capacity, self.depth + 1, self.max_depth, self.insertionOrder)
        self.se = Quadtree(Rectangle(mid_x, mid_y, max_x, max_y), self.capacity, self.depth + 1, self.max_depth, self.insertionOrder)

        # print(f"Subdivided into nw, ne, sw, se at depth {self.depth + 1}")
        self.is_leaf = False
        
        

        # Redistribute points to child nodes
        for point in self.points:
            inserted = False
            for child in (self.nw, self.ne, self.sw, self.se):
                if child.insert(point):
                    inserted = True
                    break

            if not inserted:
                print(f"Point {point.index} at position {point.position} could not be inserted into any child node at depth {self.depth + 1}")
                print(f"Point boundaries: nw: {self.nw.boundary.toString()}, ne: {self.ne.boundary.toString()}, sw: {self.sw.boundary.toString()}, se: {self.se.boundary.toString()}")
                raise RuntimeError(f"Failed to insert point {point.index} at depth {self.depth + 1} into any child node")
        # for point in self.points:
        #     if not any(child.insert(point) for child in (self.nw, self.ne, self.sw, self.se)):
        #         raise RuntimeError(f"Failed to insert point {point.index} at depth {self.depth + 1} into any child node")
        
        # for point in self.points:
        #     inserted = False
        #     for child in (self.nw, self.ne, self.sw, self.se):
        #         if child.insert(point):
        #             inserted = True
        #             break  # Exit loop once the point is successfully inserted

        #     if not inserted:
        #         print(f"Failed to insert point {point.index} at depth {self.depth + 1}")
        
        self.points = []
        # self.insertionOrder = SortedSet(key=lambda p: p.index)
        # print(f"Cleared points in parent node at depth {self.depth}")


        # print(f"Finished redistributing points at depth {self.depth}")
       
    @staticmethod
    def batchQuery(particles, maxInfluenceDist):
        supercell_size = maxInfluenceDist
        supercell_map = collections.defaultdict(list)
        results = {}

        for i, p in enumerate(particles):
            supercell_x = int(p.position[0] // supercell_size)
            supercell_y = int(p.position[1] // supercell_size)
            supercell_map[(supercell_x, supercell_y)].append(p)
            results[p] = []

        for (scx, scy), particles_in_supercell in supercell_map.items():
            range_query = Rectangle(
                scx * supercell_size - maxInfluenceDist,
                scy * supercell_size - maxInfluenceDist,
                supercell_size + maxInfluenceDist * 2,
                supercell_size + maxInfluenceDist * 2
            )
            found = Constants.PARTICLE_QUADTREE.query(range_query, [])

            for p in particles_in_supercell:
                results[p] = [f for f in found if f != p]

        return results

    # @staticmethod
    # def batchCalcDest(particles):
    #     if not particles:
    #         return  # No particles to process

    #     # Grab a random particle to determine maxInfluenceDist
    #     maxInfluenceDist = next(iter(particles)).maxInfluenceDist  # Assuming all particles have the same maxInfluenceDist
    #     influenceTable = particles.__particleAttractions
        
    #     # Batch query the quadtree for all particles using supercells
    #     neighbors_dict = Particle.batchQuery(particles, maxInfluenceDist)
        
    #     # Calculate destinations for all particles
    #     for particle in particles:
    #         finalVelX, finalVelY = 0, 0
    #         maxInfluenceDistSquared = maxInfluenceDist ** 2
            
    #         neighbors = neighbors_dict[particle]
    #         for p in neighbors:
    #             dx = p.x - particle.x
    #             dy = p.y - particle.y
    #             distSquared = dx ** 2 + dy ** 2
                
    #             if distSquared > maxInfluenceDistSquared:
    #                 continue
                
    #             dist = math.sqrt(distSquared)
                
                
    #             influenceIndex = particle.particleTypeByEnum(p.particleType)
    #             influence = influenceTable[particle.particleType.name][influenceIndex]
                
    #             if influence > 0 and dist < particle.minInfluenceDist:
    #                 impact = particle.minInfluenceDist - dist
    #                 impact *= 0.4
    #                 influence -= impact
                
    #             influence *= math.exp(-dist / maxInfluenceDist)
                
    #             if dist != 0:
    #                 dirX = dx / dist
    #                 dirY = dy / dist
                    
    #                 finalVelX += influence * dirX
    #                 finalVelY += influence * dirY
            
    #         particle.destX = particle.x + finalVelX
    #         particle.destY = particle.y + finalVelY
    
    

class Rectangle:
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    # def contains(self, position, epsilon=1e-9):
    #     x, y = position
    #     return (self.min_x <= x < self.max_x + epsilon and
    #             self.min_y <= y < self.max_y + epsilon)
    def contains(self, position):
        x, y = position
        return self.min_x <= x < self.max_x and self.min_y <= y < self.max_y

    def intersects(self, other):
        return (
            self.min_x <= other.max_x and self.max_x >= other.min_x and
            self.min_y <= other.max_y and self.max_y >= other.min_y
        )
    
    def toString(self):
        return f"Rectangle: w {self.min_x} | e {self.max_x} | s {self.min_y} | n {self.max_y}"


