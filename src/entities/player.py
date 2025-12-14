#0 at the top left corner of the screen
#moving a cube smothly using arrow
from typing import Tuple
import pygame
# Initialize Pygame
pygame.init()

# Set up the display
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_PLAYER, PLAYER_MAX_HEALTH, PLAYER_INVULNERABILITY_DURATION
from combat.combat_manager import CombatManager
from combat.factory import WeaponFactory
from entities.base import GridObject
from core.physics import check_collision
from core.physics import check_collision
from core.debug import debug
from config.constants import OP_ADD, OP_MULTIPLY, STAT_HEAL

class Player(GridObject):
    def __init__(self, x, y, size, speed):
        super().__init__(x, y, size, size, color=COLOR_PLAYER)
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

    def collect_item(self, item):
        debug.log(f"Collected item: {item.name}")
        
        if item.type == "weapon_upgrade":
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

            if effect == STAT_HEAL:
                 if op == OP_ADD:
                     self.health = min(self.max_health, self.health + val)
                 elif op == OP_MULTIPLY:
                     self.health = min(self.max_health, self.health * (1 + val))
                 
                 debug.log(f"Healed (Op: {op}, Val: {val}). Health: {self.health}/{self.max_health}")
                 continue

            # Generic stat handling
            attr_name = f"{effect}_mult"
            if hasattr(self, attr_name):
                current_val = getattr(self, attr_name)
                
                if op == OP_ADD:
                    setattr(self, attr_name, current_val + val)
                elif op == OP_MULTIPLY:
                    setattr(self, attr_name, current_val * (1 + val))
                    
                debug.log(f"{effect.capitalize()} modified (Op: {op}, Val: {val}). New multiplier: {getattr(self, attr_name)}")
            else:
                 debug.log(f"Unknown stat upgrade: {effect}")

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        
        # Manage active effects
        for effect_data in self.active_effects[:]: # Iterate copy to safe remove
            if current_time - effect_data["start_time"] > effect_data["duration"]:
                item = effect_data["item"]
                debug.log(f"Effect expired: {item.name}")
                
                # Revert effects
                for effect, data in item.effects.items():
                    op = data["op"]
                    val = data["value"]
                    
                    if effect == STAT_HEAL: continue # Heal is instant, doesn't revert
                    
                    attr_name = f"{effect}_mult"
                    if hasattr(self, attr_name):
                        current_val = getattr(self, attr_name)
                        if op == OP_ADD:
                            setattr(self, attr_name, current_val - val)
                        elif op == OP_MULTIPLY:
                            setattr(self, attr_name, current_val / (1 + val))
                            
                        debug.log(f"  -> {effect} reverted. Multiplier: {getattr(self, attr_name)}")
                
                self.active_effects.remove(effect_data)
        
        # Handle invulnerability
        if self.invulnerable:
            if current_time - self.last_hit_time > self.invulnerability_duration:
                self.invulnerable = False

        self.combat.update(enemies, current_time)

    def take_damage(self, amount):
        if self.invulnerable:
            return

        self.health -= amount
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

    def move(self, keys, bounds: Tuple[int, int, int, int], world, tile_size: int): #movement using arrow keys or WASD
#pygame.K_ DIRECTION is used to detect key presses on this precise touch
        dx = 0
        dy = 0
        
        current_speed = self.speed * self.speed_mult
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            dx -= current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += current_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += current_speed

        # Try moving X
        new_x = self.x + dx
        collision_x = check_collision(new_x, self.y, self.w, self.h, bounds, world, tile_size)
        if not collision_x:
            self.x = new_x
        elif isinstance(collision_x, tuple):
             return collision_x

        # Try moving Y
        new_y = self.y + dy
        collision_y = check_collision(self.x, new_y, self.w, self.h, bounds, world, tile_size)
        if not collision_y:
            self.y = new_y
        elif isinstance(collision_y, tuple):
             return collision_y
        
        return None

    def draw(self, surface, tile_size):
        # Draw player
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.w * tile_size, self.h * tile_size))
        
        # Draw weapon
        weapon = self.combat.current_weapon
        if weapon:
            # Simple representation: a small colored rect next to the player
            weapon_color = (200, 200, 200)
            if "fire" in weapon.name.lower():
                weapon_color = (255, 100, 0)
            elif "bow" in weapon.name.lower():
                weapon_color = (100, 255, 100)
            
            # Draw slightly offset
            wx = self.x + (self.w * tile_size) * 0.8
            wy = self.y + (self.h * tile_size) * 0.2
            
            if weapon.image:
                 # Scale weapon image if needed (arbitrary size choice or based on tiles)
                 # Let's say weapon is same size as player width roughly? Or fixed small icon.
                 # Using fixed small size for now to match rect
                 scaled_weapon = pygame.transform.scale(weapon.image, (10, 20)) 
                 surface.blit(scaled_weapon, (wx, wy))
            else:
                 pygame.draw.rect(surface, weapon_color, (wx, wy, 4, 10))
