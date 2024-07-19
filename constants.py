from enum import Enum
import pygame
import time
from collections import defaultdict

# class Constants:
MONITOR_INTERVAL = 2
SCREEN_WIDTH = None
SCREEN_HEIGHT = None

SCREEN = None
    

START_PARTICLES = 1500
MAX_PARTICLES = 2000
    
    
FRICTION = 0.85
    
    
class displays(Enum):
    MAIN = 0
    SECONDARY = 1
        
DISPLAY = displays.MAIN
    
def mapValue(input, inputMin, inputMax, outputMin, outputMax):
    return outputMin + ((input - inputMin) / (inputMax - inputMin)) * (outputMax - outputMin)
    
    