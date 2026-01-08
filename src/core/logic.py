import pygame
import random
from random import randint, choice
from entities.enemy import Enemy
from items.item import Item
from items.factory import ItemFactory
from entities.xp_orb import XPOrb
from config.settings import CELL_SIZE, GLOBAL_DROP_CHANCE, SCREEN_HEIGHT_PIX, SCREEN_WIDTH_PIX, SPAWN_ACTIVATION_DISTANCE
from core.debug import debug
from core.triggers import execute_trigger
from core.vfx import vfx_manager
from core.triggers import execute_trigger
from core.vfx import vfx_manager
from core.registry import Registry
from core.pathfinding import FlowField


class GameLogic:
    def __init__(self, game):
        self.game = game
        self.flow_field = FlowField()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.game.player.combat.switch_weapon()

    def update(self):
        vfx_manager.update()
        
        # Update Flow Field
        self.flow_field.update(self.game.player.x, self.game.player.y, self.game.world)
        
        self._handle_player_movement()
        self._handle_combat()
        
        # Check for game over (restart)
        if self.game.player.health <= 0:
            self.game.restart_game()
            return

        self._handle_pickups()
        self._handle_spawning_and_drops()
        self._handle_proximity_spawning()

        for obj in self.game.gridObjects:
            if isinstance(obj, Enemy):
                obj.update(self.flow_field, entities=self.game.gridObjects)
            else:
                obj.update((self.game.player.x, self.game.player.y))

        self._handle_input()
        self._handle_debug_input()

    def handle_pause_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            # Define button areas (must match renderer)
            # Screen props
            screen_w = pygame.display.get_surface().get_width()
            screen_h = pygame.display.get_surface().get_height()
            
            # Button dims
            btn_w = 200
            btn_h = 50
            start_y = screen_h - 250
            
            # Save Button
            save_rect = pygame.Rect(screen_w//2 - btn_w//2 - 110, start_y, btn_w, btn_h)
            # Close Button
            close_rect = pygame.Rect(screen_w//2 + 10, start_y, btn_w, btn_h)
            
            # New Game Button
            new_y = start_y + 70
            new_rect = pygame.Rect(screen_w//2 - btn_w//2, new_y, btn_w, btn_h)
            
            if save_rect.collidepoint(mouse_pos):
                from core.save_manager import SaveManager
                SaveManager.save_game(self.game)
                # Ensure we don't spam save
                
            elif close_rect.collidepoint(mouse_pos):
                # Quit game
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            
            elif new_rect.collidepoint(mouse_pos):
                from core.save_manager import SaveManager
                SaveManager.delete_save_file()
                self.game.restart_game()

    def _handle_player_movement(self):
        result = self.game.player.move(pygame.key.get_pressed(), self.game.world)
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
        player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * CELL_SIZE, self.game.player.h * CELL_SIZE)
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w * CELL_SIZE, enemy.h * CELL_SIZE)
            if player_rect.colliderect(enemy_rect):
                self.game.player.take_damage(enemy.damage)

    def _handle_pickups(self):
        # Pickup System (Items & XP)
        pickupables = [obj for obj in self.game.gridObjects if isinstance(obj, (Item, XPOrb))]
        
        # Pre-calculate player center and range squared
        px = self.game.player.x + (self.game.player.w * CELL_SIZE) / 2
        py = self.game.player.y + (self.game.player.h * CELL_SIZE) / 2
        pickup_range_sq = self.game.player.pickup_range ** 2
        
        player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * CELL_SIZE, self.game.player.h * CELL_SIZE)
        
        for obj in pickupables:
            # Magnet Logic (Optimized)
            ox = obj.x + (obj.w * CELL_SIZE)/2
            oy = obj.y + (obj.h * CELL_SIZE)/2
            
            dx = ox - px
            dy = oy - py
            dist_sq = dx*dx + dy*dy
            
            if dist_sq <= pickup_range_sq:
                if hasattr(obj, 'move_towards'):
                    obj.move_towards(self.game.player.x, self.game.player.y)
            
            # Collision/Collection Logic
            # Optimization: Only check collision if close enough (e.g. < 2 tiles)
            if dist_sq < (CELL_SIZE * 2) ** 2:
                obj_rect = pygame.Rect(obj.x, obj.y, obj.w * CELL_SIZE, obj.h * CELL_SIZE)
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
        
    def _handle_proximity_spawning(self):
        px = self.game.player.x
        py = self.game.player.y
        act_dist_sq = (SPAWN_ACTIVATION_DISTANCE * CELL_SIZE) ** 2
        
        for point in self.game.world.spawn_points:
            if point['spawned']:
                continue
                
            cx = point['x'] * CELL_SIZE
            cy = point['y'] * CELL_SIZE
            
            dx = cx - px
            dy = cy - py
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < act_dist_sq:
                # Activate Spawner
                point['spawned'] = True
                
                count = point['enemy_count']
                e_type = point['type']
                
                for _ in range(count):
                    # Spawn logic
                    valid = False
                    spawn_x, spawn_y = 0, 0
                    
                    for _ in range(10): 
                        off_x = randint(-2, 2)
                        off_y = randint(-2, 2)
                        tx = point['x'] + off_x
                        ty = point['y'] + off_y
                        
                        cell = self.game.world.get_cell(tx, ty)
                        if cell and cell.walkable:
                            spawn_x = tx * CELL_SIZE 
                            spawn_y = ty * CELL_SIZE
                            valid = True
                            break
                    
                    if valid:
                         self.game.gridObjects.append(
                            Enemy(self.game, spawn_x, spawn_y, enemy_type=e_type)
                         )
                         debug.log(f"Spawned {e_type} from spawner.")

    def _handle_input(self):
        pass

    def _handle_debug_input(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            min_x, min_y, max_x, max_y = 0, 0, SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX
            enemy_types = Registry.get_enemy_types()
            if enemy_types:
                # Try to find a valid spawn position
                for _ in range(50):
                    rx = randint(min_x, max_x - CELL_SIZE)
                    ry = randint(min_y, max_y - CELL_SIZE)
                    
                    # Check walkability
                    grid_x = int(rx / CELL_SIZE)
                    grid_y = int(ry / CELL_SIZE)
                    
                    cell = self.game.world.get_cell(grid_x, grid_y)
                    if cell and cell.walkable:
                        enemy_type = choice(enemy_types)
                        self.game.gridObjects.append(
                            Enemy(
                                self.game,
                                rx,
                                ry,
                                enemy_type=enemy_type
                            )
                        )
                        debug.log(f"Spawned {enemy_type} at ({rx}, {ry})")
                        break
                else:
                    debug.log("Failed to find valid spawn location for enemy.")
