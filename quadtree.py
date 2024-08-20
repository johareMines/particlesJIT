import numpy as np
import time
import collections
import constants
from constants import Constants



class Point:
    def __init__(self, position, index):
        self.position = np.array(position)
        self.index = index

class Quadtree:
    def __init__(self, boundary, capacity=10, depth=0, max_depth=10):
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

    def clear(self):
        self.points = []
        self.divided = False
        self.is_leaf = True
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

    def insert(self, point):
        if not self.boundary.contains(point.position):
            return False

        if len(self.points) < self.capacity or self.depth >= self.max_depth:
            self.points.append(point)
            return True

        if self.is_leaf:
            self.subdivide()

        return any(child.insert(point) for child in (self.nw, self.ne, self.sw, self.se))


    def batchInsert(self, positions):
        for i, pos in enumerate(positions):
            p = Point(pos, i)
            self.insert(p)
        
    def update(self, point):
        if self.remove(point):
            return self.insert(point)
        return False

    def remove(self, point):
        if not self.boundary.contains(point.position):
            return False

        if point in self.points:
            self.points.remove(point)
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
        min_x, min_y, max_x, max_y = self.boundary.min_x, self.boundary.min_y, self.boundary.max_x, self.boundary.max_y
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        # self.nw = Quadtree(x, y, hw, hh, self.max_particles, self.depth + 1, self.max_depth)

        self.nw = Quadtree(Rectangle(min_x, min_y, mid_x, mid_y), self.capacity, self.depth + 1, self.max_depth)
        self.ne = Quadtree(Rectangle(mid_x, min_y, max_x, mid_y), self.capacity, self.depth + 1, self.max_depth)
        self.sw = Quadtree(Rectangle(min_x, mid_y, mid_x, max_y), self.capacity, self.depth + 1, self.max_depth)
        self.se = Quadtree(Rectangle(mid_x, mid_y, max_x, max_y), self.capacity, self.depth + 1, self.max_depth)

        self.is_leaf = False

        for point in self.points:
            self.nw.insert(point) or self.ne.insert(point) or self.sw.insert(point) or self.se.insert(point)

        self.points = []

       
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

    def contains(self, position):
        x, y = position
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def intersects(self, other):
        return (
            self.min_x <= other.max_x and self.max_x >= other.min_x and
            self.min_y <= other.max_y and self.max_y >= other.min_y
        )


