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
        Now includes World and LevelManager.
        """
        data = {
            "player": game.player,
            "gridObjects": game.gridObjects,
            "camera": game.camera,
            "level_manager": game.level_manager,
            "world": game.world  
        }
        
        try:
            with open(SAVE_FILE_PATH, "wb") as f:
                pickle.dump(data, f)
            debug.log("Game Saved Successfully!")
        except Exception as e:
            debug.log(f"Failed to save game: {e}")
            import traceback
            traceback.print_exc()

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
            
            # Restore Level Manager & World
            if "level_manager" in data:
                game.level_manager = data["level_manager"]
            
            if "world" in data:
                game.world = data["world"]
            
            # Clear old VFX
            from core.vfx import vfx_manager
            vfx_manager.effects.clear()
            
            # Re-link game reference and restore transients
            
                     # World Texture Reload
            if game.world:
                 from core.registry import Registry
                 config_dir = os.path.join(BASE_DIR, "config")
                 
                 # Flatten grid for iteration
                 for row in game.world.grid:
                     for cell_data in row:
                         cell, _ = cell_data
                         if cell and cell.texture_path and not cell.texture:
                             # Resolve path relative to config dir (mirroring Registry logic)
                             full_path = cell.texture_path
                             if not os.path.isabs(full_path):
                                 full_path = os.path.normpath(os.path.join(config_dir, full_path))
                             
                             import pygame
                             try:
                                 if os.path.isdir(full_path):
                                     # Load directory of textures (e.g. Ground)
                                     cell.textures = []
                                     for file in os.listdir(full_path):
                                         if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                             tex_path = os.path.join(full_path, file)
                                             tex = pygame.image.load(tex_path).convert_alpha()
                                             cell.textures.append(tex)
                                     
                                     if cell.textures:
                                         # Select random or first? 
                                         # Ideally we should have saved the index or specific texture name if we wanted exact restore.
                                         # But for now, picking one (or re-randomizing) is better than invisible.
                                         # Logic in World generator might have picked specific one? 
                                         # Cell doesn't store WHICH texture variant it picked, only the list.
                                         # Actually Registry.load_cells just fills the list. World gen picks one?
                                         # If World gen picked one and assigned to .texture, we lost that info unless we saved an index.
                                         # For Ground, it changes rarely, so random pick is okay? 
                                         # Or just use the first one like Registry does by default?
                                         import random
                                         cell.texture = random.choice(cell.textures)
                                 
                                 elif os.path.exists(full_path):
                                     cell.texture = pygame.image.load(full_path).convert_alpha()
                             except Exception as e:
                                 debug.log(f"Failed to reload texture for cell {cell.name} at {full_path}: {e}")
            
            # Renderer Reload
            game.renderer.reload_world()

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
            import traceback
            traceback.print_exc()
            # SaveManager.delete_save_file() # Optional: Disable auto-delete for debug
            return False

    @staticmethod
    def has_save_file():
        return os.path.exists(SAVE_FILE_PATH)

    @staticmethod
    def delete_save_file():
        if os.path.exists(SAVE_FILE_PATH):
            os.remove(SAVE_FILE_PATH)
            debug.log("Save file deleted.")
