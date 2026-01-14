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
        # Equip default weapons using the factory
        try:
            self.combat.add_weapon(WeaponFactory.create_weapon("fireball_staff"))
            self.combat.add_weapon(WeaponFactory.create_weapon("basic_sword"))
        except Exception as e:
            print(f"Failed to equip default weapons: {e}")

        # Visuals
        self.texture = None
        try:
            import os
            # Build absolute path to avoid cwd issues
            # We assume src is in path or we are running from root
            # Let's try relative to this file
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            img_path = os.path.join(base_path, "src", "assets", "images", "Alice.png")
            
            loaded_img = pygame.image.load(img_path).convert_alpha()
            self.texture = pygame.transform.scale(loaded_img, (int(self.w * CELL_SIZE), int(self.h * CELL_SIZE)))
            debug.log(f"Loaded Player Texture: {img_path}")
        except Exception as e:
            debug.log(f"Failed to load player texture: {e}")
            self.texture = None

        # Physics / Forces
        self.external_force = [0, 0]
        self.force_decay = 0.9 # Retain 90% per frame (slippery) or 0.5 for fast stop

        # Dash Mechanic
        self.dash_charges = 3
        self.max_dash_charges = 3
        self.dash_recharge_time = 3000 # 3 seconds to recharge one dash
        self.dash_last_recharge = 0
        self.is_dashing = False
        self.dash_duration = 200 # ms
        self.dash_start_time = 0
        self.dash_speed_mult = 3.0 # 3x speed
        self.dash_speed_mult = 3.0 # 3x speed
        self.dash_direction = (0, 0)
        
        # AI Control Flags
        self.ai_controlled = False
        self.ai_move_dir = (0, 0)
        self.ai_attack = False
        self.ai_dash = False

    def set_ai_action(self, action):
        """
        Maps discrete action (0-7) to player controls.
        0: Idle
        1: Up, 2: Down, 3: Left, 4: Right
        5: Attack
        6: Dash
        7: Switch Weapon? (Unused/Placeholder)
        """
        self.ai_move_dir = (0, 0)
        self.ai_attack = False
        self.ai_dash = False
        
        if action == 1: self.ai_move_dir = (0, -1)
        elif action == 2: self.ai_move_dir = (0, 1)
        elif action == 3: self.ai_move_dir = (-1, 0)
        elif action == 4: self.ai_move_dir = (1, 0)
        elif action == 5: self.ai_attack = True
        elif action == 6: self.ai_dash = True
        
    def _modify_stat(self, effect, op, value, revert=False):
        if effect == STAT_HEAL:
             if revert: return # Heal is instant, doesn't revert
             
             if op == OP_ADD:
                 self.health = min(self.max_health, self.health + value)
             elif op == OP_MULTIPLY:
                 self.health = min(self.max_health, self.health * (1 + value))
             
             debug.log(f"Healed (Op: {op}, Val: {value}). Health: {self.health}/{self.max_health}")
             return

        attr_name = f"{effect}_mult"
        if hasattr(self, attr_name):
            current_val = getattr(self, attr_name)
            
            if revert:
                if op == OP_ADD:
                    setattr(self, attr_name, current_val - value)
                elif op == OP_MULTIPLY:
                    setattr(self, attr_name, current_val / (1 + value))
                debug.log(f"  -> {effect} reverted. Multiplier: {getattr(self, attr_name)}")
            else:
                if op == OP_ADD:
                    setattr(self, attr_name, current_val + value)
                elif op == OP_MULTIPLY:
                    setattr(self, attr_name, current_val * (1 + value))
                debug.log(f"{effect.capitalize()} modified (Op: {op}, Val: {value}). New multiplier: {getattr(self, attr_name)}")
        else:
             debug.log(f"Unknown stat upgrade: {effect}")

    def collect_item(self, item):
        debug.log(f"Collected item: {item.name}")
        
        if item.type == ITEM_TYPE_WEAPON:
            self.combat.apply_upgrade(item)
            return

        # Check if temporary effect
        if item.duration > 0:
            self.active_effects.append({
                "item": item,
                "start_time": pygame.time.get_ticks(),
                "duration": item.duration
            })
            debug.log(f"Applied temporary effect: {item.name} for {item.duration}ms")

        # Apply effect immediately (revert logic will handle removal)
        for effect, data in item.effects.items():
            op = data["op"]
            val = data["value"]
            self._modify_stat(effect, op, val, revert=False)

    def dash(self):
        """
        Activates dash if charges available.
        """
        current_time = pygame.time.get_ticks()
        
        if self.is_dashing:
            return # Already dashing
            
        if self.dash_charges > 0:
            self.dash_charges -= 1
            self.is_dashing = True
            self.invulnerable = True # I-Frames
            self.dash_start_time = current_time
            # Keep dash_last_recharge relative to last update or reset? 
            # If we are at 3 charges, timer is dormant. If we drop to 2, timer starts? 
            # Let's handle recharge in update.
            
            # Determine direction from last input or default
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
            
            # Normalize
            if dx != 0 or dy != 0:
                length = (dx*dx + dy*dy)**0.5
                self.dash_direction = (dx/length, dy/length)
            else:
                # Default dash forward (right?) or last faced? 
                # For now default right if static
                self.dash_direction = (0, 0) # No dash if standing still? Or dash forward?
                # User says "movement direction". If no movement, no dash velocity? 
                # Let's assume no dash movement if stationary, but still consume charge? 
                # Or just abort? Most games dash forward.
                # Let's abort if no input.
                if dx == 0 and dy == 0:
                     self.is_dashing = False
                     self.invulnerable = False
                     self.dash_charges += 1 # Refund
                     return

            debug.log(f"Dash! Charges remaining: {self.dash_charges}")

    def update(self, enemies=None):
        current_time = pygame.time.get_ticks()
        
        # Dash Logic
        if self.is_dashing:
            if current_time - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
                self.invulnerable = False
                # If we were invulnerable due to hit, we might accidentally clear it.
                # But typically dash i-frames override everything.
                # Better: Check if invulnerable_duration from hit is still active? 
                # For simplicity: Dash end clears invulnerability. 
                # If player gets hit right after dash, normal logic applies.

        # Dash Recharge
        if self.dash_charges < self.max_dash_charges:
            if current_time - self.dash_last_recharge > self.dash_recharge_time:
                self.dash_charges += 1
                self.dash_last_recharge = current_time
                debug.log(f"Dash Recharged. Total: {self.dash_charges}")
        else:
             self.dash_last_recharge = current_time # Reset timer while full


        # Manage active effects
        for effect_data in self.active_effects[:]: # Iterate copy to safe remove
            if current_time - effect_data["start_time"] > effect_data["duration"]:
                item = effect_data["item"]
                debug.log(f"Effect expired: {item.name}")
                
                # Revert effects
                for effect, data in item.effects.items():
                    op = data["op"]
                    val = data["value"]
                    self._modify_stat(effect, op, val, revert=True)
                
                self.active_effects.remove(effect_data)
        
        if self.invulnerable and not self.is_dashing: # Only check hit timer if not dashing
            if current_time - self.last_hit_time > self.invulnerability_duration:
                self.invulnerable = False

        # AI Actions
        if self.ai_controlled:
            if self.ai_dash:
                 self.dash()
            if self.ai_attack and enemies:
                 # Find nearest enemy
                 nearest = None
                 min_d = float('inf')
                 for e in enemies:
                     d = (e.x - self.x)**2 + (e.y - self.y)**2
                     if d < min_d:
                         min_d = d
                         nearest = e
                         
                 if nearest:
                     # Check cooldown and attack
                     if self.combat.current_weapon and self.combat.current_weapon.can_attack(current_time):
                         self.combat.attack(nearest, enemies, current_time)

        self.combat.update(enemies, current_time)

    def take_damage(self, amount):
        if self.invulnerable:
            return

        self.health -= amount
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)
        self.invulnerable = True
        self.last_hit_time = pygame.time.get_ticks()
        debug.log(f"Player took {amount} damage! Health: {self.health}/{self.max_health}")
        
        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Player died!")
        # TODO: Handle player death (restart game, show game over screen, etc.)

    def gain_xp(self, amount):
        self.xp += amount
        debug.log(f"Gained {amount} XP. Total: {self.xp}/{self.xp_to_next_level}")
        
        if self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        debug.log(f"Level Up! New Level: {self.level}")
        # TODO: Trigger level up UI or choices

    def move(self, keys, world):  # movement using arrow keys or WASD
        # pygame.K_ DIRECTION is used to detect key presses on this precise touch
        dx = 0
        dy = 0
        
        current_speed = self.speed * self.speed_mult
        
        # Dash Override
        if self.is_dashing:
             dx = self.dash_direction[0] * current_speed * self.dash_speed_mult
             dy = self.dash_direction[1] * current_speed * self.dash_speed_mult
        
        elif self.ai_controlled:
            # AI Movement
            dx = self.ai_move_dir[0] * current_speed
            dy = self.ai_move_dir[1] * current_speed
            
        else:
            # Keyboard Movement
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
                dx -= current_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += current_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= current_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += current_speed

        # Apply external forces (e.g. Gravity Smash)
        dx += self.external_force[0]
        dy += self.external_force[1]
        
        # Decay force
        self.external_force[0] *= self.force_decay
        self.external_force[1] *= self.force_decay
        
        # Snap to 0 if small
        if abs(self.external_force[0]) < 0.1: self.external_force[0] = 0
        if abs(self.external_force[1]) < 0.1: self.external_force[1] = 0

        bounds = (0, 0, GRID_WIDTH_PIX, GRID_HEIGHT_PIX)

        # Try moving X
        new_x = self.x + dx
        collision_x = check_collision(new_x, self.y, self.w, self.h, bounds, world)
        
        final_collision = None
        
        if not collision_x:
            self.x = new_x
        elif isinstance(collision_x, tuple):
             final_collision = collision_x

        # Try moving Y
        new_y = self.y + dy
        collision_y = check_collision(self.x, new_y, self.w, self.h, bounds, world)
        
        if not collision_y:
            self.y = new_y
        elif isinstance(collision_y, tuple):
             if final_collision is None:
                 final_collision = collision_y
        
        # Return trigger if any collision was a trigger
        return final_collision

    def draw(self, screen):
        # Draw player
        if self.texture:
            screen.blit(self.texture, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.w * CELL_SIZE, self.h * CELL_SIZE))
        
        # Draw weapon
        weapon = self.combat.current_weapon
        if weapon:
            # Simple representation: a small colored rect next to the player
            weapon_color = (200, 200, 200)
            weapon_color = (200, 200, 200)
            if TAG_FIRE in weapon.tags:
                weapon_color = (255, 100, 0)
            elif TAG_RANGED in weapon.tags:
                weapon_color = (100, 255, 100)
            
            # Draw slightly offset
            wx = self.x + (self.w * CELL_SIZE) * 0.8
            wy = self.y + (self.h * CELL_SIZE) * 0.2
            
            if weapon.image:
                 # Scale weapon image if needed (arbitrary size choice or based on tiles)
                 scaled_weapon = pygame.transform.scale(weapon.image, (10, 20)) 
                 screen.blit(scaled_weapon, (wx, wy))
            else:
                 pygame.draw.rect(screen, weapon_color, (wx, wy, 4, 10))

    # Serialization
    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude non-serializable game reference
        del state['game']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # 'game' will be re-assigned by SaveManager
        self.game = None 

    def post_load(self):
        # Reload weapon images
        for weapon in self.combat.weapons:
            if hasattr(weapon, 'reload_texture'):
                weapon.reload_texture()
            if hasattr(weapon, 'reload_behavior'):
                weapon.reload_behavior()
