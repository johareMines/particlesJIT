from enum import Enum
import pygame
import time
from collections import defaultdict

# class Constants:
MONITOR_INTERVAL = 2
SCREEN_WIDTH = None
SCREEN_HEIGHT = None

SCREEN = None
    

START_PARTICLES = 800
MAX_PARTICLES = 2000

MAX_PARTICLE_INFLUENCE = 250
MIN_PARTICLE_INFLUENCE = 65
    
FRICTION = 0.85
K = 0.05
    
    
class displays(Enum):
    MAIN = 0
    SECONDARY = 1
        
DISPLAY = displays.MAIN
    
def mapValue(input, inputMin, inputMax, outputMin, outputMax):
    return outputMin + ((input - inputMin) / (inputMax - inputMin)) * (outputMax - outputMin)
    
    