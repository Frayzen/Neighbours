import pygame
import random
from random import randint
from entities.enemy import Enemy
from items.item import Item
from items.factory import ItemFactory
from config.settings import GLOBAL_DROP_CHANCE
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

        # Check for collisions between player and enemies
        player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * self.game.tile_size, self.game.player.h * self.game.tile_size)
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w * self.game.tile_size, enemy.h * self.game.tile_size)
            if player_rect.colliderect(enemy_rect):
                self.game.player.take_damage(enemy.damage)

        # Item Pickup System
        items = [obj for obj in self.game.gridObjects if isinstance(obj, Item)]
        for item in items:
            item_rect = pygame.Rect(item.x, item.y, item.w * self.game.tile_size, item.h * self.game.tile_size)
            if player_rect.colliderect(item_rect):
                self.game.player.collect_item(item)
                self.game.gridObjects.remove(item)

        # Remove dead enemies and Drop System
        dead_enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy) and obj.health <= 0]
        for enemy in dead_enemies:
            # Apply luck to drop chance
            current_drop_chance = GLOBAL_DROP_CHANCE * self.game.player.luck_mult
            
            if random.random() < current_drop_chance:
                # Pass luck to item factory for better rarity chances
                item = ItemFactory.create_random_item(enemy.x, enemy.y, luck=self.game.player.luck_mult)
                if item:
                    self.game.gridObjects.append(item)
                    debug.log(f"Item dropped: {item.name}")
            self.game.gridObjects.remove(enemy)

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
            self.game.gridObjects.append(
                Enemy(
                    randint(min_x, max_x - self.game.tile_size),
                    randint(min_y, max_y - self.game.tile_size),
                    1, 
                    1
                )
            )
            debug.log("Spawned Enemy")
