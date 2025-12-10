import json
import os
import pygame
from core.world import Cell

class Registry:
    _cells = {}

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
                color=tuple(props['color'])
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
    def get_cell(name):
        return Registry._cells.get(name)
