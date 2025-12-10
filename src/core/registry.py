import json
import os
import pygame
from core.world import Environment

class Registry:
    _environments = {}

    @staticmethod
    def load_environments(filepath):
        if not os.path.exists(filepath):
            print(f"Error: Environment file not found at {filepath}")
            return

        with open(filepath, 'r') as f:
            data = json.load(f)
        
        base_path = os.path.dirname(filepath)

        for name, props in data.items():
            env = Environment(
                name=name,
                walkable=props['walkable'],
                texture_path=props.get('texture_path', ""),
                color=tuple(props['color']),
                width=props.get('width', 1),
                height=props.get('height', 1),
                trigger=props.get('trigger', None)
            )
            
            # Load texture if path is provided
            if env.texture_path:
                full_path = os.path.normpath(os.path.join(base_path, env.texture_path))
                if os.path.exists(full_path):
                    try:
                        env.texture = pygame.image.load(full_path).convert_alpha()
                        print(f"Loaded texture for {name} from {full_path}")
                    except pygame.error as e:
                        print(f"Failed to load texture for {name} from {full_path}: {e}")
                else:
                    print(f"Texture not found for {name}: {full_path}")

            Registry._environments[name] = env
            
        print(f"Loaded {len(Registry._environments)} environments.")

    @staticmethod
    def get_environment(name):
        return Registry._environments.get(name)
