import pygame


class GridObject:

    def __init__(self, x, y, w, h, color="red") -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

    def draw(self, screen, tile_size):
        pygame.draw.rect(
            screen,
            self.color,
            (self.x, self.y, self.w * tile_size, self.h * tile_size),
        )

    def update(self, target_pos=None):
        pass