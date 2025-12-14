import math
import os
import pygame
from config.settings import BASE_DIR

class Weapon:
    def __init__(self, id: str, name: str, damage: int, range: float, cooldown: int, is_aoe: bool = False, aoe_radius: float = 0, tags: list = None, texture_path: str = None):
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
        self.behavior_func = None # Assigned by factory
        
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
