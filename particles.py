import numpy as np
from enum import Enum
from numba import jit
import constants


# Methods for all particles
class Particles():
    __particleAttractions = None
    CURRENT_PARTICLE_COUNT = constants.START_PARTICLES
    
    spawnIteration, SPAWN_ITERATION = 100, 100

    positions, velocities, types = None, None, None

    @staticmethod
    def getParticleInfo():
        return (Particles.positions, Particles.velocities, Particles.types)
    
    @staticmethod
    def setAttractions():
        attractions = np.random.uniform(0.2, 1, (len(Particles.particleTypeColors), len(Particles.particleTypeColors)))
    
        # Make some of the forces negative
        mask = np.random.random((len(Particles.particleTypeColors), len(Particles.particleTypeColors))) < 0.5
        attractions[mask] *= -1
        
        print(f"Forces are {attractions}")
        return attractions
    
    @staticmethod
    def spawnNewParticle():
        if Particles.spawnIteration == 0:
            print(f"Did spawn")
            # print(f"{}")
            Particles.spawnIteration = Particles.SPAWN_ITERATION
        else:
            Particles.spawnIteration -= 1
    
    
    @jit(nopython=True)
    def updateParticles(positions, velocities, types, attractions, currentParticleCount):
        new_positions = np.empty_like(positions)
        new_velocities = np.empty_like(velocities)
        
        for i in range(currentParticleCount):
            totForceX, totForceY = 0.0, 0.0
            pos_x, pos_y = positions[i]
            vel_x, vel_y = velocities[i]
            p_type = types[i]
            
            for j in range(currentParticleCount):
                if i != j:
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
                    if dist > 0:
                        dir_x, dir_y = dir_x / dist, dir_y / dist # Normalize dir vector
                        other_type = types[j]
                        if dist < constants.MIN_PARTICLE_INFLUENCE:
                            force = abs(attractions[p_type, other_type]) * -3 * (1 - dist / constants.MIN_PARTICLE_INFLUENCE) * constants.K
                            totForceX += dir_x * force
                            totForceY += dir_y * force
                            
                        if dist < constants.MAX_PARTICLE_INFLUENCE:
                            force = attractions[p_type, other_type] * (1 - dist / constants.MAX_PARTICLE_INFLUENCE) * constants.K
                            totForceX += dir_x * force
                            totForceY += dir_y * force
            
            new_vel_x = vel_x + totForceX
            new_vel_y = vel_y + totForceY
            new_pos_x = (pos_x + new_vel_x) % constants.SCREEN_WIDTH
            new_pos_y = (pos_y + new_vel_y) % constants.SCREEN_HEIGHT
            new_vel_x *= constants.FRICTION
            new_vel_y *= constants.FRICTION
            
            new_positions[i] = new_pos_x, new_pos_y
            new_velocities[i] = new_vel_x, new_vel_y
            
        return new_positions, new_velocities
    
    
    
    @staticmethod
    class particleTypeColors(Enum):
        PINK = (255, 130, 169)
        TEAL = (44, 175, 201)
        GREY = (156, 174, 169)
        MAIZE = (244, 224, 77)
        INDIGO = (84, 13, 110)
        ORANGE = (224, 92, 21)
        
    
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