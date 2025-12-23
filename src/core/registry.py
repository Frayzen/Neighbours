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

        with open(filepath, 'r') as f:
            data = json.load(f)
        
        base_path = os.path.dirname(filepath)

        for name, props in data.items():
            cell = Cell(
                name=name,
                walkable=props['walkable'],
                texture_path=props.get('texture_path', ""),
                color=tuple(props['color']),
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
                        print(f"Loaded texture for {name} from {full_path}")
                    except pygame.error as e:
                        print(f"Failed to load texture for {name} from {full_path}: {e}")
                else:
                    print(f"Texture not found for {name}: {full_path}")

            Registry._cells[name] = cell
            
        print(f"Loaded {len(Registry._cells)} cells.")

    @staticmethod
    def load_enemies(filepath):
        if not os.path.exists(filepath):
            print(f"Error: Enemy file not found at {filepath}")
            return

        with open(filepath, 'r') as f:
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
                        print(f"Loaded texture for enemy {name} from {full_path}")
                    except pygame.error as e:
                        print(f"Failed to load texture for enemy {name} from {full_path}: {e}")
                else:
                    print(f"Texture not found for enemy {name}: {full_path}")
            
            props['texture'] = texture
            Registry._enemies[name] = props
            
        print(f"Loaded {len(Registry._enemies)} enemy types.")

    @staticmethod
    def get_cell(name):
        return Registry._cells.get(name)

    @staticmethod
    def get_enemy_config(name):
        return Registry._enemies.get(name)

    @staticmethod
    def get_enemy_types():
        return list(Registry._enemies.keys())
