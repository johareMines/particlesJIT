import constants
from particles import Particles
import pygame
import time
import sys
import psutil
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import uuid
import json
import os

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


            # Map numkeys to attraction value saves
            self.numberKeyMappings = {
                pygame.K_0: 0,
                pygame.K_1: 1,
                pygame.K_2: 2,
                pygame.K_3: 3,
                pygame.K_4: 4,
                pygame.K_5: 5,
                pygame.K_6: 6,
                pygame.K_7: 7,
                pygame.K_8: 8,
                pygame.K_9: 9
            }

            self.frame_times = []
            self.frame_print_time = time.time()

            self.performanceMonitor = PerformanceMonitor(constants.MONITOR_INTERVAL) # Interval in seconds
            self.performanceMonitor.start()

            # Event to handle killing thread on program end
            self.velThreadStopEvent = threading.Event()

    @staticmethod          
    def get_save_file_list(directory):
        # List files in the directory
        files = os.listdir(directory)
        fileList = []

        # Check if there is exactly one file
        for i in range(len(files)):
            fileList.append(files[i])
        
        return fileList
    
    @staticmethod
    def load_attractions_from_save(filePath):
        if not os.path.exists(filePath):
            raise FileNotFoundError(f"No such file: '{filePath}'")
        
        # Read the JSON file
        with open(filePath, 'r') as json_file:
            data = json.load(json_file)
        
        # Convert
        array = np.array(data)
        
        return array
    
    @staticmethod
    def save_attractions_to_JSON():
        # Save forces array to new JSON file
        jsonList = Particles.__particleAttractions.tolist()
                    
        # Time based UUID
        id = uuid.uuid1()


        # Define the directory and file path
        directory = 'SavedAttractions'
        file_path = os.path.join(directory, f'{id}.json')

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Write to the JSON file
        with open(file_path, 'w') as json_file:
            # data = {"example": "data"}  # Replace this with your actual data
            json.dump(jsonList, json_file)

            print(f"Data saved to {file_path}")

    @staticmethod
    def get_instance():
        # Static method to get the singleton instance
        if Simulation.__instance is None:
            Simulation.__instance = Simulation()
        return Simulation.__instance

    

    # Handle numkey press (load saved attraction values)
    def handle_key_press(self, key):
        if key in self.numberKeyMappings:
            self.load_save_file(self.numberKeyMappings[key])
        else:
            print(f"Invalid key: {key}")
        
    def load_save_file(self, index):
        directory = 'SavedAttractions/LoadDir'
        saveFiles = self.get_save_file_list(directory)

        if index >= len(saveFiles):
            return
        
        loadFile = os.path.join(directory, saveFiles[index])

        newAttractions = self.load_attractions_from_save(loadFile)

        Particles.__particleAttractions = newAttractions

        


    def run(self):
        # Initialize empty np arrays
        Particles.__particleAttractions = Particles.setAttractions()
        Particles.positions = (np.random.rand(constants.MAX_PARTICLES, 2) * [constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT]).astype(np.float64)
        Particles.velocities = np.zeros((constants.MAX_PARTICLES, 2), dtype=np.float32)
        Particles.typesAndSizes = np.column_stack((np.random.randint(0, constants.PARTICLE_TYPE_COUNT - 1, constants.MAX_PARTICLES), np.full(constants.MAX_PARTICLES, 2)))
        Particles.splitTimers = np.zeros(constants.MAX_PARTICLES, dtype=np.int64)
        # Particles.fissionParticles = np.array(np.zeros((constants.MAX_PARTICLES_FROM_FISSION, 2), dtype=np.float64), np.zeros(dtype=np.int32))
        # Particles.typesAndSizes = np.random.randint(0, constants.PARTICLE_TYPE_COUNT, constants.MAX_PARTICLES)
        
        print(f"Initial values: Pos {Particles.positions} | Vel {Particles.velocities} | TypesEtc {Particles.typesAndSizes}")

        

        running = True
        while running:
            start_time = time.time() # For framerate calculation
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        Particles.__particleAttractions = Particles.setAttractions()
                    if event.key == pygame.K_s:
                        self.save_attractions_to_JSON()

                    # Load saved values
                    elif event.key in self.numberKeyMappings:
                        self.handle_key_press(event.key)
                        


            constants.SCREEN.fill((0, 0, 0))  # Clear the screen
            
            inputPos, inputVel, inputTypesAndSizes = Particles.getParticleInfo()
            posUntrimmed, velUntrimmed, splitTimersUntrimmed, fusionCandidate, fissionPosition, fissionType, fissionQuantity = Particles.updateParticles(inputPos, inputVel, inputTypesAndSizes, Particles.splitTimers, Particles.__particleAttractions, Particles.CURRENT_PARTICLE_COUNT)
            Particles.positions[:Particles.CURRENT_PARTICLE_COUNT], Particles.velocities[:Particles.CURRENT_PARTICLE_COUNT], Particles.splitTimers[:Particles.CURRENT_PARTICLE_COUNT] = posUntrimmed[:Particles.CURRENT_PARTICLE_COUNT], velUntrimmed[:Particles.CURRENT_PARTICLE_COUNT], splitTimersUntrimmed[:Particles.CURRENT_PARTICLE_COUNT]
            
            # Particles.splitTimers = splitTimersUntrimmed
            # print(f"JUST UPDATED: Fusion {fusionCandidate} | Pcount {Particles.CURRENT_PARTICLE_COUNT} | Pos ({len(Particles.positions)}) {Particles.positions} | Vel ({len(Particles.velocities)}) {Particles.velocities} | TypeandSize ({len(Particles.typesAndSizes)}) {Particles.typesAndSizes}")
            # print(f"Just updated: fission {fissionPositionsTypesAndQuantities} ")#| split {Particles.splitTimers[:Particles.CURRENT_PARTICLE_COUNT]}")#{newTypesSizesAndSplitTimersUntrimmed}")#fissionParticle {fissionParticles}")
            # for i in newTypesSizesAndSplitTimersUntrimmed:
            #     print(i)
            if fusionCandidate >= 0:
                indices, avgPos, newSize = Particles.detectFusionIndices(fusionCandidate, Particles.positions, inputTypesAndSizes, Particles.CURRENT_PARTICLE_COUNT)

                # Commence fusion
                if newSize > 0:
                    # print(f"IN FUSION")

                    # Remove small particles
                    newPos, newVel, newTypesAndSizes, newSplitTimers, pType = Particles.removeParticlesForFusion(indices)
                    # print(f"Out of remove by indices: Pcount {Particles.CURRENT_PARTICLE_COUNT} | Pos ({len(newPos)}) {newPos} | Vel ({len(newVel)}) {newVel} | TypeandSize ({len(newTypesAndSizes)}) {newTypesAndSizes}")
            

                    Particles.positions, Particles.velocities, Particles.typesAndSizes, Particles.splitTimers = newPos, newVel, newTypesAndSizes, newSplitTimers

                    # print(f"Out of remove by indices: Ptype: {pType} | Pcount {Particles.CURRENT_PARTICLE_COUNT} | Pos ({len(Particles.positions)}) {Particles.positions} | Vel ({len(Particles.velocities)}) {Particles.velocities} | TypeandSize ({len(Particles.typesAndSizes)}) {Particles.typesAndSizes}")


                    # Add large particle
                    Particles.positions[Particles.CURRENT_PARTICLE_COUNT] = avgPos
                    Particles.velocities[Particles.CURRENT_PARTICLE_COUNT] = np.array([0, 0], dtype=np.float32)
                    Particles.typesAndSizes[Particles.CURRENT_PARTICLE_COUNT] = np.array([pType, newSize])
                    Particles.splitTimers[Particles.CURRENT_PARTICLE_COUNT] = 0

                    Particles.CURRENT_PARTICLE_COUNT += 1
            
            
            Particles.handleFission(fissionPosition, fissionType, fissionQuantity)


            # Draw circle at mouse position
            # self.drawMouseCircle()
            
            Particles.spawnParticlePeriodically()
            
            Particles.draw()
            
            
            
            
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
            self.monitorParticleCount()

    def monitorCPU(self):
        cpu_percent = self.process.cpu_percent()
        print(f"CPU usage: {cpu_percent}%")
    
    def monitorMemory(self):
        memory_info = self.process.memory_info()
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024)} MB")  # Convert to MB
    
    def monitorParticleCount(self):
        print(f"Particle Count: {Particles.CURRENT_PARTICLE_COUNT}")
    
    def stop(self):
        self.stopped.set()
