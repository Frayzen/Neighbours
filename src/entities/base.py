from config.settings import CELL_SIZE
import pygame


class GridObject:

    def __init__(self, x, y, w, h, color="red") -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            (self.x, self.y, self.w * CELL_SIZE, self.h * CELL_SIZE),
        )

    def update(self, target_pos=None):
        pass
