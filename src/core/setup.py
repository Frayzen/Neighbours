import pygame
import os
from typing import List

from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BASE_DIR, PLAYER_SIZE, PLAYER_SPEED
from core.registry import Registry
from levels.loader import load_level
from entities.base import GridObject
from entities.player import Player
"""Florian LAINE"""

class GameSetup:
    def __init__(self, game):
        self.game = game

    def perform_setup(self):
        self._init_display()
        self.game.clock = pygame.time.Clock()
        self._load_resources()
        self._init_level()
        self._calculate_layout()
        self._init_entities()

    def _init_display(self):
        self.game.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game.screen_width, self.game.screen_height = SCREEN_WIDTH, SCREEN_HEIGHT

    def _load_resources(self):
        Registry.load_cells(os.path.join(BASE_DIR, 'config', 'environments.json'))
        Registry.load_enemies(os.path.join(BASE_DIR, 'config', 'enemies.json'))

    def _init_level(self):
        self.game.world = load_level(1)

    def _calculate_layout(self):
        self.game.tile_size = min(self.game.screen_width // self.game.world.width, self.game.screen_height // self.game.world.height)
        self.game.start_x = (self.game.screen_width - (self.game.world.width * self.game.tile_size)) // 2
        self.game.start_y = (self.game.screen_height - (self.game.world.height * self.game.tile_size)) // 2
        
        self.game.map_bounds = (
            self.game.start_x,
            self.game.start_y,
            self.game.start_x + self.game.world.width * self.game.tile_size,
            self.game.start_y + self.game.world.height * self.game.tile_size
        )

    def _init_entities(self):
        self.game.gridObjects = []
        self.game.player = Player(
            self.game,
            self.game.start_x + (self.game.world.width * self.game.tile_size) // 2,
            self.game.start_y + (self.game.world.height * self.game.tile_size) // 2,
            PLAYER_SIZE, # Player size matches tile size
            PLAYER_SPEED
        )
