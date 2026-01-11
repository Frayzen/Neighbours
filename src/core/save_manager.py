import pickle
import os
from config.settings import BASE_DIR
from core.debug import debug
"""Janis REISENAUER"""

SAVE_FILE_NAME = "savegame.pkl"
SAVE_FILE_PATH = os.path.join(BASE_DIR, SAVE_FILE_NAME)

class SaveManager:
    SAVE_FILE_PATH = SAVE_FILE_PATH # Expose for debug
    
    @staticmethod
    def save_game(game):
        """
        Serializes and saves the current game state.
        We explicitly choose what to save to avoid pickling the entire Game object 
        (which contains non-serializable Pygame surfaces).
        """
        data = {
            "player": game.player,
            "gridObjects": game.gridObjects,
            "camera": game.camera,
            "level": game.player.level,
            "xp": game.player.xp    
        }
        
        try:
            with open(SAVE_FILE_PATH, "wb") as f:
                pickle.dump(data, f)
            debug.log("Game Saved Successfully!")
        except Exception as e:
            debug.log(f"Failed to save game: {e}")

    @staticmethod
    def load_game(game):
        """
        Loads the game state from the save file and restores it into the given game instance.
        """
        if not os.path.exists(SAVE_FILE_PATH):
            debug.log("No save file found.")
            return False

        try:
            with open(SAVE_FILE_PATH, "rb") as f:
                data = pickle.load(f)
            
            # Restore state
            game.player = data["player"]
            game.gridObjects = data["gridObjects"]
            game.camera = data["camera"]
            
            # Clear old VFX
            from core.vfx import vfx_manager
            vfx_manager.effects.clear()
            
            # Re-link game reference and restore transients
            # Player
            game.player.game = game
            if hasattr(game.player, 'post_load'):
                game.player.post_load()
            
            # Entities
            for obj in game.gridObjects:
                if hasattr(obj, 'game'):
                    obj.game = game
                
                # Restore textures/behaviors
                if hasattr(obj, 'post_load'):
                    obj.post_load()
            
            debug.log("Game Loaded Successfully!")
            return True
        except Exception as e:
            debug.log(f"Failed to load game: {e}")
            return False

    @staticmethod
    def has_save_file():
        return os.path.exists(SAVE_FILE_PATH)

    @staticmethod
    def delete_save_file():
        if os.path.exists(SAVE_FILE_PATH):
            os.remove(SAVE_FILE_PATH)
            debug.log("Save file deleted.")
