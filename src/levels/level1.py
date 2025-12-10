from core.registry import Registry

def setup(world):
    # Get cells from Registry
    grass = Registry.get_cell("Grass")
    wall = Registry.get_cell("Wall")
    water = Registry.get_cell("Water")
    door = Registry.get_cell("Door")

    # Fill background with grass
    for y in range(world.height):
        for x in range(world.width):
            world.set_cell(x, y, grass)

    # Add border walls
    for x in range(world.width):
        world.set_cell(x, 0, wall)
        world.set_cell(x, world.height - 1, wall)
    
    for y in range(world.height):
        world.set_cell(0, y, wall)
        world.set_cell(world.width - 1, y, wall)

    # Create a simple walled area
    for i in range(5, 15):
        world.set_cell(i, 5, wall)
        world.set_cell(i, 15, wall)
    
    for i in range(5, 16):
        world.set_cell(5, i, wall)
        world.set_cell(14, i, wall)

    # Add a small pond
    world.set_cell(20, 20, water)
    world.set_cell(21, 20, water)
    world.set_cell(20, 21, water)
    world.set_cell(21, 21, water)

    # Add a door
    if door:
        world.set_cell(10, 5, door)
