
import sys
import os
import pygame

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from core.game import Game
from core.input_state import InputState

def verify_headless():
    print("Initializing Headless Game...")
    try:
        # Initialize Game with headless=True
        # Note: We might need to modify Game to accept headless arg if it doesn't already, 
        # or rely on the flag being set in __init__?
        # Looking at previous file views, Game seems to take headless in __init__?
        # Let's check Game.__init__ signature if it fails, but for now assume yes based on plan.
        
        # Actually, let's peek at Game.__init__ first or trust my previous modifications?
        # My plan said: "Initialize Game(headless=True)".
        # Previous edits for Player checked `getattr(game, 'headless', False)`.
        # So I need to ensure Game accepts it.
        
        game = Game(headless=True)
        print("Game initialized.")
        
        if game.headless:
            print("PASS: Game is in headless mode.")
        else:
            print("FAIL: Game is NOT in headless mode.")
            return

        # Check Player Texture
        if game.player.texture is None:
            print("PASS: Player texture is None (not loaded).")
        else:
            print("FAIL: Player texture IS loaded.")
            
        # Run a few updates
        print("Running updates...")
        input_state = InputState()
        input_state.move_x = 1
        
        for i in range(10):
            game.player.update(input_state, enemies=[])
            game.player.move(input_state, game.world)
            
        print("PASS: Updates ran without error.")
        print("Headless verification SUCCESS.")

    except Exception as e:
        print(f"FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_headless()
