import math
import os
import pygame
from config.settings import BASE_DIR

class Weapon:
    def __init__(self, id: str, name: str, damage: int, range: float, cooldown: int, is_aoe: bool = False, aoe_radius: float = 0, tags: list = None, texture_path: str = None, behavior_name: str = None, line_of_sight: bool = False, projectile_speed: float = 0, projectile_texture_path: str = None):
        """
        Initialize a new Weapon.
        
        :param id: Unique identifier for the weapon (e.g., 'fireball_staff')
        :param name: Name of the weapon
        :param damage: Damage dealt by the weapon
        :param range: Attack range of the weapon
        :param cooldown: Cooldown time in milliseconds
        :param is_aoe: Whether the weapon deals Area of Effect damage
        :param aoe_radius: The radius of the AOE attack (if is_aoe is True)
        :param tags: List of tags associated with the weapon
        :param texture_path: Path to the weapon's texture file
        :param behavior_name: Name of the behavior function to use
        :param line_of_sight: Whether the weapon requires line of sight to fire
        :param projectile_speed: Speed of the projectile (if applicable)
        :param projectile_texture_path: Texture path for the projectile
        """
        self.id = id
        self.name = name
        self.damage = damage
        self.range = range
        self.cooldown = cooldown
        self.is_aoe = is_aoe
        self.aoe_radius = aoe_radius
        self.tags = tags if tags else []
        self.last_attack_time = 0
        self.behavior_name = behavior_name
        self.behavior_func = None # Assigned by factory or reload
        self.texture_path = texture_path
        self.line_of_sight = line_of_sight
        self.projectile_speed = projectile_speed
        self.projectile_texture_path = projectile_texture_path
        
        # Texture handling
        self.image = None
        if texture_path:
            full_path = os.path.join(BASE_DIR, texture_path)
            if os.path.exists(full_path):
                try:
                    loaded_image = pygame.image.load(full_path).convert_alpha()
                    self.image = loaded_image
                except Exception as e:
                     print(f"Failed to load weapon texture {texture_path}: {e}")
            else:
                print(f"Weapon texture not found: {full_path}")
        
        # Projectile Texture loading
        self.projectile_image = None
        if projectile_texture_path:
            full_path = os.path.join(BASE_DIR, projectile_texture_path)
            if os.path.exists(full_path):
                try:
                    loaded_image = pygame.image.load(full_path).convert_alpha()
                    self.projectile_image = loaded_image
                except Exception as e:
                     print(f"Failed to load projectile texture {projectile_texture_path}: {e}")
            else:
                print(f"Projectile texture not found: {full_path}")

    def has_clear_shot(self, owner, target):
        if not self.line_of_sight:
            return True
            
        if not target or not hasattr(owner, 'game') or not owner.game.world:
            return True # Fail open if we can't check
            
        from core.physics import has_line_of_sight
        # Check from center to center
        start_x = owner.x + (owner.w * 50) / 2 # Assuming 50 is CELL_SIZE, ideally import it or use owner.w*CELL_SIZE if available.
        # But wait, owner.w is in cells. owner.x is in pixels.
        # Let's import CELL_SIZE or rely on owner having rect.
        # Safest is to just use x, y + half size.
        # Assuming entities are 1 tile roughly? 
        # Using pure pixels:
        
        return has_line_of_sight(owner.x, owner.y, target.x, target.y, owner.game.world)

    def can_attack(self, current_time: int) -> bool:
        """Check if the weapon is ready to attack."""
        return current_time - self.last_attack_time >= self.cooldown

    def attack(self, current_time: int, owner=None, target=None, enemies=None):
        """Register an attack and reset cooldown."""
        self.last_attack_time = current_time
        
        # Execute custom behavior if defined
        if self.behavior_func:
            self.behavior_func(self, owner, target, enemies)

    def get_targets(self, primary_target, all_enemies):
        """
        Determine which enemies are hit by the attack.
        Defines the shape/reach of the attack.
        """
        if not self.is_aoe:
            return [primary_target]
        
        targets = []
        for enemy in all_enemies:
            # Calculate distance from primary_target to enemy (Circular AOE around target)
            dx = primary_target.x - enemy.x
            dy = primary_target.y - enemy.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist <= self.aoe_radius:
                targets.append(enemy)
        
        return targets
        
    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude image and behavior function
        state['image'] = None
        state['behavior_func'] = None 
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = None
        self.behavior_func = None
        
        # Backward compatibility
        if not hasattr(self, 'projectile_speed'):
            self.projectile_speed = 0
        if not hasattr(self, 'projectile_texture_path'):
            self.projectile_texture_path = None
        if not hasattr(self, 'projectile_image'):
            self.projectile_image = None

    def reload_texture(self):
        if self.texture_path:
             full_path = os.path.join(BASE_DIR, self.texture_path)
             if os.path.exists(full_path):
                 try:
                     self.image = pygame.image.load(full_path).convert_alpha()
                 except Exception as e:
                     print(f"Failed to reload weapon texture {self.texture_path}: {e}")

        if hasattr(self, 'projectile_texture_path') and self.projectile_texture_path:
             full_path = os.path.join(BASE_DIR, self.projectile_texture_path)
             if os.path.exists(full_path):
                 try:
                     self.projectile_image = pygame.image.load(full_path).convert_alpha()
                 except Exception as e:
                     print(f"Failed to reload projectile texture {self.projectile_texture_path}: {e}")

    def reload_behavior(self):
        from combat.behaviors import WeaponBehaviors
        
        # If behavior_name is stored, reload it
        if hasattr(self, 'behavior_name') and self.behavior_name:
            self.behavior_func = WeaponBehaviors.get_behavior(self.behavior_name)
        else:
            # Fallback: Recover from Factory using ID
            try:
                from combat.factory import WeaponFactory
                # Ensure data is loaded
                WeaponFactory.load_weapons()
                if self.id in WeaponFactory._weapons_data:
                    data = WeaponFactory._weapons_data[self.id]
                    from config.constants import BEHAVIOR_MELEE_SWING
                    recalled_behavior = data.get("behavior", BEHAVIOR_MELEE_SWING)
                    
                    # Store it for next save
                    self.behavior_name = recalled_behavior
                    self.behavior_func = WeaponBehaviors.get_behavior(recalled_behavior)
                    print(f"DEBUG: Recovered behavior '{recalled_behavior}' for weapon '{self.name}'")
            except Exception as e:
                print(f"Failed to recover behavior for {self.name}: {e}")
