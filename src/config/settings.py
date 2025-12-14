import os

CELL_SIZE = 8
GRID_WIDTH = 100
GRID_HEIGHT = 100
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

MAX_WEAPONS = 3

FPS = 60
TARGET_CHECK_INTERVAL = 500
DEBUG_MODE = True

# Colors
COLOR_BACKGROUND = "black"
COLOR_PLAYER = (255, 255, 255)
COLOR_ENEMY = "red"
COLOR_HEALTH_BAR_BG = (255, 0, 0)
COLOR_HEALTH_BAR_FG = (0, 255, 0)
COLOR_HEALTH_BAR_BORDER = (255, 255, 255)

# Player Settings
PLAYER_SPEED = 5
PLAYER_SIZE = 1
PLAYER_MAX_HEALTH = 100
PLAYER_INVULNERABILITY_DURATION = 1000

# Enemy Settings
ENEMY_SPEED = 0.5
ENEMY_HEALTH = 100
ENEMY_DAMAGE = 10

# UI Settings
UI_HEALTH_BAR_WIDTH = 200
UI_HEALTH_BAR_HEIGHT = 20
UI_HEALTH_BAR_X = 10
UI_HEALTH_BAR_Y = 10

# Base directory of the project (src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Item Settings
GLOBAL_DROP_CHANCE = 0.3

RARITY_WEIGHTS = {
    "common": 70,
    "rare": 25,
    "legendary": 5
}

RARITY_SCALING = {
    "common": 1.0,
    "rare": 1.5,
    "legendary": 3.0
}

COLOR_RARITY = {
    "common": (128, 128, 128),  # Grey
    "rare": (0, 0, 255),        # Blue
    "legendary": (255, 165, 0)  # Orange
}
