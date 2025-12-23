
import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock pygame
sys.modules['pygame'] = MagicMock()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock config.settings
mock_settings = MagicMock()
mock_settings.MAX_WEAPONS = 2
mock_settings.TARGET_CHECK_INTERVAL = 500
sys.modules['config.settings'] = mock_settings

from combat.combat_manager import CombatManager
from combat.weapon import Weapon

# Mock debug
from core.debug import debug
debug.log = MagicMock()

class MockItem:
    def __init__(self, name, type, target_weapon, effects):
        self.name = name
        self.type = type
        self.target_weapon = target_weapon
        self.effects = effects

class TestWeaponID(unittest.TestCase):
    def test_upgrade_with_id(self):
        # Setup
        owner = MagicMock()
        owner.damage_mult = 1.0
        cm = CombatManager(owner)
        
        # Create weapon with ID "fireball_staff"
        # Note: We are manually creating it here, matching the new signature
        weapon = Weapon(id="fireball_staff", name="Fireball Staff", damage=10, range=100, cooldown=1000, is_aoe=True, aoe_radius=20)
        cm.add_weapon(weapon)
        
        print(f"Initial Stats: ID={weapon.id}, Damage={weapon.damage}, AOE={weapon.aoe_radius}")
        
        # Create upgrade item targeting "fireball_staff"
        item = MockItem("Fire Essence", "weapon_upgrade", "fireball_staff", {"aoe_radius": 50})
        
        # Apply upgrade
        cm.apply_upgrade(item)
        
        print(f"Post-Upgrade Stats: ID={weapon.id}, Damage={weapon.damage}, AOE={weapon.aoe_radius}")
        
        # Assertions
        self.assertEqual(weapon.aoe_radius, 70)
        print("Test Passed!")

if __name__ == '__main__':
    unittest.main()
