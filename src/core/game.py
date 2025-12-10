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


class Game:

    def __init__(self):
        pygame.init()
        self._init_display()
        self.clock = pygame.time.Clock()
        
        self._load_resources()
        self._init_level()
        self._calculate_layout()
        self._init_entities()

    def _init_display(self):
        if FULLSCREEN_MODE:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.screen_width, self.screen_height = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen_width, self.screen_height = SCREEN_WIDTH, SCREEN_HEIGHT

    def _load_resources(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        Registry.load_cells(os.path.join(base_dir, 'config', 'environments.json'))

    def _init_level(self):
        self.world = load_level(1)

    def _calculate_layout(self):
        if FULLSCREEN_MODE:
            self.tile_size = min(self.screen_width // self.world.width, self.screen_height // self.world.height)
            self.start_x = (self.screen_width - (self.world.width * self.tile_size)) // 2
            self.start_y = (self.screen_height - (self.world.height * self.tile_size)) // 2
        else:
            self.tile_size = TILE_SIZE
            self.start_x = START_X
            self.start_y = START_Y
        
        self.map_bounds = (
            self.start_x,
            self.start_y,
            self.start_x + self.world.width * self.tile_size,
            self.start_y + self.world.height * self.tile_size
        )

    def _init_entities(self):
        self.gridObjects: List[GridObject] = []
        self.player = Player(
            self.start_x + (self.world.width * self.tile_size) // 2,
            self.start_y + (self.world.height * self.tile_size) // 2,
            1,
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

            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def update(self):
        self.player.move(pygame.key.get_pressed(), self.map_bounds, self.tile_size)

        for obj in self.gridObjects:
            obj.update((self.player.x, self.player.y))
        
        self.handle_input()

    def draw(self):
        self.screen.fill("black")
        self.draw_world()
        self.draw_entities()
        pygame.display.flip()

    def draw_world(self):
        for y in range(self.world.height):
            for x in range(self.world.width):
                cell = self.world.get_cell(x, y)
                if cell:
                    rect = pygame.Rect(
                        self.start_x + x * self.tile_size, 
                        self.start_y + y * self.tile_size, 
                        self.tile_size, 
                        self.tile_size
                    )
                    
                    if cell.texture:
                        if cell.texture.get_width() != self.tile_size or cell.texture.get_height() != self.tile_size:
                            cell.texture = pygame.transform.scale(cell.texture, (self.tile_size, self.tile_size))
                        self.screen.blit(cell.texture, rect)
                    else:
                        pygame.draw.rect(self.screen, cell.color, rect)

    def draw_entities(self):
        self.player.draw(self.screen, self.tile_size)
        for obj in self.gridObjects:
            obj.draw(self.screen, self.tile_size)

    def handle_input(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            min_x, min_y, max_x, max_y = self.map_bounds
            self.gridObjects.append(
                Enemy(
                    randint(min_x, max_x - self.tile_size),
                    randint(min_y, max_y - self.tile_size),
                    1, 
                    1
                )
            )

gameInstance = Game()
