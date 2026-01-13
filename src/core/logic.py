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
from core.vfx import vfx_manager, ExplosionEffect
from core.registry import Registry
from core.pathfinding import FlowField


class GameLogic:
    def __init__(self, game):
        self.game = game
        self.flow_field = FlowField()
        self.last_pathfinding_update = 0
        self.pathfinding_interval = 150 # ms

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.game.player.combat.switch_weapon()
            elif event.key == pygame.K_SPACE:
                self.game.player.dash()

    def update(self):
        vfx_manager.update()
        
        # Update Flow Field (Throttled)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_pathfinding_update > self.pathfinding_interval:
            self.flow_field.update(self.game.player.x, self.game.player.y, self.game.world, max_dist=30)
            self.last_pathfinding_update = current_time
        
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
            if obj == self.game.player:
                continue
            if isinstance(obj, Enemy):
                obj.update(self.flow_field, entities=self.game.gridObjects)
            else:
                obj.update((self.game.player.x, self.game.player.y))

        self._handle_input()
        self._handle_debug_input()
        self._handle_projectiles()

    def _handle_projectiles(self):
        to_remove = []
        # Update and Move
        for proj in self.game.projectiles:
            proj.update()
            
            # Check for explicit explosion signal (e.g. reached target)
            if proj.should_explode:
                self._trigger_projectile_explosion(proj)
                to_remove.append(proj)
                continue
            
            # 1. Wall Collision
            # Check center point or just current position
            grid_x = int(proj.x / CELL_SIZE)
            grid_y = int(proj.y / CELL_SIZE)
            
            cell = self.game.world.get_cell(grid_x, grid_y)
            if not cell or not cell.walkable:
                if proj.behavior == "TARGET_EXPLOSION":
                     self._trigger_projectile_explosion(proj)
                to_remove.append(proj)
                continue
            
            # 2. Entity Collision
            proj_rect = pygame.Rect(proj.x, proj.y, proj.w * CELL_SIZE, proj.h * CELL_SIZE)
            
            if proj.owner_type == "player":
                # Check vs Enemies
                enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
                for enemy in enemies:
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w * CELL_SIZE, enemy.h * CELL_SIZE)
                    if proj_rect.colliderect(enemy_rect):
                        if proj.behavior == "TARGET_EXPLOSION":
                             self._trigger_projectile_explosion(proj)
                        else:
                             enemy.take_damage(proj.damage)
                        
                        if proj not in to_remove:
                            to_remove.append(proj)
                        break # One projectile hits one enemy (unless passing through?)
            
            elif proj.owner_type == "enemy":
                 # Check vs Player
                 player = self.game.player
                 player_rect = pygame.Rect(player.x, player.y, player.w * CELL_SIZE, player.h * CELL_SIZE)
                 if proj_rect.colliderect(player_rect):
                     if proj.behavior == "TARGET_EXPLOSION":
                         self._trigger_projectile_explosion(proj)
                     else:
                         player.take_damage(proj.damage)
                     
                     if proj not in to_remove:
                        to_remove.append(proj)
        
        # Cleanup
        for r in to_remove:
            if r in self.game.projectiles:
                self.game.projectiles.remove(r)

    def _trigger_projectile_explosion(self, proj):
        # Visual Effect
        vfx_manager.add_effect(ExplosionEffect(proj.x, proj.y, radius=proj.explode_radius, color=proj.color))
        
        # Damage Logic (AOE)
        center_x = proj.x
        center_y = proj.y
        # radius is already in pixels
        radius_sq = proj.explode_radius ** 2
        
        # Apply Damage
        targets = []
        if proj.owner_type == "player":
             targets = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
        else:
             targets = [self.game.player]
             
        for target in targets:
             # Center to center
             tx = target.x + (target.w * CELL_SIZE)/2
             ty = target.y + (target.h * CELL_SIZE)/2
             
             dist_sq = (tx - center_x)**2 + (ty - center_y)**2
             if dist_sq <= proj.explode_radius ** 2:
                 target.take_damage(proj.damage)

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
        
        # Check for triggers on the tile the player is currently standing on
        # Calculate center of player
        px = self.game.player.x + (self.game.player.w * CELL_SIZE) / 2
        py = self.game.player.y + (self.game.player.h * CELL_SIZE) / 2
        
        grid_x = int(px / CELL_SIZE)
        grid_y = int(py / CELL_SIZE)
        
        cell = self.game.world.get_cell(grid_x, grid_y)
        if cell and cell.trigger:
            execute_trigger(cell.trigger, self.game, grid_x, grid_y)

        # Handle collision triggers (if any that block movement)
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
            # Check spawn mode logic
            can_spawn = False
            spawn_mode = point.get('spawn_mode', 'once') # Default to once
            current_time = pygame.time.get_ticks()

            if spawn_mode == 'once':
                if not point['spawned']:
                     can_spawn = True
            elif spawn_mode == 'infinite':
                last_spawn = point.get('last_spawn_time', 0)
                cooldown = point.get('cooldown', 5000) # Default 5s
                if current_time - last_spawn > cooldown:
                    can_spawn = True

            if not can_spawn:
                continue

            cx = point['x'] * CELL_SIZE
            cy = point['y'] * CELL_SIZE
            
            dx = cx - px
            dy = cy - py
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < act_dist_sq:
                # Activate Spawner
                point['spawned'] = True
                if spawn_mode == 'infinite':
                    point['last_spawn_time'] = current_time
                    
                count = point['enemy_count']
                base_type = point['type']
                
                for _ in range(count):
                    # Determine type
                    if base_type == "random":
                        # Exclude Boss from random spawns
                        available = [e for e in Registry.get_enemy_types() if "Boss" not in e and e != "JörnBoss"]
                        print(f"DEBUG: Spawning random enemy. Excluded JörnBoss. Available: {available}")
                        # Start with a default
                        e_type = "basic_enemy"
                        if available:
                            e_type = choice(available)
                    else:
                        e_type = base_type

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
        if keystate[pygame.K_p]:
            min_x, min_y, max_x, max_y = 0, 0, SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX
            enemy_types = [e for e in Registry.get_enemy_types() if e != "JörnBoss"]
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
