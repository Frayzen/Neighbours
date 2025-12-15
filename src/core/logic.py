import pygame
import random
from random import randint
from entities.enemy import Enemy
from items.item import Item
from items.factory import ItemFactory
from entities.xp_orb import XPOrb
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
        
        self._handle_player_movement()
        self._handle_combat()
        
        # Check for game over (restart)
        if self.game.player.health <= 0:
            self.game.restart_game()
            return

        self._handle_pickups()
        self._handle_spawning_and_drops()

        for obj in self.game.gridObjects:
            obj.update((self.game.player.x, self.game.player.y))
        
        self._handle_input()
        self._handle_debug_input()

    def _handle_player_movement(self):
        result = self.game.player.move(pygame.key.get_pressed(), self.game.map_bounds, self.game.world, self.game.tile_size)
        if result:
            cell, x, y = result
            if cell.trigger:
                execute_trigger(cell.trigger, self.game, x, y)

    def _handle_combat(self):
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

    def _handle_pickups(self):
        # Pickup System (Items & XP)
        pickupables = [obj for obj in self.game.gridObjects if isinstance(obj, (Item, XPOrb))]
        
        # Pre-calculate player center and range squared
        px = self.game.player.x + (self.game.player.w * self.game.tile_size) / 2
        py = self.game.player.y + (self.game.player.h * self.game.tile_size) / 2
        pickup_range_sq = self.game.player.pickup_range ** 2
        
        player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * self.game.tile_size, self.game.player.h * self.game.tile_size)
        
        for obj in pickupables:
            # Magnet Logic (Optimized)
            ox = obj.x + (obj.w * self.game.tile_size)/2
            oy = obj.y + (obj.h * self.game.tile_size)/2
            
            dx = ox - px
            dy = oy - py
            dist_sq = dx*dx + dy*dy
            
            if dist_sq <= pickup_range_sq:
                if hasattr(obj, 'move_towards'):
                    obj.move_towards(self.game.player.x, self.game.player.y)
            
            # Collision/Collection Logic
            # Optimization: Only check collision if close enough (e.g. < 2 tiles)
            if dist_sq < (self.game.tile_size * 2) ** 2:
                obj_rect = pygame.Rect(obj.x, obj.y, obj.w * self.game.tile_size, obj.h * self.game.tile_size)
                if player_rect.colliderect(obj_rect):
                    if isinstance(obj, Item):
                        self.game.player.collect_item(obj)
                    elif isinstance(obj, XPOrb):
                        self.game.player.gain_xp(obj.value)
                    
                    if obj in self.game.gridObjects: # Check existence to avoid double removal
                        self.game.gridObjects.remove(obj)

    def _handle_spawning_and_drops(self):
        # Remove dead enemies and Drop System
        dead_enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy) and obj.health <= 0]
        for enemy in dead_enemies:
            # Drop XP
            xp_orb = XPOrb(enemy.x, enemy.y, enemy.xp_value)
            self.game.gridObjects.append(xp_orb)

            # Apply luck to drop chance
            current_drop_chance = GLOBAL_DROP_CHANCE * self.game.player.luck_mult
            
            if random.random() < current_drop_chance:
                # Pass luck to item factory for better rarity chances
                item = ItemFactory.create_random_item(enemy.x, enemy.y, luck=self.game.player.luck_mult)
                if item:
                    self.game.gridObjects.append(item)
                    debug.log(f"Item dropped: {item.name}")
            self.game.gridObjects.remove(enemy)

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
