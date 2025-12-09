import pygame
from player_mvt import Player

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
player= Player(100,100,50,5)
# Main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill("purple")
    player.draw(screen)
    player.move(pygame.key.get_pressed())
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
