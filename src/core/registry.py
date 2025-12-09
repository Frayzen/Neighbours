import json
import os
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
        
        for name, props in data.items():
            Registry._environments[name] = Environment(
                name=name,
                walkable=props['walkable'],
                symbol=props['symbol'],
                color=tuple(props['color'])
            )
        print(f"Loaded {len(Registry._environments)} environments.")

    @staticmethod
    def get_environment(name):
        return Registry._environments.get(name)
