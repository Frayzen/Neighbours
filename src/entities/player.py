#0 at the top left corner of the screen
#moving a cube smothly using arrow
from typing import Tuple
import pygame
# Initialize Pygame
pygame.init()

# Set up the display
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def move(self, keys, bounds: Tuple[int, int, int, int], tile_size: int): #movement using arrow keys or WASD
#pygame.K_ DIRECTION is used to detect key presses on this precise touch
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed

        # Keep cube inside the bounds
        # bounds is a tuple (min_x, min_y, max_x, max_y)
        min_x, min_y, max_x, max_y = bounds
        pixel_size = self.size * tile_size
        self.x = max(min_x, min(self.x, max_x - pixel_size))
        self.y = max(min_y, min(self.y, max_y - pixel_size))

    def draw(self, surface, tile_size):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.size * tile_size, self.size * tile_size))

    