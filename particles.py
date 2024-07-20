import numpy as np
from enum import Enum
from numba import jit
import constants
import pygame
import random


# Methods for all particles
class Particles():
    __particleAttractions = None
    CURRENT_PARTICLE_COUNT = constants.START_PARTICLES
    
    spawnIteration, SPAWN_ITERATION = 100, 2

    positions, velocities, types, typesAndSizes = None, None, None, None

    colors = ((245, 41, 170), # Pink
                (112, 215, 255), # Cyan
                (156, 174, 169), # GREY
                (255, 0, 0),#(244, 224, 77), # Red
                (19, 138, 54),#(112, 5, 72), # Purple
                (224, 142, 0)
                , # Orange
                (0, 255, 0), (0, 0, 255), (255, 255, 255)
                 )

    
    @staticmethod
    def setAttractions():
        attractions = np.random.uniform(0.2, 1, (constants.PARTICLE_TYPE_COUNT, constants.PARTICLE_TYPE_COUNT))
    
        # Make some of the forces negative
        mask = np.random.random((constants.PARTICLE_TYPE_COUNT, constants.PARTICLE_TYPE_COUNT)) < 0.5
        attractions[mask] *= -1
        
        print(f"Forces are {attractions}")
        return attractions
    
    @staticmethod
    def spawnNewParticle():
        if Particles.CURRENT_PARTICLE_COUNT >= constants.MAX_PARTICLES:
            print(f"Attempted particle spawn while capacity was full")
            return
        
        if Particles.spawnIteration == 0:
            Particles.positions[Particles.CURRENT_PARTICLE_COUNT] = np.array([constants.SCREEN_WIDTH // 2 + random.randint(-10, 10), constants.SCREEN_HEIGHT // 2 + random.randint(-10, 10)])
            Particles.velocities[Particles.CURRENT_PARTICLE_COUNT] = np.array([0, 0])
            Particles.CURRENT_PARTICLE_COUNT += 1

            Particles.spawnIteration = Particles.SPAWN_ITERATION
        else:
            Particles.spawnIteration -= 1
    
    
    @jit(nopython=True)
    def detectCloseParticleIndices(index, positions, typesAndSizes, currentParticleCount):
        
        closeIndexes = np.zeros(constants.MIN_PARTICLES_FOR_FUSION, dtype=np.int32)
        # closePositions = np.zeros((constants.MIN_PARTICLES_FOR_FUSION, 2), dtype=np.float64)
        closeSizes = np.zeros(constants.MIN_PARTICLES_FOR_FUSION, dtype=np.int32)

        closeParticlesDetected = 0

        for i in range(currentParticleCount):
            if i == index:
                continue
            if typesAndSizes[i, 0] != typesAndSizes[index, 0]:
                continue

            print(f"Type me {typesAndSizes[index, 0]} | type they {typesAndSizes[i, 0]}")

            dir_x = positions[i, 0] - positions[index, 0]
            dir_y = positions[i, 1] - positions[index, 1]
                    
            
            dist = np.sqrt(dir_x**2 + dir_y**2)

                
            if dist >= constants.MIN_PARTICLE_INFLUENCE:
                continue

            # Close enough to consider for fusion
            
            closeIndexes[closeParticlesDetected] = i
            # closePositions[closeParticlesDetected] = positions[i]
            closeSizes[closeParticlesDetected] = typesAndSizes[i, 1]

            closeParticlesDetected += 1

            if closeParticlesDetected >= constants.MIN_PARTICLES_FOR_FUSION:
                # Calc new size
                size = np.sum(closeSizes)
                # size = size
                
                # Manually calculate the mean position
                sum_x = 0.0
                sum_y = 0.0
                for j in range(closeParticlesDetected):
                    sum_x += positions[closeIndexes[j], 0]
                    sum_y += positions[closeIndexes[j], 1]
                averagePos = np.array([sum_x / closeParticlesDetected, sum_y / closeParticlesDetected])



                # averagePos = (positions[closeIndexes[:closeParticlesDetected]].mean(axis=0))
                #np.average(closePositions)

                return closeIndexes, averagePos, int(typesAndSizes[index, 0]), int(size)
            
        print("BOOFER")
        return closeIndexes, np.zeros(2, dtype=np.float64), int(0), int(0)


    @jit(nopython=True)
    def updateParticles(positions, velocities, typesAndSizes, attractions, currentParticleCount):
        new_positions = np.empty_like(positions)
        new_velocities = np.empty_like(velocities)
        fusionCandidate = -1

        for i in range(currentParticleCount):
            totForceX, totForceY = 0.0, 0.0
            pos_x, pos_y = positions[i]
            vel_x, vel_y = velocities[i]
            p_type = typesAndSizes[i, 0]
            size = typesAndSizes[i, 1]
            fusionCount = 0

            for j in range(currentParticleCount):
                if i == j:
                    continue
                
                dir_x = positions[j, 0] - pos_x
                dir_y = positions[j, 1] - pos_y
                    
                # Ensure forces obey screen wrapping
                if dir_x > 0.5 * constants.SCREEN_WIDTH:
                    dir_x -= constants.SCREEN_WIDTH
                if dir_x < -0.5 * constants.SCREEN_WIDTH:
                    dir_x += constants.SCREEN_WIDTH
                if dir_y > 0.5 * constants.SCREEN_HEIGHT:
                    dir_y -= constants.SCREEN_HEIGHT
                if dir_y < -0.5 * constants.SCREEN_HEIGHT:
                    dir_y += constants.SCREEN_HEIGHT
                        
                dist = np.sqrt(dir_x**2 + dir_y**2)

                if dist <= 0:
                    continue
                if dist >= constants.MAX_PARTICLE_INFLUENCE:
                    continue

                dir_x, dir_y = dir_x / dist, dir_y / dist # Normalize dir vector
                other_type = typesAndSizes[j, 0]
                if dist < constants.MIN_PARTICLE_INFLUENCE:
                    force = abs(attractions[p_type, other_type]) * -3 * (1 - dist / constants.MIN_PARTICLE_INFLUENCE) * constants.K * size / 2
                    totForceX += dir_x * force
                    totForceY += dir_y * force

                    if p_type == other_type:
                        fusionCount += 1
                else:
                    force = attractions[p_type, other_type] * (1 - dist / constants.MAX_PARTICLE_INFLUENCE) * constants.K * size / 2
                    totForceX += dir_x * force
                    totForceY += dir_y * force
                
            
            if fusionCandidate == -1:
                if fusionCount >= constants.MIN_PARTICLES_FOR_FUSION:
                    fusionCandidate = i    
            
            new_vel_x = vel_x + totForceX
            new_vel_y = vel_y + totForceY
            new_pos_x = (pos_x + new_vel_x) % constants.SCREEN_WIDTH
            new_pos_y = (pos_y + new_vel_y) % constants.SCREEN_HEIGHT
            new_vel_x *= constants.FRICTION
            new_vel_y *= constants.FRICTION
            
            new_positions[i] = new_pos_x, new_pos_y
            new_velocities[i] = new_vel_x, new_vel_y
            
        return new_positions, new_velocities, fusionCandidate
    
    # Original array
    array = np.zeros(200, dtype=int)
    # Let's say indices 0-25 contain important data
    array[:26] = np.arange(26)

    # Indices to remove
    indices_to_remove = [4, 19]

    def removeParticlesByIndices(indices):
        # Convert the array to a list for easier manipulation
        
        indicesList = indices.tolist()
        print(f"Indices len {len(indicesList)}")
        posList = Particles.positions.tolist()
        velList = Particles.velocities.tolist()
        typesAndSizesList = Particles.typesAndSizes.tolist()
        
        # Removeal - reverse sorting is important
        for index in sorted(indicesList, reverse=True):
            del posList[index]
            del velList[index]
            del typesAndSizesList[index]

        Particles.CURRENT_PARTICLE_COUNT -= len(indicesList)

        print(f"pCount after removal {Particles.CURRENT_PARTICLE_COUNT}")
        
        # Convert back to numpy array
        positionsTrimmed = np.array(posList[:Particles.CURRENT_PARTICLE_COUNT])
        velocitiesTrimmed = np.array(velList[:Particles.CURRENT_PARTICLE_COUNT])
        typesAndSizesTrimmed = np.array(typesAndSizesList[:Particles.CURRENT_PARTICLE_COUNT])

        
        # Create a new array with the same size, initialized with zeros
        newPositions = np.zeros((len(posList) + len(indicesList), 2), dtype=Particles.positions.dtype)
        newVelocities = np.zeros((len(velList) + len(indicesList), 2), dtype=Particles.velocities.dtype)
        newTypesAndSizes = np.zeros((len(typesAndSizesList) + len(indicesList), 2), dtype=Particles.typesAndSizes.dtype)
        
        # Copy the trimmed array into the new array
        newPositions[:len(positionsTrimmed)] = positionsTrimmed
        print(f"positionsTrimmed: {positionsTrimmed.size} | {positionsTrimmed}")
        print(f"newPos is now {newPositions.size} | {newPositions}")
        print(f"pCount {Particles.CURRENT_PARTICLE_COUNT}")


        newVelocities[:len(velocitiesTrimmed)] = velocitiesTrimmed
        newTypesAndSizes[:len(typesAndSizesTrimmed)] = typesAndSizesTrimmed
    
        
        return newPositions, newVelocities, newTypesAndSizes

    
    @staticmethod
    def draw():
        for i in range(Particles.CURRENT_PARTICLE_COUNT):
            color = Particles.colors[Particles.types[i]]
            pygame.draw.circle(constants.SCREEN, color, (Particles.positions[i, 0], Particles.positions[i, 1]), Particles.typesAndSizes[i, 1])
    
    # @staticmethod
    # class particleTypeColors(Enum):
    #     PINK = (255, 130, 169)
    #     TEAL = (44, 175, 201)
    #     GREY = (156, 174, 169)
    #     MAIZE = (244, 224, 77)
    #     INDIGO = (84, 13, 110)
    #     ORANGE = (224, 92, 21)

    
    @staticmethod
    def getParticleInfo():
        return (Particles.positions, Particles.velocities, Particles.typesAndSizes)
        
    
    # @staticmethod
    # def particleTypeByIndex(index):
    #     switch = {
    #         0: Particle.particleTypes.PINK,
    #         1: Particle.particleTypes.TEAL,
    #         2: Particle.particleTypes.GREY,
    #         3: Particle.particleTypes.MAIZE,
    #         4: Particle.particleTypes.INDIGO,
    #         5: Particle.particleTypes.ORANGE
    #     }
    #     return switch.get(index)

    # @staticmethod
    # def particleTypeByEnum(enum):
    #     switch = {
    #         Particle.particleTypes.PINK: 0,
    #         Particle.particleTypes.TEAL: 1,
    #         Particle.particleTypes.GREY: 2,
    #         Particle.particleTypes.MAIZE: 3,
    #         Particle.particleTypes.INDIGO: 4,
    #         Particle.particleTypes.ORANGE: 5,
    #     }
    #     return switch.get(enum)