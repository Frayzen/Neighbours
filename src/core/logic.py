import pygame
from random import randint, choice
from entities.enemy import Enemy
from core.debug import debug
from core.triggers import execute_trigger
from core.vfx import vfx_manager
from core.registry import Registry

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

        # Check for collisions between player and enemies
        player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * self.game.tile_size, self.game.player.h * self.game.tile_size)
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w * self.game.tile_size, enemy.h * self.game.tile_size)
            if player_rect.colliderect(enemy_rect):
                self.game.player.take_damage(enemy.damage)

        # Remove dead enemies
        self.game.gridObjects = [obj for obj in self.game.gridObjects if not (isinstance(obj, Enemy) and obj.health <= 0)]

        for obj in self.game.gridObjects:
            obj.update((self.game.player.x, self.game.player.y))
        
        self._handle_input()
        self._handle_debug_input()

    def _handle_input(self):
        pass

    def _handle_debug_input(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            min_x, min_y, max_x, max_y = self.game.map_bounds
            enemy_types = Registry.get_enemy_types()
            if enemy_types:
                enemy_type = choice(enemy_types)
                self.game.gridObjects.append(
                    Enemy(
                        self.game,
                        randint(min_x, max_x - self.game.tile_size),
                        randint(min_y, max_y - self.game.tile_size),
                        enemy_type=enemy_type
                    )
                )
                debug.log(f"Spawned {enemy_type}")
