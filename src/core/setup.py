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

        # Preload all textures
        Registry.preload_textures(BASE_DIR)

    def _init_level(self):
        self.world_loader = WorldLoader()
        level_config = self.game.level_manager.get_current_level()
        print(f"DEBUG: Generating initial level: {level_config}")
        self.game.world = self.world_loader.generate(level_config)

    def _init_entities(self):
        self.game.gridObjects = []
        # Create new player
        self._spawn_player(create_new=True)

    def respawn_player(self):
        # Keep existing player, only move them
        self.game.gridObjects = []  # Clear old entities
        self.game.gridObjects.append(self.game.player)  # Add player back
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
                print(
                    f"WARNING: Spawn point ({center_x}, {center_y}) is {cell}. searching for neighbor..."
                )
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
                        if found:
                            break
                    if found:
                        break

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

        # Initialize Spawners from World Data
        from entities.spawner import Spawner
        
        for sp in self.game.world.spawn_points:
            # Check if this marker is meant for a Spawner Entity
            if sp.get('type') == 'spawner_entity':
                spawner = Spawner(self.game, sp['x'] * CELL_SIZE, sp['y'] * CELL_SIZE)
                self.game.gridObjects.append(spawner)
            else:
                # Legacy / Manual handling (JSON Levels)
                # Create a Spawner that immediately triggers with fixed enemies
                # This ensures consistent logic but respects the map design
                count = sp.get('enemy_count', 1)
                etype = sp.get('type', 'basic_enemy')
                
                # If specific enemy (e.g. Boss), we want it to spawn immediately or when player is near.
                # Spawner with trigger distance handles "when near".
                # For Boss, trigger distance might need to be large or 0 (auto)? 
                # Let's use standard distance for now.
                
                fixed_wave = [etype] * count
                spawner = Spawner(self.game, sp['x'] * CELL_SIZE, sp['y'] * CELL_SIZE, trigger_distance=10, fixed_wave=fixed_wave)
                self.game.gridObjects.append(spawner)
                
                # If "spawned" was true in save/logic, we'd skip? 
                # But typically loader resets this.
                
        # Clear spawn_points so we don't re-process or confuse logic
        # self.game.world.spawn_points = []
