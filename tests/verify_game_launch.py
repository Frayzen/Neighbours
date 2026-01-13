
import os
import sys
import unittest
import pygame
from unittest.mock import MagicMock

# Set dummy video driver for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from core.game import Game
except ImportError:
    # Handle case where run from root
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
    from core.game import Game

class TestGameLaunch(unittest.TestCase):
    def test_game_init(self):
        """Test that Game class initializes correctly."""
        print("Testing Game Initialization...")
        try:
            # We mock pygame.display.set_mode to avoid window creation issues if dummy driver fails
            # But usually dummy driver is enough.
            # However, GameSetup calls pygame.display.set_mode.
            
            game = Game()
            self.assertIsNotNone(game.player, "Player should be initialized")
            self.assertIsNotNone(game.world, "World should be initialized")
            self.assertIsNotNone(game.renderer, "Renderer should be initialized")
            self.assertIsNotNone(game.clock, "Clock should be initialized")
            
            print("Game initialized successfully.")
            
        except Exception as e:
            self.fail(f"Game initialization failed with error: {e}")
        finally:
            pygame.quit()

if __name__ == '__main__':
    unittest.main()
