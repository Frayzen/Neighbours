from core.world import World
from levels import level1

def load_level(level_id):
    """
    Loads a specific level based on the ID provided.
    Returns a populated World object.
    """
    world = World()
    
    if level_id == 1:
        level1.setup(world)

    return world
