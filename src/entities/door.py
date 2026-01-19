from entities.base import GridObject
import pygame
from config.settings import CELL_SIZE, BASE_DIR
import os

class Door(GridObject):
    def __init__(self, game, x, y):
        # Door covers the scaled area (e.g., 2x2)
        from config.settings import MAZE_SCALE_UP
        width = MAZE_SCALE_UP
        height = MAZE_SCALE_UP
        
        super().__init__(x, y, width, height, color=(139, 69, 19))
        self.game = game
        self.texture = None
        
        # Load texture
        try:
             path = os.path.join(BASE_DIR, "assets", "images", "door.png")
             if os.path.exists(path):
                 raw = pygame.image.load(path).convert_alpha()
                 # Scale to full dimensions
                 self.texture = pygame.transform.scale(raw, (int(self.w*CELL_SIZE), int(self.h*CELL_SIZE)))
        except Exception as e:
            print(f"Failed to load Door texture: {e}")

    def update(self, *args, **kwargs):
        pass
        
    def draw(self, screen):
        if self.texture:
            screen.blit(self.texture, (self.x, self.y))
        else:
            super().draw(screen)
