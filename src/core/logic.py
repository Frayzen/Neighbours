import pygame
from random import randint
from entities.enemy import Enemy

class GameLogic:
    def __init__(self, game):
        self.game = game

    def update(self):
        self.game.player.move(pygame.key.get_pressed(), self.game.map_bounds, self.game.world, self.game.tile_size)

        for obj in self.game.gridObjects:
            obj.update((self.game.player.x, self.game.player.y))
        
        self._handle_input()

    def _handle_input(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            min_x, min_y, max_x, max_y = self.game.map_bounds
            self.game.gridObjects.append(
                Enemy(
                    randint(min_x, max_x - self.game.tile_size),
                    randint(min_y, max_y - self.game.tile_size),
                    1, 
                    1
                )
            )
