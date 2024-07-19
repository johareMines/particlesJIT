import constants
from particle import Particles
import pygame
import time
import sys
import psutil
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor

class Simulation:
    __instance = None
    def __init__(self, width=1920, height=1080):
        if Simulation.__instance is not None:
            raise Exception("Singleton can't be instantiated multiple times.")
        else:
            pygame.init()
            
            screenInfo = pygame.display.Info()

            constants.SCREEN_WIDTH = screenInfo.current_w
            constants.SCREEN_HEIGHT = screenInfo.current_h

            constants.SCREEN = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.RESIZABLE, display=constants.DISPLAY.value)
            
            self.clock = pygame.time.Clock()
            self.frame_times = []
            self.frame_print_time = time.time()

            self.performanceMonitor = PerformanceMonitor(constants.MONITOR_INTERVAL) # Interval in seconds
            self.performanceMonitor.start()

            # Event to handle killing thread on program end
            self.velThreadStopEvent = threading.Event()
                
    @staticmethod
    def get_instance():
        # Static method to get the singleton instance
        if Simulation.__instance is None:
            Simulation.__instance = Simulation()
        return Simulation.__instance

    def run(self):
        # Create particles
        Particles.__particleAttractions = Particles.setAttractions()
        positions = np.random.rand(constants.MAX_PARTICLES, 2) * [constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT]
        velocities = np.zeros((constants.MAX_PARTICLES, 2))
        types = np.random.randint(0, len(Particles.particleTypeColors), constants.MAX_PARTICLES)
        
        running = True
        while running:
            start_time = time.time() # For framerate calculation
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            constants.SCREEN.fill((0, 0, 0))  # Clear the screen
            
            
            positions, velocities = Particles.updateParticles(positions, velocities, types, Particles.__particleAttractions, Particles.MIN_INFLUENCE_DIST, Particles.MAX_INFLUENCE_DIST, 0.85, 0.05, Particles.CURRENT_PARTICLE_COUNT)
            
            # Draw circle at mouse position
            # self.drawMouseCircle()
            
            for i in range(Particles.CURRENT_PARTICLE_COUNT):
                color = pygame.Color(0)
                color.hsva = (types[i] * (360 // len(Particles.particleTypeColors)), 100, 100, 100)
                pygame.draw.circle(constants.SCREEN, color, (positions[i, 0], positions[i, 1]), 2)
            
            Particles.spawnNewParticle()
            
            pygame.display.flip() # Update display
            
            # Calc framerate
            self.clock.tick(60)  # FPS Limit
            end_time = time.time()
            frame_time = end_time - start_time
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 70:
                self.frame_times.pop(0)
            self.calculateFramerate()
            
            
            
        self.performanceMonitor.stop()
        self.performanceMonitor.join()

        
        pygame.quit()
        sys.exit()
        
    
    def calculateFramerate(self):
        if time.time() - self.frame_print_time < constants.MONITOR_INTERVAL:
            return
        
        if len(self.frame_times) < 70:
            return
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        fps = 1.0 / avg_frame_time
        print(f"FPS: {round(fps, 1)}")

        self.frame_print_time = time.time()
            
    
    
class PerformanceMonitor(threading.Thread):
    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.stopped = threading.Event()
        self.process = psutil.Process()

    def run(self):
        while not self.stopped.wait(self.interval):
            self.monitorCPU()
            self.monitorMemory()
            self.monitorObjects()

    def monitorCPU(self):
        cpu_percent = self.process.cpu_percent()
        print(f"CPU usage: {cpu_percent}%")
    
    def monitorMemory(self):
        memory_info = self.process.memory_info()
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024)} MB")  # Convert to MB
    
    def stop(self):
        self.stopped.set()
