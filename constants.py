from enum import Enum
import pygame
import time
from collections import defaultdict

# class Constants:
MONITOR_INTERVAL = 2
SCREEN_WIDTH = None
SCREEN_HEIGHT = None

SCREEN = None
    

START_PARTICLES = 700
MAX_PARTICLES = 900
PARTICLE_TYPE_COUNT = 11

MAX_PARTICLE_INFLUENCE = 225
MIN_PARTICLE_INFLUENCE = 35
MIN_PARTICLES_FOR_FUSION = 4
MAX_FUSION_DISTANCE = 5
    
FRICTION = 0.85
K = 0.05
    
    
class displays(Enum):
    MAIN = 0
    SECONDARY = 1
        
DISPLAY = displays.MAIN
    
def mapValue(input, inputMin, inputMax, outputMin, outputMax):
    return outputMin + ((input - inputMin) / (inputMax - inputMin)) * (outputMax - outputMin)
    
    