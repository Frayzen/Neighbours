import os

CELL_SIZE = 8
GRID_WIDTH = 100
GRID_HEIGHT = 100
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

MAX_WEAPONS = 3

FPS = 60
TARGET_CHECK_INTERVAL = 500

# Colors
COLOR_BACKGROUND = "black"
COLOR_PLAYER = (255, 255, 255)
COLOR_ENEMY = "red"

# Player Settings
PLAYER_SPEED = 5
PLAYER_SIZE = 1

# Enemy Settings
ENEMY_SPEED = 0.5
ENEMY_HEALTH = 100

# Base directory of the project (src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

