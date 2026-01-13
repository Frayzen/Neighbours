from random import randint, choice
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
from entities.enemy import Enemy


class GameSetup:
    def __init__(self, game):
        self.game = game

    def perform_setup(self):
        if not self.game.headless:
            self._init_display()
        
        self.game.clock = pygame.time.Clock()
        self._load_resources()
        self._init_level()
        self._init_entities()

    def _init_display(self):
        if self.game.headless: return
        self.game.screen = pygame.display.set_mode(
            (SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX)
        )

    def _load_resources(self):
        Registry.load_cells(os.path.join(BASE_DIR, "config", "environments.json"))
        Registry.load_enemies(os.path.join(BASE_DIR, "config", "enemies.json"))
        
        # Preload all textures ONLY if not headless
        if not self.game.headless:
            Registry.preload_textures(BASE_DIR)

    def _init_level(self):
        self.world_loader = WorldLoader()
        self.game.world = self.world_loader.generate()

    def _init_entities(self):
        self.game.gridObjects = []
        # Create new player
        self._spawn_player(create_new=True)

    def respawn_player(self):
        # Keep existing player, only move them
        self.game.gridObjects = [] # Clear old entities
        self.game.gridObjects.append(self.game.player) # Add player back
        self._spawn_player(create_new=False)

    def _spawn_player(self, create_new=True):
        rooms = self.world_loader.rooms
        if not rooms:
             print("ERROR: No rooms found! Spawning at (1,1)")
             spawn_x, spawn_y = CELL_SIZE, CELL_SIZE
        else:
            spawn_room = rooms[randint(0, len(rooms) - 1)]
            
            # Use explicit indices for clarity: (x, y, width, height)
            rx, ry, rw, rh = spawn_room
            
            # Calculate center
            center_x = rx + rw // 2
            center_y = ry + rh // 2
            
            # Verify walkability (Safety Check)
            cell = self.game.world.get_cell(center_x, center_y)
            if not cell or not cell.walkable:
                 print(f"WARNING: Spawn point ({center_x}, {center_y}) is {cell}. searching for neighbor...")
                 # Spiral search for walkable
                 found = False
                 for radius in range(1, 5):
                     for dy in range(-radius, radius + 1):
                         for dx in range(-radius, radius + 1):
                             nx, ny = center_x + dx, center_y + dy
                             ncell = self.game.world.get_cell(nx, ny)
                             if ncell and ncell.walkable:
                                 center_x, center_y = nx, ny
                                 found = True
                                 break
                         if found: break
                     if found: break
                 
                 if not found:
                     print("CRITICAL: Could not find walkable spawn in room!")
            
            spawn_x = center_x * CELL_SIZE
            spawn_y = center_y * CELL_SIZE

        if create_new:
            self.game.player = Player(
                self.game,
                spawn_x,
                spawn_y,
                PLAYER_SIZE,
                PLAYER_SPEED,
            )
            self.game.gridObjects.append(self.game.player)
        else:
            self.game.player.x = spawn_x
            self.game.player.y = spawn_y
        
        # Enemies will now be spawned by the Logic system based on proximity using self.game.world.spawn_points
        # (Current logic relies on update loop to populate enemies)
