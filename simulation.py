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

            # self.frame_times = []
            # self.frame_print_time = time.time()

            # self.performanceMonitor = PerformanceMonitor(constants.MONITOR_INTERVAL) # Interval in seconds
            # self.performanceMonitor.start()

            # # Event to handle killing thread on program end
            # self.velThreadStopEvent = threading.Event()

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
        Particles.positions = np.random.rand(constants.MAX_PARTICLES, 2) * [constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT]
        Particles.velocities = np.zeros((constants.MAX_PARTICLES, 2))
        Particles.types = np.random.randint(0, constants.PARTICLE_TYPE_COUNT, constants.MAX_PARTICLES)
        
        
        # Generate random type and set initial size
        pType = np.random.randint(0, constants.PARTICLE_TYPE_COUNT, constants.MAX_PARTICLES)

        # typesAndSizes -> [pType, 2]
        Particles.typesAndSizes = np.column_stack((pType, np.full(constants.MAX_PARTICLES, 2)))


        # # Create a 2D array where each element is [x, 2]
        # Particles.typesAndSizes = np.array([[x, 2] for x in pType])
        

        running = True
        while running:
            # start_time = time.time() # For framerate calculation
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
            fusionCandidate = -1
            Particles.positions, Particles.velocities, fusionCandidate = Particles.updateParticles(inputPos, inputVel, inputTypesAndSizes, Particles.__particleAttractions, Particles.CURRENT_PARTICLE_COUNT)
            
            
            if fusionCandidate >= 0:
                print(f"Fucad {fusionCandidate}")
                print(f"Old Pos {Particles.positions}, curCount {Particles.CURRENT_PARTICLE_COUNT}")
                indices, avgPos, pType, newSize = Particles.detectCloseParticleIndices(fusionCandidate, Particles.positions, inputTypesAndSizes, Particles.CURRENT_PARTICLE_COUNT)
                print(f"pre remove indices {indices} | newSize {newSize}")

                # Commence fusion
                if newSize > 0:
                    print(f"IN NEW")
                    # Remove small particles
                    Particles.positions, Particles.velocities, Particles.typesAndSizes = Particles.removeParticlesByIndices(indices)
                    # print(f"Removed, pos is")
                    for i in Particles.positions:
                          print(i)
                    # Particles.CURRENT_PARTICLE_COUNT -= len(indices)

                    # print(f"Count is {Particles.CURRENT_PARTICLE_COUNT}")
                    # # Add large particle
                    # Particles.positions[Particles.CURRENT_PARTICLE_COUNT] = avgPos
                    # Particles.velocities[Particles.CURRENT_PARTICLE_COUNT] = np.array([0, 0])
                    # Particles.typesAndSizes[Particles.CURRENT_PARTICLE_COUNT] = np.array([pType, newSize])

                    # Particles.CURRENT_PARTICLE_COUNT += 1
                    

            # Draw circle at mouse position
            # self.drawMouseCircle()
            
            Particles.draw()
            
            
            Particles.spawnNewParticle()
            
            pygame.display.flip() # Update display
            
            # Calc framerate
            self.clock.tick(60)  # FPS Limit
            # end_time = time.time()
            # frame_time = end_time - start_time
            # self.frame_times.append(frame_time)
            # if len(self.frame_times) > 70:
            #     self.frame_times.pop(0)
            # self.calculateFramerate()
            
            
            
        # self.performanceMonitor.stop()
        # self.performanceMonitor.join()

        
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
            # self.monitorObjects()

    def monitorCPU(self):
        cpu_percent = self.process.cpu_percent()
        print(f"CPU usage: {cpu_percent}%")
    
    def monitorMemory(self):
        memory_info = self.process.memory_info()
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024)} MB")  # Convert to MB
    
    def stop(self):
        self.stopped.set()
