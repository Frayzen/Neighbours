
import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock pygame before imports
sys.modules['pygame'] = MagicMock()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock config and config.settings
mock_config = MagicMock()
mock_settings = MagicMock()
mock_settings.COLOR_PLAYER = (255, 255, 255)
mock_settings.PLAYER_MAX_HEALTH = 100
mock_settings.PLAYER_INVULNERABILITY_DURATION = 1000
mock_settings.SCREEN_WIDTH = 800
mock_settings.SCREEN_HEIGHT = 600

sys.modules['config'] = mock_config
sys.modules['config.settings'] = mock_settings

from entities.player import Player
from core.debug import debug

debug.log = MagicMock()

class MockItem:
    def __init__(self, name, type, effects):
        self.name = name
        self.type = type
        self.effects = effects
        self.target_weapon = None

class TestPlayerStats(unittest.TestCase):
    def test_generic_stats(self):
        # Setup
        # Mock GridObject init or just let it run if it doesn't need pygame display
        # Player inherits GridObject. GridObject.__init__ might need checking.
        # Assuming GridObject just sets x,y,w,h.
        
        # We need to mock CombatManager inside Player or mock Player.combat
        with unittest.mock.patch('entities.player.CombatManager') as MockCombat:
             with unittest.mock.patch('entities.player.WeaponFactory'):
                player = Player(0, 0, 1, 5)
        
        print(f"Initial Stats: Speed={player.speed_mult}, Defense={player.defense_mult}, Cooldown={player.cooldown_mult}")

        # Test Speed Upgrade
        item_speed = MockItem("Speed Boots", "stat_upgrade", {"speed": 0.5})
        player.collect_item(item_speed)
        self.assertEqual(player.speed_mult, 1.5)
        
        # Test Defense Upgrade (New)
        item_def = MockItem("Shield", "stat_upgrade", {"defense": 0.2})
        player.collect_item(item_def)
        self.assertEqual(player.defense_mult, 1.2)
        
        # Test Cooldown Upgrade (New)
        item_cd = MockItem("Hourglass", "stat_upgrade", {"cooldown": -0.1})
        player.collect_item(item_cd)
        self.assertEqual(player.cooldown_mult, 0.9)
        
        # Test Invalid Stat
        item_bad = MockItem("Bad Item", "stat_upgrade", {"unknown": 10})
        player.collect_item(item_bad)
        # Should not crash, and should not add attribute (or we check it)
        self.assertFalse(hasattr(player, "unknown_mult"))
        
        print(f"Final Stats: Speed={player.speed_mult}, Defense={player.defense_mult}, Cooldown={player.cooldown_mult}")
        print("Test Passed!")

if __name__ == '__main__':
    unittest.main()
