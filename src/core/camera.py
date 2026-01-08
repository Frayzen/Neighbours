import pygame
from config.settings import (
    GRID_WIDTH_PIX,
    SCREEN_WIDTH_PIX,
    GRID_HEIGHT_PIX,
    SCREEN_HEIGHT_PIX,
)
from entities.player import Player


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, player: Player):
        self.x = player.x - SCREEN_WIDTH_PIX // 2
        self.y = player.y - SCREEN_HEIGHT_PIX // 2
        self.x = max(min(GRID_WIDTH_PIX - SCREEN_WIDTH_PIX, self.x), 0)
        self.y = max(min(GRID_HEIGHT_PIX - SCREEN_HEIGHT_PIX, self.y), 0)

    def get_subregion(self):
        return pygame.Rect(self.x, self.y, GRID_WIDTH_PIX, GRID_HEIGHT_PIX)
