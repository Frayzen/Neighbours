import pygame
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from entities.player import Player
from config.settings import CELL_SIZE

# Mock Game class
class MockGame:
    def __init__(self):
        self.screen = None
        self.damage_texts = None

def verify_player_texture():
    pygame.init()
    # Initialize display (required for loading images with convert_alpha which player init does)
    pygame.display.set_mode((100, 100))
    
    game = MockGame()
    
    # Try to init player
    # x,y,size,speed
    try:
        player = Player(game, 0, 0, 1, 5)
        
        if player.image is None:
            print("FAILURE: player.image is None")
            return False
            
        print(f"SUCCESS: Player image loaded. Size: {player.image.get_size()}")
        
        expected_w = int(1 * CELL_SIZE)
        expected_h = int(1 * CELL_SIZE)
        
        if player.image.get_size() != (expected_w, expected_h):
             print(f"WARNING: Image size {player.image.get_size()} does not match expected ({expected_w}, {expected_h})")
        
        return True
        
    except Exception as e:
        print(f"FAILURE: Exception initializing player: {e}")
        return False
    finally:
        pygame.quit()

if __name__ == "__main__":
    if verify_player_texture():
        sys.exit(0)
    else:
        sys.exit(1)
