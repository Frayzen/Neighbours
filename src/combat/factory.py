import json
import os
from combat.weapon import Weapon
from combat.behaviors import WeaponBehaviors
from config.settings import BASE_DIR
from config.constants import BEHAVIOR_MELEE_SWING

class WeaponFactory:
    _weapons_data = None

    @staticmethod
    def load_weapons():
        if WeaponFactory._weapons_data is None:
            path = os.path.join(BASE_DIR, 'config', 'weapons.json')
            try:
                with open(path, 'r') as f:
                    WeaponFactory._weapons_data = json.load(f)
            except FileNotFoundError:
                print(f"Error: Could not find weapons.json at {path}")
                WeaponFactory._weapons_data = {}

    @staticmethod
    def create_weapon(weapon_id: str) -> Weapon:
        WeaponFactory.load_weapons()
        
        if weapon_id not in WeaponFactory._weapons_data:
            raise ValueError(f"Weapon ID '{weapon_id}' not found in configuration.")

        data = WeaponFactory._weapons_data[weapon_id]
        
        # Get behavior name
        behavior_name = data.get("behavior", BEHAVIOR_MELEE_SWING)

        # Create the weapon instance
        weapon = Weapon(
            id=weapon_id,
            name=data["name"],
            damage=data["damage"],
            range=data["range"],
            cooldown=data["cooldown"],
            is_aoe=data.get("is_aoe", False),
            aoe_radius=data.get("aoe_radius", 0),
            tags=data.get("tags", []),
            texture_path=data.get("texture_path", None),
            behavior_name=behavior_name,
            line_of_sight=data.get("line_of_sight", False),
            projectile_speed=data.get("projectile_speed", 0),
            projectile_texture_path=data.get("projectile_texture_path", None)
        )
        
        # Attach the behavior function
        weapon.behavior_func = WeaponBehaviors.get_behavior(behavior_name)
        
        return weapon
