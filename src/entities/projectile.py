import pygame
from entities.base import GridObject
from config.settings import CELL_SIZE

class Projectile(GridObject):
    def __init__(self, x, y, direction, speed, damage, owner_type, texture=None):
        super().__init__(x, y, 0.5, 0.5, color=(255, 255, 0)) # Default small yellow square
        self.direction = pygame.math.Vector2(direction).normalize()
        self.speed = speed
        self.damage = damage
        self.owner_type = owner_type # "player" or "enemy"
        self.texture = texture
        
        # Determine rotation if texture exists
        if self.texture:
            angle = self.direction.angle_to(pygame.math.Vector2(1, 0))
            self.texture = pygame.transform.rotate(self.texture, angle)

    def update(self):
        self.x += self.direction.x * self.speed
        self.y += self.direction.y * self.speed

    def draw(self, screen):
        if self.texture:
             # Scale if needed? For now assume texture is size appropriate or pre-scaled
             # Centering logic
             dest_rect = self.texture.get_rect(center=(self.x + (self.w*CELL_SIZE)/2, self.y + (self.h*CELL_SIZE)/2))
             screen.blit(self.texture, dest_rect)
        else:
            # Draw simple circle or rect
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 4)
