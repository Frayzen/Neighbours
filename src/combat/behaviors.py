import math
from core.debug import debug

class WeaponBehaviors:
    """
    This class contains the definitions for different weapon behaviors.
    You can add new functions here and reference them in weapons.json.
    """

    @staticmethod
    def melee_swing(weapon, owner, target, enemies):
        """
        Standard melee attack.
        """
        debug.log(f"{owner.__class__.__name__} swings {weapon.name} at {target.__class__.__name__}!")
        # TODO play melee swing animation and sound
        return True

    @staticmethod
    def fireball_cast(weapon, owner, target, enemies):
        """
        Casts a fireball that explodes on the target.
        """
        debug.log(f"{owner.__class__.__name__} casts a fireball from {weapon.name}!")
        
        # TODO spawn a Projectile entity
        # TODO explosion effect
        debug.log(f"Fireball flies towards {target.__class__.__name__}...")
        debug.log(f"BOOM! Fireball explodes!")
        
        return True

    @staticmethod
    def ranged_shot(weapon, owner, target, enemies):
        """
        Fires a projectile.
        """
        debug.log(f"{owner.__class__.__name__} shoots an arrow from {weapon.name}!")
        return True

    @staticmethod
    def ground_smash(weapon, owner, target, enemies):
        """
        Smashes the ground dealing heavy AOE.
        """
        debug.log(f"{owner.__class__.__name__} smashes the ground with {weapon.name}!")
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
