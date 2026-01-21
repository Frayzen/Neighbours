import math
from core.debug import debug
from core.vfx import vfx_manager, SlashEffect, ExplosionEffect
from config.settings import CELL_SIZE

class WeaponBehaviors:
    """
    This class contains the definitions for different weapon behaviors.
    You can add new functions here and reference them in weapons.json.
    """

    @staticmethod
    def _get_center(entity):
        # Helper to get center of entity
        w = getattr(entity, 'w', getattr(entity, 'size', 1)) * CELL_SIZE
        h = getattr(entity, 'h', getattr(entity, 'size', 1)) * CELL_SIZE
        return entity.x + w / 2, entity.y + h / 2

    @staticmethod
    def melee_swing(weapon, owner, target, enemies):
        """
        Standard melee attack.
        """
        debug.log(f"{owner.__class__.__name__} swings {weapon.name} at {target.__class__.__name__}!")
        
        ox, oy = WeaponBehaviors._get_center(owner)
        tx, ty = WeaponBehaviors._get_center(target)
        
        vfx_manager.add_effect(SlashEffect(ox, oy, tx, ty, width=3, color=(200, 200, 200)))
        return True

    @staticmethod
    def fireball_cast(weapon, owner, target, enemies):
        """
        Casts a fireball that explodes on the target.
        """
        debug.log(f"{owner.__class__.__name__} casts a fireball from {weapon.name}!")
        
        ox, oy = WeaponBehaviors._get_center(owner)
        tx, ty = WeaponBehaviors._get_center(target)
        
        # Calculate direction
        import pygame
        direction = pygame.math.Vector2(tx - ox, ty - oy)
        if direction.length() > 0:
            direction = direction.normalize()

        from entities.projectile import Projectile
        
        # Fireball specific overrides if not set on weapon
        # But ideally we use weapon config. 
        # For now, forcing it to ensure it works as requested even if weapon data isn't fully updated yet.
        
        proj = Projectile(
            x=ox,
            y=oy,
            direction=direction,
            speed=weapon.projectile_speed if weapon.projectile_speed > 0 else 8,
            damage=weapon.damage,
            owner_type="player" if owner.__class__.__name__ == "Player" else "enemy",
            texture=None, # Procedural fireball
            behavior="TARGET_EXPLOSION",
            visual_type="FIREBALL",
            target_pos=(tx, ty),
            explode_radius=weapon.aoe_radius if weapon.aoe_radius > 0 else 60,
            color=(255, 100, 0)
        )
        owner.game.projectiles.append(proj)
        
        return True

    @staticmethod
    def ranged_shot(weapon, owner, target, enemies):
        """
        Fires a projectile based on weapon config.
        """
        debug.log(f"{owner.__class__.__name__} shoots from {weapon.name}!")
        
        ox, oy = WeaponBehaviors._get_center(owner)
        tx, ty = WeaponBehaviors._get_center(target)
        
        # Calculate direction
        import pygame
        direction = pygame.math.Vector2(tx - ox, ty - oy)
        if direction.length() > 0:
            direction = direction.normalize()
            
        # Spawn Projectile
        from entities.projectile import Projectile
        
        speed = weapon.projectile_speed if weapon.projectile_speed > 0 else 10

        
        proj = Projectile(
            x=ox,
            y=oy,
            direction=direction,
            speed=speed,
            damage=weapon.damage,
            owner_type="player" if owner.__class__.__name__ == "Player" else "enemy",
            texture=None,
            behavior=getattr(weapon, 'projectile_behavior', "LINEAR"),
            visual_type=getattr(weapon, 'projectile_visual', "ARROW"),
            target_pos=(tx, ty), # Passed even for Linear, though unused
            color=getattr(weapon, 'projectile_color', (255, 255, 0)),
            explode_radius=getattr(weapon, 'projectile_explode_radius', 0)
        )
        owner.game.projectiles.append(proj)
        
        return True

    @staticmethod
    def ground_smash(weapon, owner, target, enemies):
        """
        Smashes the ground dealing heavy AOE.
        """
        debug.log(f"{owner.__class__.__name__} smashes the ground with {weapon.name}!")
        
        ox, oy = WeaponBehaviors._get_center(owner)
        vfx_manager.add_effect(ExplosionEffect(ox, oy, radius=weapon.aoe_radius, color=(100, 50, 0)))
        return True

    @staticmethod
    def get_behavior(behavior_name):
        """
        Returns the function corresponding to the behavior name.
        """
        if hasattr(WeaponBehaviors, behavior_name):
            return getattr(WeaponBehaviors, behavior_name)
        else:
            debug.log(f"Warning: Behavior '{behavior_name}' not found. Using default.")
            return WeaponBehaviors.melee_swing
