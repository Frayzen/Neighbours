import math
import os
import pygame
from config.settings import BASE_DIR

"""Janis REISENAUER"""

class Weapon:
    def __init__(self, id: str, name: str, damage: int, range: float, cooldown: int, is_aoe: bool = False, aoe_radius: float = 0, tags: list = None, texture_path: str = None, behavior_name: str = None):
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

    def reload_texture(self):
        if self.texture_path:
             full_path = os.path.join(BASE_DIR, self.texture_path)
             if os.path.exists(full_path):
                 try:
                     self.image = pygame.image.load(full_path).convert_alpha()
                 except Exception as e:
                     print(f"Failed to reload weapon texture {self.texture_path}: {e}")

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
