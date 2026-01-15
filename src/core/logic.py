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
from core.input_state import InputState


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

    def _get_human_input(self):
        keys = pygame.key.get_pressed()
        input_state = InputState()
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: input_state.move_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: input_state.move_x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: input_state.move_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: input_state.move_y = 1
        
        if keys[pygame.K_SPACE]: input_state.dash = True
        
        if pygame.mouse.get_pressed()[0]: 
             input_state.attack = True
             
        return input_state

    def update(self, input_state=None):
        vfx_manager.update()
        
        if input_state is None:
             input_state = self._get_human_input()
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_pathfinding_update > self.pathfinding_interval:
            self.flow_field.update(self.game.player.x, self.game.player.y, self.game.world, max_dist=30)
            self.last_pathfinding_update = current_time
        
        self._handle_player_movement(input_state)
        self._handle_combat(input_state)
        
        if self.game.player.health <= 0:
            self.game.restart_game()
            return

        self._handle_pickups()
        self._handle_spawning_and_drops()
        self._handle_proximity_spawning()

        # Update Entities
        # Optimization: Filter list once if possible, but list comprehension is fast enough for <100 entities
        for obj in self.game.gridObjects:
            if obj == self.game.player:
                continue
            if isinstance(obj, Enemy):
                obj.update(self.flow_field, entities=self.game.gridObjects)
            else:
                obj.update((self.game.player.x, self.game.player.y))

        self._handle_projectiles()

    def _handle_projectiles(self):
        to_remove = []
        
        # Pre-cache player bounds
        p = self.game.player
        px, py = p.x, p.y
        pw, ph = p.w * CELL_SIZE, p.h * CELL_SIZE
        
        # Pre-filter enemies to avoid filtering per projectile
        enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
        
        # Pre-cache enemy bounds: List of (obj, x, y, w, h)
        # This prevents attribute lookups inside the inner loop
        enemy_bounds = []
        for e in enemies:
            enemy_bounds.append((e, e.x, e.y, e.w * CELL_SIZE, e.h * CELL_SIZE))

        grid = self.game.world.grid

        for proj in self.game.projectiles:
            proj.update()
            
            if proj.should_explode:
                self._trigger_projectile_explosion(proj)
                to_remove.append(proj)
                continue
            
            # 1. Wall Collision (Optimized Grid Access)
            grid_x = int(proj.x / CELL_SIZE)
            grid_y = int(proj.y / CELL_SIZE)
            
            try:
                if not grid[grid_y][grid_x][0].walkable:
                    if proj.behavior == "TARGET_EXPLOSION":
                         self._trigger_projectile_explosion(proj)
                    to_remove.append(proj)
                    continue
            except IndexError:
                to_remove.append(proj) # OOB
                continue
            
            # 2. Entity Collision (AABB Math, no Rects)
            pr_x, pr_y = proj.x, proj.y
            pr_w, pr_h = proj.w * CELL_SIZE, proj.h * CELL_SIZE
            
            hit = False
            
            if proj.owner_type == "player":
                # Check vs Enemies
                for e_obj, ex, ey, ew, eh in enemy_bounds:
                    # AABB Check
                    if pr_x < ex + ew and pr_x + pr_w > ex and pr_y < ey + eh and pr_y + pr_h > ey:
                        if proj.behavior == "TARGET_EXPLOSION":
                             self._trigger_projectile_explosion(proj)
                        else:
                             e_obj.take_damage(proj.damage)
                        
                        hit = True
                        break 
            
            elif proj.owner_type == "enemy":
                 # Check vs Player
                 if pr_x < px + pw and pr_x + pr_w > px and pr_y < py + ph and pr_y + pr_h > py:
                     if proj.behavior == "TARGET_EXPLOSION":
                         self._trigger_projectile_explosion(proj)
                     else:
                         p.take_damage(proj.damage)
                         if proj.owner and hasattr(proj.owner, 'summoner') and proj.owner.summoner:
                             if hasattr(proj.owner.summoner, 'minion_damage_dealt'):
                                 proj.owner.summoner.minion_damage_dealt += proj.damage
                     hit = True
            
            if hit and proj not in to_remove:
                to_remove.append(proj)
        
        for r in to_remove:
            if r in self.game.projectiles:
                self.game.projectiles.remove(r)

    def _trigger_projectile_explosion(self, proj):
        vfx_manager.add_effect(ExplosionEffect(proj.x, proj.y, radius=proj.explode_radius, color=proj.color))
        
        center_x = proj.x
        center_y = proj.y
        radius_sq = proj.explode_radius ** 2
        
        targets = []
        if proj.owner_type == "player":
             targets = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
        else:
             targets = [self.game.player]
             
        for target in targets:
             tx = target.x + (target.w * CELL_SIZE)/2
             ty = target.y + (target.h * CELL_SIZE)/2
             dist_sq = (tx - center_x)**2 + (ty - center_y)**2
             if dist_sq <= radius_sq:
                 target.take_damage(proj.damage)

    def handle_pause_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            screen_w = pygame.display.get_surface().get_width()
            screen_h = pygame.display.get_surface().get_height()
            btn_w = 200
            btn_h = 50
            start_y = screen_h - 250
            
            save_rect = pygame.Rect(screen_w//2 - btn_w//2 - 110, start_y, btn_w, btn_h)
            close_rect = pygame.Rect(screen_w//2 + 10, start_y, btn_w, btn_h)
            new_rect = pygame.Rect(screen_w//2 - btn_w//2, start_y + 70, btn_w, btn_h)
            
            if save_rect.collidepoint(mouse_pos):
                from core.save_manager import SaveManager
                SaveManager.save_game(self.game)
            elif close_rect.collidepoint(mouse_pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif new_rect.collidepoint(mouse_pos):
                from core.save_manager import SaveManager
                SaveManager.delete_save_file()
                self.game.restart_game()

    def _handle_player_movement(self, input_state):
        result = self.game.player.move(input_state, self.game.world)
        
        px = self.game.player.x + (self.game.player.w * CELL_SIZE) / 2
        py = self.game.player.y + (self.game.player.h * CELL_SIZE) / 2
        
        grid_x = int(px / CELL_SIZE)
        grid_y = int(py / CELL_SIZE)
        
        cell = self.game.world.get_cell(grid_x, grid_y)
        if cell and cell.trigger:
            execute_trigger(cell.trigger, self.game, grid_x, grid_y)

        if result:
            cell, x, y = result
            if cell.trigger:
                execute_trigger(cell.trigger, self.game, x, y)

    def _handle_combat(self, input_state):
        enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy)]
        self.game.player.update(input_state, enemies)

        # Player Hit Collision (AABB)
        px, py = self.game.player.x, self.game.player.y
        pw, ph = self.game.player.w * CELL_SIZE, self.game.player.h * CELL_SIZE
        
        for enemy in enemies:
            ex, ey = enemy.x, enemy.y
            ew, eh = enemy.w * CELL_SIZE, enemy.h * CELL_SIZE
            
            if px < ex + ew and px + pw > ex and py < ey + eh and py + ph > ey:
                self.game.player.take_damage(enemy.damage)
                if hasattr(enemy, 'summoner') and enemy.summoner:
                     if hasattr(enemy.summoner, 'minion_damage_dealt'):
                         enemy.summoner.minion_damage_dealt += enemy.damage

    def _handle_pickups(self):
        pickupables = [obj for obj in self.game.gridObjects if isinstance(obj, (Item, XPOrb))]
        px = self.game.player.x + (self.game.player.w * CELL_SIZE) / 2
        py = self.game.player.y + (self.game.player.h * CELL_SIZE) / 2
        pickup_range_sq = self.game.player.pickup_range ** 2
        
        pl_x, pl_y = self.game.player.x, self.game.player.y
        pl_w, pl_h = self.game.player.w * CELL_SIZE, self.game.player.h * CELL_SIZE
        
        for obj in pickupables:
            ox = obj.x + (obj.w * CELL_SIZE)/2
            oy = obj.y + (obj.h * CELL_SIZE)/2
            dx = ox - px
            dy = oy - py
            dist_sq = dx*dx + dy*dy
            
            if dist_sq <= pickup_range_sq:
                if hasattr(obj, 'move_towards'):
                    obj.move_towards(self.game.player.x, self.game.player.y)
            
            if dist_sq < (CELL_SIZE * 2) ** 2:
                # Collision Check (AABB)
                ow, oh = obj.w * CELL_SIZE, obj.h * CELL_SIZE
                if pl_x < obj.x + ow and pl_x + pl_w > obj.x and pl_y < obj.y + oh and pl_y + pl_h > obj.y:
                    if isinstance(obj, Item):
                        self.game.player.collect_item(obj)
                    elif isinstance(obj, XPOrb):
                        self.game.player.gain_xp(obj.value)
                    
                    if obj in self.game.gridObjects:
                        self.game.gridObjects.remove(obj)

    def _handle_spawning_and_drops(self):
        dead_enemies = [obj for obj in self.game.gridObjects if isinstance(obj, Enemy) and obj.health <= 0]
        for enemy in dead_enemies:
            xp_orb = XPOrb(enemy.x, enemy.y, enemy.xp_value)
            self.game.gridObjects.append(xp_orb)
            current_drop_chance = GLOBAL_DROP_CHANCE * self.game.player.luck_mult
            if random.random() < current_drop_chance:
                item = ItemFactory.create_random_item(enemy.x, enemy.y, luck=self.game.player.luck_mult)
                if item:
                    self.game.gridObjects.append(item)
            self.game.gridObjects.remove(enemy)
        
    def _handle_proximity_spawning(self):
        px = self.game.player.x
        py = self.game.player.y
        act_dist_sq = (SPAWN_ACTIVATION_DISTANCE * CELL_SIZE) ** 2
        current_time = pygame.time.get_ticks()
        
        for point in self.game.world.spawn_points:
            can_spawn = False
            spawn_mode = point.get('spawn_mode', 'once')

            if spawn_mode == 'once':
                if not point['spawned']:
                     can_spawn = True
            elif spawn_mode == 'infinite':
                last_spawn = point.get('last_spawn_time', 0)
                cooldown = point.get('cooldown', 5000)
                if current_time - last_spawn > cooldown:
                    can_spawn = True

            if not can_spawn: continue

            cx = point['x'] * CELL_SIZE
            cy = point['y'] * CELL_SIZE
            dx = cx - px
            dy = cy - py
            if dx*dx + dy*dy < act_dist_sq:
                point['spawned'] = True
                if spawn_mode == 'infinite':
                    point['last_spawn_time'] = current_time
                    
                count = point['enemy_count']
                base_type = point['type']
                
                for _ in range(count):
                    if base_type == "random":
                        available = [e for e in Registry.get_enemy_types() if "Boss" not in e and e != "JörnBoss"]
                        e_type = "basic_enemy"
                        if available: e_type = choice(available)
                    else:
                        e_type = base_type

                    valid = False
                    spawn_x, spawn_y = 0, 0
                    
                    for _ in range(10): 
                        off_x = randint(-2, 2)
                        off_y = randint(-2, 2)
                        tx = point['x'] + off_x
                        ty = point['y'] + off_y
                        
                        # Safe Grid Check
                        cell = self.game.world.get_cell(tx, ty)
                        if cell and cell.walkable:
                            spawn_x = tx * CELL_SIZE 
                            spawn_y = ty * CELL_SIZE
                            valid = True
                            break
                    
                    if valid:
                         if e_type == "JörnBoss":
                             from entities.boss.joern import JoernBoss
                             self.game.gridObjects.append(JoernBoss(self.game, spawn_x, spawn_y))
                         else:
                             self.game.gridObjects.append(Enemy(self.game, spawn_x, spawn_y, enemy_type=e_type))

    def _handle_input(self):
        pass

    def _handle_debug_input(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_p]:
            min_x, min_y, max_x, max_y = 0, 0, SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX
            enemy_types = [e for e in Registry.get_enemy_types() if e != "JörnBoss"]
            if enemy_types:
                for _ in range(50):
                    rx = randint(min_x, max_x - CELL_SIZE)
                    ry = randint(min_y, max_y - CELL_SIZE)
                    grid_x = int(rx / CELL_SIZE)
                    grid_y = int(ry / CELL_SIZE)
                    cell = self.game.world.get_cell(grid_x, grid_y)
                    if cell and cell.walkable:
                        self.game.gridObjects.append(Enemy(self.game, rx, ry, enemy_type=choice(enemy_types)))
                        break