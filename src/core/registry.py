import json
import os
import pygame
from core.world import Cell

class Registry:
    _cells = {}
    _enemies = {}

    @staticmethod
    def load_cells(filepath):
        if not os.path.exists(filepath):
            print(f"Error: Environment file not found at {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        base_path = os.path.dirname(filepath)

        for name, props in data.items():
            cell = Cell(
                name=name,
                walkable=props.get('walkable', True),
                texture_path=props.get('texture_path', ""),
                color=tuple(props.get('color', (255, 255, 255))),
                width=props.get('width', 1),
                height=props.get('height', 1),
                trigger=props.get('trigger', None)
            )
            
            # Load texture if path is provided
            if cell.texture_path:
                full_path = os.path.normpath(os.path.join(base_path, cell.texture_path))
                if os.path.exists(full_path):
                    try:
                        cell.texture = pygame.image.load(full_path).convert_alpha()
                        # print(f"Loaded texture for {name} from {full_path}")
                    except pygame.error as e:
                        # print(f"Failed to load texture for {name} from {full_path}: {e}")
                        pass
                else:
                    # print(f"Texture not found for {name}: {full_path}")
                    pass

            Registry._cells[name] = cell
            
        # print(f"Loaded {len(Registry._cells)} cells.")

    @staticmethod
    def load_enemies(filepath):
        if not os.path.exists(filepath):
            print(f"Error: Enemy file not found at {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        base_path = os.path.dirname(filepath)

        for name, props in data.items():
            # Store raw properties, textures will be loaded when needed or pre-loaded here
            # For now, let's pre-load the texture if it exists
            texture = None
            texture_path = props.get('texture_path', "")
            if texture_path:
                full_path = os.path.normpath(os.path.join(base_path, texture_path))
                if os.path.exists(full_path):
                    try:
                        texture = pygame.image.load(full_path).convert_alpha()
                        # print(f"Loaded texture for enemy {name} from {full_path}")
                    except pygame.error as e:
                        # print(f"Failed to load texture for enemy {name} from {full_path}: {e}")
                        pass
                else:
                    # print(f"Texture not found for enemy {name}: {full_path}")
                    pass
            
            props['texture'] = texture
            Registry._enemies[name] = props
            
        # print(f"Loaded {len(Registry._enemies)} enemy types.")

    @staticmethod
    def get_cell(name):
        return Registry._cells.get(name)

    @staticmethod
    def get_enemy_config(name):
        return Registry._enemies.get(name)

    @staticmethod
    def get_enemy_types():
        return list(Registry._enemies.keys())

    _textures = {}

    @staticmethod
    def preload_textures(base_dir):
        """
        Recursively load all images from the assets directory.
        """
        assets_dir = os.path.join(base_dir, "assets")
        if not os.path.exists(assets_dir):
            print(f"Warning: Assets directory not found at {assets_dir}")
            return

        print(f"Preloading textures from {assets_dir}...")
        count = 0
        for root, _, files in os.walk(assets_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    full_path = os.path.join(root, file)
                    # Normalize path to match how other systems might request it
                    # We store it keyed by the absolute path for simplicity and exact matching
                    # OR we could store relative to base_dir
                    
                    try:
                        norm_path = os.path.normpath(full_path)
                        # Load and cache
                        tex = pygame.image.load(norm_path).convert_alpha()
                        Registry._textures[norm_path] = tex
                        count += 1
                    except pygame.error as e:
                        # print(f"Failed to preload {full_path}: {e}")
                        pass
        
        # print(f"Preloaded {count} textures.")

    @staticmethod
    def get_texture(path):
        """
        Get a texture from cache or load it if missing.
        Path should be absolute or relative to CWD.
        """
        norm_path = os.path.normpath(path)
        
        if norm_path in Registry._textures:
            return Registry._textures[norm_path]
        
        # Not in cache, try to load
        if os.path.exists(norm_path):
             try:
                # print(f"Cache Miss: Loading {norm_path} on demand.")
                tex = pygame.image.load(norm_path).convert_alpha()
                Registry._textures[norm_path] = tex
                return tex
             except pygame.error as e:
                # print(f"Failed to load texture {norm_path}: {e}")
                return None
        else:
            # Try checking relative to assets if direct path fails? 
            # For now, assume path is correct.
            # print(f"Texture path not found: {norm_path}")
            return None
