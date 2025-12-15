
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from combat.combat_manager import CombatManager
from combat.weapon import Weapon

# Mock libraries if needed, but we seem to only import standard ones in the files we touch, 
# except pygame in combat_manager, logic, player.
# We might need to mock pygame if it's imported at top level.
# combat_manager imports combat.weapon, config.settings, core.debug.
# We need to make sure those invalid imports don't crash us or mock them.

# Let's simple mock pygame to avoid init errors if no display
import unittest
from unittest.mock import MagicMock
import sys

sys.modules['pygame'] = MagicMock()
from core.debug import debug
debug.log = MagicMock() # Suppress logs or check them

class MockItem:
    def __init__(self, name, type, target_weapon, effects):
        self.name = name
        self.type = type
        self.target_weapon = target_weapon
        self.effects = effects

class TestUpgrade(unittest.TestCase):
    def test_upgrade(self):
        # Setup
        owner = MagicMock()
        owner.damage_mult = 1.0
        cm = CombatManager(owner)
        
        # Create weapon
        # name, damage, range, cooldown, is_aoe, aoe_radius
        weapon = Weapon("fireball_staff", 10, 100, 1000, True, 20)
        cm.add_weapon(weapon)
        
        print(f"Initial Stats: Damage={weapon.damage}, AOE={weapon.aoe_radius}")
        
        # Create upgrade item
        upgrade_data = {
            "name": "Fire Essence",
            "type": "weapon_upgrade",
            "target_weapon": "fireball_staff",
            "effects": {
                "aoe_radius": 50,
                "damage": 5
            }
        }
        item = MockItem(**upgrade_data)
        
        # Apply upgrade
        cm.apply_upgrade(item)
        
        print(f"Post-Upgrade Stats: Damage={weapon.damage}, AOE={weapon.aoe_radius}")
        
        # Assertions
        self.assertEqual(weapon.damage, 15)
        self.assertEqual(weapon.aoe_radius, 70)
        print("Test Passed!")

if __name__ == '__main__':
    unittest.main()
