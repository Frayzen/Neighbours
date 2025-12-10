#0 at the top left corner of the screen
#moving a cube smothly using arrow
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

    def move(self, keys, bounds, world, tile_size): #movement using arrow keys or WASD
#pygame.K_ DIRECTION is used to detect key presses on this precise touch
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

        # Try moving X
        new_x = self.x + dx
        if not self.check_collision(new_x, self.y, bounds, world, tile_size):
            self.x = new_x

        # Try moving Y
        new_y = self.y + dy
        if not self.check_collision(self.x, new_y, bounds, world, tile_size):
            self.y = new_y

    def check_collision(self, x, y, bounds, world, tile_size):
        min_x, min_y, max_x, max_y = bounds
        
        # Constrain to bounds first
        if x < min_x or x > max_x - self.size:
            return True
        if y < min_y or y > max_y - self.size:
            return True

        # Check corners against world grid
        corners = [
            (x, y),
            (x + self.size - 0.1, y),
            (x, y + self.size - 0.1),
            (x + self.size - 0.1, y + self.size - 0.1)
        ]

        for cx, cy in corners:
            grid_x = int((cx - min_x) / tile_size)
            grid_y = int((cy - min_y) / tile_size)
            
            env = world.get_environment(grid_x, grid_y)
            if env and not env.walkable:
                return True
        
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.size, self.size))

    