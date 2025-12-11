# 0 at the top left corner of the screen
# moving a cube smothly using arrow
from typing import Tuple
import pygame

# Initialize Pygame
pygame.init()

# Set up the display
from config.settings import (
    CELL_SIZE,
    GRID_HEIGHT,
    GRID_WIDTH,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def move(self, keys, world):  # movement using arrow keys or WASD
        # pygame.K_ DIRECTION is used to detect key presses on this precise touch
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed

        bounds = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Try moving X
        new_x = self.x + dx
        collision_x = self.check_collision(new_x, self.y, bounds, world, CELL_SIZE)
        if not collision_x:
            self.x = new_x
        elif isinstance(collision_x, tuple):
            return collision_x

        # Try moving Y
        new_y = self.y + dy
        collision_y = self.check_collision(self.x, new_y, bounds, world, CELL_SIZE)
        if not collision_y:
            self.y = new_y
        elif isinstance(collision_y, tuple):
            return collision_y

        return None

    def check_collision(self, x, y, bounds, world, CELL_SIZE):
        min_x, min_y, max_x, max_y = bounds

        pixel_size = self.size * CELL_SIZE

        # Constrain to bounds first
        if x < min_x or x > max_x - pixel_size:
            return True
        if y < min_y or y > max_y - pixel_size:
            return True

        # Check corners against world grid
        corners = [
            (x, y),
            (x + pixel_size - 0.1, y),
            (x, y + pixel_size - 0.1),
            (x + pixel_size - 0.1, y + pixel_size - 0.1),
        ]

        for cx, cy in corners:
            grid_x = int((cx - min_x) / CELL_SIZE)
            grid_y = int((cy - min_y) / CELL_SIZE)

            cell_data = world.get_cell_full(grid_x, grid_y)
            if cell_data:
                cell, offset = cell_data
                if not cell.walkable:
                    # Return cell and its origin grid coordinates
                    origin_x = grid_x - offset[0]
                    origin_y = grid_y - offset[1]
                    return (cell, origin_x, origin_y)

        return False

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (self.x, self.y, self.size * CELL_SIZE, self.size * CELL_SIZE),
        )
