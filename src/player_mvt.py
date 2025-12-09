#0 at the top left corner of the screen
#moving a cube smothly using arrow
import pygame
# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 1280, 720

class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def move(self, keys): #movement using arrow keys 
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed

        # Keep cube inside the screen
        self.x = max(0, min(self.x, WIDTH - self.size))
        self.y = max(0, min(self.y, HEIGHT - self.size))

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.size, self.size))

    
# Create cube object in the center of the screen
cube = Player(100, 100, 50, 5)
cube.move(pygame.key.get_pressed())

# Font for “0”
font = pygame.font.SysFont(None, 40)

# Draw "0" in top-left
text = font.render("0", True, (255, 255, 255))
