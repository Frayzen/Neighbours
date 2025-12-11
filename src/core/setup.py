from levels.loader import WorldLoader
import pygame
import os
from typing import List

from config.settings import GRID_HEIGHT, GRID_WIDTH, SCREEN_WIDTH, SCREEN_HEIGHT
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
        self.game.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _load_resources(self):
        # Go up one level from core/ to src/ then to config/environments.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        Registry.load_cells(os.path.join(base_dir, "config", "environments.json"))

    def _init_level(self):
        self.game.world = WorldLoader().generate()

    def _init_entities(self):
        self.game.gridObjects = []
        self.game.player = Player(
            GRID_WIDTH // 2,
            GRID_HEIGHT // 2,
            1,
            5,
        )
