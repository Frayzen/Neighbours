from random import randint
from levels.loader import WorldLoader
import pygame
import os
from typing import List

from config.settings import (
    CELL_SIZE,
    GRID_HEIGHT,
    GRID_WIDTH,
    SCREEN_WIDTH_PIX,
    SCREEN_HEIGHT_PIX,
)
from config.settings import (
    BASE_DIR,
    PLAYER_SIZE,
    PLAYER_SPEED,
)
from core.registry import Registry
from entities.base import GridObject
from entities.player import Player


class GameSetup:
    def __init__(self, game):
        self.game = game

    def perform_setup(self):
        self._init_display()
        self.game.clock = pygame.time.Clock()
        self._load_resources()
        self._init_level()
        self._init_entities()

    def _init_display(self):
        self.game.screen = pygame.display.set_mode(
            (SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX)
        )

    def _load_resources(self):
        Registry.load_cells(os.path.join(BASE_DIR, "config", "environments.json"))
        Registry.load_enemies(os.path.join(BASE_DIR, "config", "enemies.json"))

    def _init_level(self):
        self.world_loader = WorldLoader()
        self.game.world = self.world_loader.generate()

    def _init_entities(self):
        self.game.gridObjects = []
        rooms = self.world_loader.rooms
        spawn_room = rooms[randint(0, len(rooms) - 1)]
        # INDEX FOR CLARITY
        MINX, MINY, HEIGHT, WIDTH = (0, 1, 2, 3)
        room_mid = [
            spawn_room[MINX] + spawn_room[HEIGHT] // 2,
            spawn_room[MINY] + spawn_room[WIDTH] // 2,
        ]
        self.game.player = Player(
            self.game,
            room_mid[0] * CELL_SIZE,
            room_mid[1] * CELL_SIZE,
            PLAYER_SIZE,  # Player size matches tile size
            PLAYER_SPEED,
        )
