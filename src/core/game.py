from typing import List
import pygame
import os
from random import randint, randrange

from config.settings import *
from entities.enemy import Enemy
from entities.base import GridObject
from entities.player import Player
from levels.loader import load_level
from core.registry import Registry
from core.triggers import execute_trigger
from core.debug import debug


class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up the display
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width, self.screen_height = self.screen.get_size()
        self.clock = pygame.time.Clock()

        # Initialize Registry
        # Go up one level from core/ to src/ then to config/environments.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        Registry.load_environments(os.path.join(base_dir, 'config', 'environments.json'))

        # Load Level 1
        self.world = load_level(1)

        # Calculate Tile Size and Offsets to center the map
        self.tile_size = min(self.screen_width // self.world.width, self.screen_height // self.world.height)
        self.start_x = (self.screen_width - (self.world.width * self.tile_size)) // 2
        self.start_y = (self.screen_height - (self.world.height * self.tile_size)) // 2
        
        # Define Map Bounds (min_x, min_y, max_x, max_y)
        self.map_bounds = (
            self.start_x,
            self.start_y,
            self.start_x + self.world.width * self.tile_size,
            self.start_y + self.world.height * self.tile_size
        )

        self.gridObjects: List[GridObject] = []
        # Start player in the middle of the map
        self.player = Player(
            self.start_x + (self.world.width * self.tile_size) // 2,
            self.start_y + (self.world.height * self.tile_size) // 2,
            self.tile_size, # Player size matches tile size
            5
        )

    def run(self):
        running = True
        # Main game loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.screen.fill("black")

            # Draw World
            for y in range(self.world.height):
                for x in range(self.world.width):
                    # Get environment and offset
                    cell_data = self.world.get_environment_full(x, y)
                    if cell_data:
                        env, offset = cell_data
                        
                        # Only draw if it's the origin (0,0)
                        if offset == (0, 0):
                            rect = pygame.Rect(
                                self.start_x + x * self.tile_size, 
                                self.start_y + y * self.tile_size, 
                                self.tile_size * env.width, 
                                self.tile_size * env.height
                            )
                            
                            if env.texture:
                                # Scale texture if needed (assuming texture is full size of object)
                                target_size = (self.tile_size * env.width, self.tile_size * env.height)
                                if env.texture.get_size() != target_size:
                                     env.texture = pygame.transform.scale(env.texture, target_size)
                                self.screen.blit(env.texture, rect)
                            else:
                                pygame.draw.rect(self.screen, env.color, rect)

            # Draw Player and Objects
            self.player.draw(self.screen)
            trigger_data = self.player.move(pygame.key.get_pressed(), self.map_bounds, self.world, self.tile_size)
            
            if trigger_data:
                env, grid_x, grid_y = trigger_data
                if env.trigger:
                    execute_trigger(env.trigger, self, grid_x, grid_y)

            for obj in self.gridObjects:
                obj.draw(self.screen)
                obj.update((self.player.x, self.player.y))

            # Draw Debug Overlay
            debug.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)
            self.handleEvents()
        pygame.quit()

    def handleEvents(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            min_x, min_y, max_x, max_y = self.map_bounds
            self.gridObjects.append(
                Enemy(
                    randint(min_x, max_x - self.tile_size),
                    randint(min_y, max_y - self.tile_size),
                    self.tile_size, 
                    self.tile_size
                )
            )

gameInstance = Game()
