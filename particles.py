import numpy as np
from enum import Enum
from numba import jit, types
import constants
from constants import Constants
import pygame
import random
from point import Point


# Methods for all particles
class Particles():
    __particleAttractions = None
    CURRENT_PARTICLE_COUNT = constants.START_PARTICLES
    
    spawnIteration, SPAWN_ITERATION = 10, 6

    positions, velocities, typesAndSizes, splitTimers = None, None, None, None
    
    particleSurfaces = {}

    colors = [(245, 41, 170), # Pink
                (112, 215, 255), # Cyan
                (156, 174, 169), # GREY
                (255, 0, 0),#(244, 224, 77), # Red
                (19, 138, 54),#(112, 5, 72), # Purple
                (224, 142, 0), # Orange
                (0, 255, 0), (0, 0, 255), (255, 255, 255), (3, 121, 113), (247, 179, 43)
    ]

    
    @staticmethod
    def setAttractions():
        attractions = np.random.uniform(0.2, 1, (constants.PARTICLE_TYPE_COUNT, constants.PARTICLE_TYPE_COUNT))
    
        # Make some of the forces negative
        mask = np.random.random((constants.PARTICLE_TYPE_COUNT, constants.PARTICLE_TYPE_COUNT)) < 0.5
        attractions[mask] *= -1
        
        print(f"Forces are {attractions}")
        return attractions
    
    
    @jit(nopython=True)
    def updateParticles(positions, velocities, typesAndSizes, splitTimers, attractions, currentParticleCount):
        """ Update positions and velocities for all particles directly - faster than creating a temp datatype
            Return fusion and fission info """
        fusionCandidate = -1
        fissionPosition = np.zeros(2, dtype=np.float64)
        fissionType = -1
        fissionQuantity = -1
        fissionDetected = False

        for i in range(currentParticleCount):
            totForceX, totForceY = 0.0, 0.0
            posX, posY = positions[i]
            
            pType = typesAndSizes[i, 0]
            pSize = typesAndSizes[i, 1]
            fusionCount = 0
            
            for j in range(currentParticleCount):
                # Ignore self
                if i == j:
                    continue
                
                dirX = positions[j, 0] - posX
                dirY = positions[j, 1] - posY
                    
                # Ensure forces obey screen wrapping
                if dirX > 0.5 * constants.SCREEN_WIDTH:
                    dirX -= constants.SCREEN_WIDTH
                if dirX < -0.5 * constants.SCREEN_WIDTH:
                    dirX += constants.SCREEN_WIDTH
                if dirY > 0.5 * constants.SCREEN_HEIGHT:
                    dirY -= constants.SCREEN_HEIGHT
                if dirY < -0.5 * constants.SCREEN_HEIGHT:
                    dirY += constants.SCREEN_HEIGHT
                        
                dist = np.sqrt(dirX**2 + dirY**2)
                if dist > constants.MAX_PARTICLE_INFLUENCE or dist <= 0:
                    continue

                    
                dirX, dirY = dirX / dist, dirY / dist # Normalize dir vector
                otherType = typesAndSizes[j, 0]
                otherSize = typesAndSizes[j, 1]
                if dist < constants.MIN_PARTICLE_INFLUENCE:
                    force = (abs(attractions[pType, otherType]) * -3 * otherSize * (1 - dist / constants.MIN_PARTICLE_INFLUENCE) * constants.K) / pSize
                    
                    if dist < constants.MAX_FUSION_DISTANCE and pType == otherType:
                        fusionCount += 1
                else:
                    force = (attractions[pType, otherType] * otherSize * (1 - dist / constants.MAX_PARTICLE_INFLUENCE) * constants.K) / pSize
                    
                totForceX += dirX * force
                totForceY += dirY * force
            
            # Progress towards fission
            if pSize > constants.MIN_FISSION_SIZE:
                newTimer = splitTimers[i] + 1

                # Calc values for new particles from fission
                if (not fissionDetected) and (newTimer >= constants.TIME_BEFORE_FISSION) and (currentParticleCount < constants.MAX_PARTICLES):
                    splitTimers[i] = 0
                    fissionPosition = positions[i]
                    fissionType = pType
                    fissionQuantity = pSize - constants.MIN_FISSION_SIZE
                    typesAndSizes[i, 1] = 2
                    
                    fissionDetected = True
                else:
                    splitTimers[i] = newTimer
            
                    
            
            if fusionCandidate == -1:
                if fusionCount >= constants.MIN_PARTICLES_FOR_FUSION:# and currentParticleCount < constants.MAX_PARTICLES:
                    fusionCandidate = i
            
            newVelX = velocities[i, 0] + totForceX
            newVelY = velocities[i, 1] + totForceY
            positions[i] = (posX + newVelX) % constants.SCREEN_WIDTH, (posY + newVelY) % constants.SCREEN_HEIGHT



            newVelX *= constants.FRICTION
            newVelY *= constants.FRICTION

            velocities[i] = newVelX, newVelY
            
        return fusionCandidate, fissionPosition, fissionType, fissionQuantity
    

    @staticmethod
    def spawnParticle(pos, type):
        # Prevent buffer overflow
        if Particles.CURRENT_PARTICLE_COUNT >= constants.MAX_PARTICLES:
            # print(f"Attempted to spawn particle when limit was reached")
            return
        
        # Ensure particles never have the exact same pos
        pos[0] += random.uniform(-0.1, 0.1)
        pos[1] += random.uniform(-0.1, 0.1)

        Particles.positions[Particles.CURRENT_PARTICLE_COUNT] = pos

        # Ensure arrays are clean
        Particles.velocities[Particles.CURRENT_PARTICLE_COUNT] = np.array([0, 0], dtype=np.float32)
        Particles.typesAndSizes[Particles.CURRENT_PARTICLE_COUNT] = np.array([type, 2])

        print(f"Last before insert: {Constants.PARTICLE_QUADTREE.insertionOrder[-1].index}")
        newPoint = Point(pos[:], Particles.CURRENT_PARTICLE_COUNT)
        Constants.PARTICLE_QUADTREE.insert(newPoint)
        print(f"New particle added to quadtree last is now: {Constants.PARTICLE_QUADTREE.insertionOrder[-1].index}")
        
        Particles.CURRENT_PARTICLE_COUNT += 1

        




    @staticmethod
    def spawnParticlePeriodically():
        if Particles.spawnIteration == 0:
            if Particles.CURRENT_PARTICLE_COUNT >= constants.MAX_PARTICLES:
                Particles.spawnIteration = Particles.SPAWN_ITERATION * 5
                return
            
            Particles.spawnParticle(np.array([constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2], dtype=np.float64), random.randint(0, constants.PARTICLE_TYPE_COUNT - 1))

            Particles.spawnIteration = Particles.SPAWN_ITERATION
        else:
            Particles.spawnIteration -= 1


    @jit(types.Tuple((types.int32[:], types.float64[:], types.int64))(types.int64, types.float64[:, :], types.int32[:, :], types.int64), nopython=True)
    def detectFusionIndices(index, positions, typesAndSizes, currentParticleCount):
        """ Determine the particles that will be removed during fusion
            Return particle indices for removal, avgPos (new particle spawn point), and particle type undergoing fusion
        """
        closeIndices = np.zeros(constants.MIN_PARTICLES_FOR_FUSION, np.int32)
        closeSizes = np.zeros(constants.MIN_PARTICLES_FOR_FUSION, np.int32)

        closeParticlesDetected = 0

        for i in range(currentParticleCount):
            if i == index:
                continue
            # Don't care about particles of different types
            if typesAndSizes[i, 0] != typesAndSizes[index, 0]:
                continue
            
            dir_x = positions[i, 0] - positions[index, 0]
            dir_y = positions[i, 1] - positions[index, 1]

            dist = np.sqrt(dir_x**2 + dir_y**2)

            if dist >= constants.MAX_FUSION_DISTANCE:
                continue

            # Close enough to consider for fusion
            closeIndices[closeParticlesDetected] = i
            closeSizes[closeParticlesDetected] = typesAndSizes[i, 1]
            closeParticlesDetected += 1

            if closeParticlesDetected >= constants.MIN_PARTICLES_FOR_FUSION:
                newSize = np.sum(closeSizes)
                newSize += typesAndSizes[index, 1]

                # Ceiled division so fusion results in a larger particle under more conditions
                newSize = (newSize + (constants.MIN_PARTICLES_FOR_FUSION - 1)) // (constants.MIN_PARTICLES_FOR_FUSION - 1)
                # sizeSum = sizeSum // (constants.MIN_PARTICLES_FOR_FUSION - 1)

                sum_x = 0.0
                sum_y = 0.0
                for j in range(closeParticlesDetected):
                    sum_x += positions[closeIndices[j], 0]
                    sum_y += positions[closeIndices[j], 1]
                averagePos = np.array([sum_x / closeParticlesDetected, sum_y / closeParticlesDetected], dtype=np.float64)


                return closeIndices, averagePos, newSize

        # Not enough close particles for fusion
        return closeIndices, np.zeros(2, dtype=np.float64), -1

    # Handle removing data arrays
    def removeParticlesForFusion(indices):
        indicesList = indices.tolist()
        posList = Particles.positions.tolist()[:Particles.CURRENT_PARTICLE_COUNT]
        velList = Particles.velocities.tolist()[:Particles.CURRENT_PARTICLE_COUNT]
        typesAndSizesList = Particles.typesAndSizes.tolist()[:Particles.CURRENT_PARTICLE_COUNT]
        splitTimersList = Particles.splitTimers.tolist()[:Particles.CURRENT_PARTICLE_COUNT]

        pType = -1

        # Removal - reverse sorting is important
        for index in sorted(indicesList, reverse=True):
            pType = typesAndSizesList[index][0]
            del posList[index]
            del velList[index]
            del typesAndSizesList[index]
            del splitTimersList[index]

            # Update quadtree
            # print(f"Quad before fusion removal")
            # for p in Constants.PARTICLE_QUADTREE.insertionOrder:
            #     print(f"{p.index}")
            Constants.PARTICLE_QUADTREE.remove(Constants.PARTICLE_QUADTREE.insertionOrder[index])
            # del Constants.PARTICLE_QUADTREE.insertionOrder[Constants.PARTICLE_QUADTREE.insertionOrder[index]]
            # Constants.PARTICLE_QUADTREE.insertionOrder.remove(particleToRemove)
            # Shift index of all following points
            for p in Constants.PARTICLE_QUADTREE.insertionOrder[index:]:
                p.index -= 1

            # print(f"Quad after fusion removal")
            # for p in Constants.PARTICLE_QUADTREE.insertionOrder:
            #     print(f"{p.index}")
            # print(f"Deleted index {index}: the surrounding indices are {Constants.PARTICLE_QUADTREE.insertionOrder[index-1].index} | {Constants.PARTICLE_QUADTREE.insertionOrder[index].index} | {Constants.PARTICLE_QUADTREE.insertionOrder[index+1].index}")
            # print(f"Last point is index {Constants.PARTICLE_QUADTREE.insertionOrder[len(Constants.PARTICLE_QUADTREE.insertionOrder) - 1].index}")
            Particles.CURRENT_PARTICLE_COUNT -= 1
        
        newPositions = np.zeros((constants.MAX_PARTICLES, 2), dtype=Particles.positions.dtype)
        newVelocities = np.zeros((constants.MAX_PARTICLES, 2), dtype=Particles.velocities.dtype)
        newTypesAndSizes = np.zeros((constants.MAX_PARTICLES, 2), dtype=Particles.typesAndSizes.dtype)
        newSplitTimers = np.zeros(constants.MAX_PARTICLES, dtype=Particles.splitTimers.dtype)

        # Copy trimmed array into new array of proper shape
        newPositions[:Particles.CURRENT_PARTICLE_COUNT] = np.array(posList)
        newVelocities[:Particles.CURRENT_PARTICLE_COUNT] = np.array(velList)
        newTypesAndSizes[:Particles.CURRENT_PARTICLE_COUNT] = np.array(typesAndSizesList)
        newSplitTimers[:Particles.CURRENT_PARTICLE_COUNT] = np.array(splitTimersList)

        return newPositions, newVelocities, newTypesAndSizes, newSplitTimers, pType
    
    @staticmethod
    def handleFission(pos, fType, quantity):
        # TODO: change
        
        # No fission this frame
        if fType < 0:
            return
        
        quantity += 1
        for _ in range(quantity**2):
            Particles.spawnParticle(pos, fType)
        
    @staticmethod
    def draw():
        
        # for i in range(Particles.CURRENT_PARTICLE_COUNT):
        #     pType = Particles.typesAndSizes[i, 0]
        #     pSize = Particles.typesAndSizes[i, 1]
        #     color = Particles.colors[pType]

        #     # Use cached surface if available
        #     if (pType, pSize) not in Particles.particleSurfaces:
        #         surface = pygame.Surface((pSize * 2, pSize * 2), pygame.SRCALPHA)
        #         pygame.draw.circle(surface, color, (pSize, pSize), pSize)
        #         Particles.particleSurfaces[(pType, pSize)] = surface
        #     else:
        #         surface = Particles.particleSurfaces[(pType, pSize)]

        #     pos = Particles.positions[i]
        #     constants.SCREEN.blit(surface, (pos[0] - pSize, pos[1] - pSize))
        
        
        # Lock the surface to avoid unnecessary state changes
        screenLock = pygame.surfarray.pixels2d(constants.SCREEN)
        for i in range(Particles.CURRENT_PARTICLE_COUNT):
            color = Particles.colors[Particles.typesAndSizes[i, 0]]
            # rawSize = Particles.typesAndSizes[i, 1]
            
            pygame.draw.circle(constants.SCREEN, color, (Particles.positions[i, 0], Particles.positions[i, 1]), Particles.typesAndSizes[i, 1])
        del screenLock


    
    @staticmethod
    def getParticleInfo():
        return (Particles.positions, Particles.velocities, Particles.typesAndSizes)
        