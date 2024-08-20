import constants
from constants import Constants
from particles import Particles
from quadtree import Quadtree, Rectangle
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

            self.JSONFileSelected = -1
            self.arrowKeyMappings = [
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_RIGHT,
                pygame.K_LEFT
            ]

            self.frame_times = []
            self.frame_print_time = time.time()

            self.performanceMonitor = PerformanceMonitor(constants.MONITOR_INTERVAL) # Interval in seconds
            self.performanceMonitor.start()

            # # Event to handle killing thread on program end
            # self.velThreadStopEvent = threading.Event()

    @staticmethod
    def get_instance():
        # Static method to get the singleton instance
        if Simulation.__instance is None:
            Simulation.__instance = Simulation()
        return Simulation.__instance
    
    @staticmethod          
    def getAttractionsFromJson(directory):
        # List files in the directory
        files = os.listdir(directory)
        fileList = []

        # Check if there is exactly one file
        for i in range(len(files)):
            if files[i] == 'LoadDir':
                continue

            fileList.append(files[i])
        
        return fileList
    
    @staticmethod
    def loadAttractionsFromJSON(filePath):
        if not os.path.exists(filePath):
            raise FileNotFoundError(f"No such file: '{filePath}'")
        
        # Read the JSON file
        with open(filePath, 'r') as json_file:
            data = json.load(json_file)
        
        # Convert
        array = np.array(data)
        
        return array
    
    @staticmethod
    def saveAttractionsToJSON():
        # Save forces array to new JSON file
        jsonList = Particles.__particleAttractions.tolist()
                    
        # Time based UUID
        id = uuid.uuid1()

        # Define the directory and file path
        attractionsDir = 'SavedAttractions'
        typeDir = f'{constants.PARTICLE_TYPE_COUNT}Types'
        fullDir = os.path.join(attractionsDir, typeDir)

        # Ensure the directory exists
        os.makedirs(fullDir, exist_ok=True)

        file_path = os.path.join(fullDir, f'{id}.json')

        # Write to the JSON file
        with open(file_path, 'w') as json_file:
            # data = {"example": "data"}  # Replace this with your actual data
            json.dump(jsonList, json_file)

            print(f"Data saved to {file_path}")


    # Handle numkey press (load saved attraction values)
    def handleNumkeyPress(self, key):
        if key in self.numberKeyMappings:
            self.loadSaveFromLoadDir(self.numberKeyMappings[key])
        else:
            print(f"Invalid key: {key}")
    
    def handleArrowKeyPress(self, key):
        if key not in self.arrowKeyMappings:
            print(f"Invalid key {key} OBSOLETE")
            return
        
        
        directory = f'SavedAttractions/{constants.PARTICLE_TYPE_COUNT}Types'
        saveFiles = self.getAttractionsFromJson(directory)


        if key == pygame.K_RIGHT or key == pygame.K_UP:
            self.JSONFileSelected += 1
        else:
            self.JSONFileSelected -= 1

        if self.JSONFileSelected < 0:
            self.JSONFileSelected = 0

        index = self.JSONFileSelected % len(saveFiles)

        loadFile = os.path.join(directory, saveFiles[index])

        Particles.__particleAttractions = self.loadAttractionsFromJSON(loadFile)


        
    def loadSaveFromLoadDir(self, index):
        directory = f'SavedAttractions/{constants.PARTICLE_TYPE_COUNT}Types/LoadDir'
        saveFiles = self.getAttractionsFromJson(directory)

        if index >= len(saveFiles):
            return
        
        loadFile = os.path.join(directory, saveFiles[index])

        loadAttractions = self.loadAttractionsFromJSON(loadFile)

        Particles.__particleAttractions = loadAttractions

        


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

        
        Constants.PARTICLE_QUADTREE = Quadtree(Rectangle(0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        Constants.PARTICLE_QUADTREE.batchInsert(Particles.positions)

        self.quadtreeUpdator = QuadtreeUpdator()
        self.quadtreeUpdator.start()

        # Event to handle killing thread on program end
        # self.velThreadStopEvent = threading.Event()

        running = True
        while running:
            start_time = time.time() # For framerate calculation
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        Particles.__particleAttractions = Particles.setAttractions()
                    elif event.key == pygame.K_s:
                        self.saveAttractionsToJSON()

                    # Load saved values
                    elif event.key in self.numberKeyMappings:
                        self.handleNumkeyPress(event.key)
                    
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_UP:
                        self.handleArrowKeyPress(event.key)
                        


            constants.SCREEN.fill((0, 0, 0))  # Clear the screen
            
            inputPos, inputVel, inputTypesAndSizes = Particles.getParticleInfo()
            fusionCandidate, fissionPosition, fissionType, fissionQuantity = Particles.updateParticles(inputPos, inputVel, inputTypesAndSizes, Particles.splitTimers, Particles.__particleAttractions, Particles.CURRENT_PARTICLE_COUNT)
            
            if fusionCandidate >= 0:
                indices, avgPos, newSize = Particles.detectFusionIndices(fusionCandidate, Particles.positions, inputTypesAndSizes, Particles.CURRENT_PARTICLE_COUNT)

                # Commence fusion
                if newSize > 0:

                    # Remove small particles
                    newPos, newVel, newTypesAndSizes, newSplitTimers, pType = Particles.removeParticlesForFusion(indices)
                    

                    Particles.positions, Particles.velocities, Particles.typesAndSizes, Particles.splitTimers = newPos, newVel, newTypesAndSizes, newSplitTimers


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

            # # Update quadtree
            # quadStart = time.time()
            # Constants.PARTICLE_QUADTREE.clear()
            # Constants.PARTICLE_QUADTREE.batchInsert(Particles.positions)

            # quadEnd = time.time()
            # print(f"Quad updated in {quadEnd - quadStart} s")

            
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
        self.quadtreeUpdator.stop()
        self.quadtreeUpdator.join()

        
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
            

class QuadtreeUpdator(threading.Thread):
    def __init__(self, interval=0):
        super().__init__()
        self.stopped = threading.Event()
        self.process = psutil.Process()
        self.daemon = True # Exit thread upon game quit
        self.interval = interval
        self.activeBuffer = -1
        self.updates = []
        Constants.PARTICLE_QUADTREE_DOUBLE_BUFFER = []
    
    def run(self):
        # Lower thread priority
        self.process.nice(psutil.IDLE_PRIORITY_CLASS)


        frameCount = 0
            
        while not self.stopped.wait(self.interval):
            self.updateParticleQuadtree()
            if frameCount % 5 == 0:  # Update every 5 frames
                self.updateParticleQuadtree()
            frameCount += 1
            time.sleep(0.05)
    
    def updateParticleQuadtree(self):
        # Update quadtree
        quadStart = time.time()
        Constants.PARTICLE_QUADTREE.clear()
        Constants.PARTICLE_QUADTREE.batchInsert(Particles.positions)

        quadEnd = time.time()
        # print(f"Quad updated in {quadEnd - quadStart} s")
        self.updates.append(quadEnd)

        # Report average time for n updates
        if len(self.updates) == 10:
            print(f"Time for {len(self.updates)} quadtree updates: {self.updates[len(self.updates)-1] - self.updates[0]} s")
            self.updates = []
        time.sleep(0)

    def stop(self):
        self.stopped.set()


    
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
