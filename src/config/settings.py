import os

CELL_SIZE = 8
GRID_WIDTH = 100
GRID_HEIGHT = 100
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

MAX_WEAPONS = 3

FPS = 60
TARGET_CHECK_INTERVAL = 500

# Base directory of the project (src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

