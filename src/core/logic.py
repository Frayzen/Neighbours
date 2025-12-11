import pygame
from random import randint
from entities.enemy import Enemy
from core.debug import debug
from core.triggers import execute_trigger
from core.vfx import vfx_manager

class GameLogic:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.game.player.combat.switch_weapon()

    def update(self):
        vfx_manager.update()
        result = self.game.player.move(pygame.key.get_pressed(), self.game.map_bounds, self.game.world, self.game.tile_size)

        
        if result:
            cell, x, y = result
            if cell.trigger:
                execute_trigger(cell.trigger, self.game, x, y)

        # Update player combat logic
        # Filter enemies from gridObjects
        enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
        self.game.player.update(enemies)

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
            debug.log("Spawned Enemy")
