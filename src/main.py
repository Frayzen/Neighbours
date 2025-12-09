import pygame
import os
from levels.loader import load_level
from core.registry import Registry

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
clock = pygame.time.Clock()

# Initialize Registry
Registry.load_environments(os.path.join(os.path.dirname(__file__), 'data', 'environments.json'))

running = True

# Load Level 1
world = load_level(1)

TILE_SIZE = min(SCREEN_WIDTH // world.width, SCREEN_HEIGHT // world.height)
start_x = (SCREEN_WIDTH - (world.width * TILE_SIZE)) // 2
start_y = (SCREEN_HEIGHT - (world.height * TILE_SIZE)) // 2

# Main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    screen.fill("black")

    # Draw World
    for y in range(world.height):
        for x in range(world.width):
            env = world.get_environment(x, y)
            if env:
                rect = pygame.Rect(start_x + x * TILE_SIZE, start_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if env.texture:
                    if env.texture.get_width() != TILE_SIZE or env.texture.get_height() != TILE_SIZE:
                         env.texture = pygame.transform.scale(env.texture, (TILE_SIZE, TILE_SIZE))
                    screen.blit(env.texture, rect)
                else:
                    pygame.draw.rect(screen, env.color, rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
