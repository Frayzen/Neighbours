from core.registry import Registry

def setup(world):
    # Get environments from Registry
    grass = Registry.get_environment("Grass")
    wall = Registry.get_environment("Wall")
    water = Registry.get_environment("Water")
    door = Registry.get_environment("Door")

    # Fill background with grass
    for y in range(world.height):
        for x in range(world.width):
            world.set_environment(x, y, grass)

    # Add border walls
    for x in range(world.width):
        world.set_environment(x, 0, wall)
        world.set_environment(x, world.height - 1, wall)
    
    for y in range(world.height):
        world.set_environment(0, y, wall)
        world.set_environment(world.width - 1, y, wall)

    # Create a simple walled area
    for i in range(5, 15):
        world.set_environment(i, 5, wall)
        world.set_environment(i, 15, wall)
    
    for i in range(5, 16):
        world.set_environment(5, i, wall)
        world.set_environment(14, i, wall)

    # Add a small pond
    world.set_environment(20, 20, water)
    world.set_environment(21, 20, water)
    world.set_environment(20, 21, water)
    world.set_environment(21, 21, water)

    # Add a door
    world.set_environment(10, 5, door)
