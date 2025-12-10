import pygame

from config.settings import CELL_SIZE


class GridObject:

    def __init__(self, x, y, w, h) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            "red",
            (self.x, self.y, self.w, self.h),
        )

    def update(self):
        pass
