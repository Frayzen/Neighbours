# 0 at the top left corner of the screen
# moving a cube smothly using arrow
from typing import Tuple
import pygame

# Initialize Pygame
pygame.init()

# Set up the display
from config.settings import (
    CELL_SIZE,
    GRID_HEIGHT,
    GRID_HEIGHT_PIX,
    GRID_WIDTH,
    GRID_WIDTH_PIX,
    SCREEN_WIDTH_PIX,
    SCREEN_HEIGHT_PIX,
)

from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_PLAYER, PLAYER_MAX_HEALTH, PLAYER_INVULNERABILITY_DURATION
from combat.combat_manager import CombatManager
from combat.factory import WeaponFactory
from entities.base import GridObject
from core.physics import check_collision
from core.physics import check_collision
from core.debug import debug
from config.constants import OP_ADD, OP_MULTIPLY, STAT_HEAL, ITEM_TYPE_WEAPON, TAG_FIRE, TAG_RANGED

class Player(GridObject):
    def __init__(self, game, x, y, size, speed):
        super().__init__(x, y, size, size, color=COLOR_PLAYER)
        self.game = game
        self.speed = speed
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.invulnerable = False
        self.invulnerability_duration = PLAYER_INVULNERABILITY_DURATION  # ms
        self.last_hit_time = 0
        
        # Stats Multipliers
        self.speed_mult = 1.0
        self.damage_mult = 1.0
        self.defense_mult = 1.0
        self.cooldown_mult = 1.0
        self.luck_mult = 1.0

        # XP and Leveling
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100
        self.pickup_range = 100 # Range in pixels for magnet effect
        
        self.active_effects = []
        
        # Combat setup
        self.combat = CombatManager(self)
        try:
            self.combat.add_weapon(WeaponFactory.create_weapon("fireball_staff"))
            self.combat.add_weapon(WeaponFactory.create_weapon("basic_sword"))
        except Exception as e:
            print(f"Failed to equip default weapons: {e}")

        # Visuals
        self.texture = None
        self.headless = getattr(game, 'headless', False)
        
        if not self.headless:
            try:
                import os
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                img_path = os.path.join(base_path, "src", "assets", "images", "Alice.png")
                loaded_img = pygame.image.load(img_path).convert_alpha()
                self.texture = pygame.transform.scale(loaded_img, (int(self.w * CELL_SIZE), int(self.h * CELL_SIZE)))
                debug.log(f"Loaded Player Texture: {img_path}")
            except Exception as e:
                debug.log(f"Failed to load player texture: {e}")
                self.texture = None
        else:
            self.texture = None

        # Physics / Forces
        self.external_force = [0, 0]
        self.force_decay = 0.9 

        # Dash Mechanic
        self.dash_charges = 3
        self.max_dash_charges = 3
        self.dash_recharge_time = 3000
        self.dash_last_recharge = 0
        self.is_dashing = False
        self.dash_duration = 200
        self.dash_start_time = 0
        self.dash_speed_mult = 3.0
        self.dash_direction = (0, 0)
        
        self.ai_controlled = False

    def _modify_stat(self, effect, op, value, revert=False):
        if effect == STAT_HEAL:
             if revert: return 
             if op == OP_ADD:
                 self.health = min(self.max_health, self.health + value)
             elif op == OP_MULTIPLY:
                 self.health = min(self.max_health, self.health * (1 + value))
             return

        attr_name = f"{effect}_mult"
        if hasattr(self, attr_name):
            current_val = getattr(self, attr_name)
            if revert:
                if op == OP_ADD: setattr(self, attr_name, current_val - value)
                elif op == OP_MULTIPLY: setattr(self, attr_name, current_val / (1 + value))
            else:
                if op == OP_ADD: setattr(self, attr_name, current_val + value)
                elif op == OP_MULTIPLY: setattr(self, attr_name, current_val * (1 + value))
        else:
             debug.log(f"Unknown stat upgrade: {effect}")

    def collect_item(self, item):
        debug.log(f"Collected item: {item.name}")
        
        if item.type == ITEM_TYPE_WEAPON:
            self.combat.apply_upgrade(item)
            return

        if item.duration > 0:
            self.active_effects.append({
                "item": item,
                "start_time": pygame.time.get_ticks(),
                "duration": item.duration
            })

        for effect, data in item.effects.items():
            op = data["op"]
            val = data["value"]
            self._modify_stat(effect, op, val, revert=False)

    def dash(self, input_state):
        current_time = pygame.time.get_ticks()
        if self.is_dashing: return 
            
        if self.dash_charges > 0:
            self.dash_charges -= 1
            self.is_dashing = True
            self.invulnerable = True
            self.dash_start_time = current_time
            
            dx, dy = input_state.move_x, input_state.move_y
            if dx != 0 or dy != 0:
                length = (dx*dx + dy*dy)**0.5
                self.dash_direction = (dx/length, dy/length)
            else:
                self.is_dashing = False
                self.invulnerable = False
                self.dash_charges += 1
                return

    def update(self, input_state, enemies=None):
        current_time = pygame.time.get_ticks()
        
        if self.is_dashing:
            if current_time - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
                self.invulnerable = False

        if self.dash_charges < self.max_dash_charges:
            if current_time - self.dash_last_recharge > self.dash_recharge_time:
                self.dash_charges += 1
                self.dash_last_recharge = current_time
        else:
             self.dash_last_recharge = current_time 

        for effect_data in self.active_effects[:]: 
            if current_time - effect_data["start_time"] > effect_data["duration"]:
                item = effect_data["item"]
                for effect, data in item.effects.items():
                    op = data["op"]
                    val = data["value"]
                    self._modify_stat(effect, op, val, revert=True)
                self.active_effects.remove(effect_data)
        
        if self.invulnerable and not self.is_dashing:
            if current_time - self.last_hit_time > self.invulnerability_duration:
                self.invulnerable = False

        if input_state:
            if input_state.dash: self.dash(input_state)
            if input_state.attack:
                 pass # Combat manager handles attack timing

        self.combat.update(enemies, current_time)

    def take_damage(self, amount):
        if self.invulnerable: return

        # Apply Defense
        reduced_amount = amount / self.defense_mult
        self.health -= reduced_amount
        
        self.game.damage_texts.spawn(self.x, self.y - 10, int(reduced_amount))
        self.invulnerable = True
        self.last_hit_time = pygame.time.get_ticks()
        
        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Player died!")

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        
        # --- NEW: STAT GROWTH ---
        self.max_health += 20
        self.health = self.max_health # Full Heal
        self.damage_mult += 0.1       # +10% Damage
        self.defense_mult += 0.05     # +5% Defense
        
        # Visuals
        self.game.damage_texts.spawn(self.x, self.y - 30, "LEVEL UP!", color=(255, 215, 0))
        debug.log(f"Level Up! Level: {self.level}, MaxHP: {self.max_health}, Dmg: {self.damage_mult:.2f}")

    def move(self, input_state, world):  
        dx = 0
        dy = 0
        current_speed = self.speed * self.speed_mult
        
        if self.is_dashing:
             dx = self.dash_direction[0] * current_speed * self.dash_speed_mult
             dy = self.dash_direction[1] * current_speed * self.dash_speed_mult
        elif input_state:
            dx = input_state.move_x * current_speed
            dy = input_state.move_y * current_speed

        dx += self.external_force[0]
        dy += self.external_force[1]
        
        self.external_force[0] *= self.force_decay
        self.external_force[1] *= self.force_decay
        
        if abs(self.external_force[0]) < 0.1: self.external_force[0] = 0
        if abs(self.external_force[1]) < 0.1: self.external_force[1] = 0

        bounds = (0, 0, GRID_WIDTH_PIX, GRID_HEIGHT_PIX)

        new_x = self.x + dx
        collision_x = check_collision(new_x, self.y, self.w, self.h, bounds, world)
        
        final_collision = None
        if not collision_x:
            self.x = new_x
        elif isinstance(collision_x, tuple):
             final_collision = collision_x

        new_y = self.y + dy
        collision_y = check_collision(self.x, new_y, self.w, self.h, bounds, world)
        
        if not collision_y:
            self.y = new_y
        elif isinstance(collision_y, tuple):
             if final_collision is None:
                 final_collision = collision_y
        
        return final_collision

    # Serialization
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['game']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.game = None 

    def post_load(self):
        for weapon in self.combat.weapons:
            if hasattr(weapon, 'reload_texture'): weapon.reload_texture()
            if hasattr(weapon, 'reload_behavior'): weapon.reload_behavior()