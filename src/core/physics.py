
def check_collision(x, y, width, height, bounds, world, tile_size):
    min_x, min_y, max_x, max_y = bounds
    
    pixel_w = width * tile_size
    pixel_h = height * tile_size

    # Constrain to bounds first
    if x < min_x or x > max_x - pixel_w:
        return True
    if y < min_y or y > max_y - pixel_h:
        return True

    # Check corners against world grid
    corners = [
        (x, y),
        (x + pixel_w - 0.1, y),
        (x, y + pixel_h - 0.1),
        (x + pixel_w - 0.1, y + pixel_h - 0.1)
    ]

    for cx, cy in corners:
        grid_x = int((cx - min_x) / tile_size)
        grid_y = int((cy - min_y) / tile_size)
        
        cell_data = world.get_cell_full(grid_x, grid_y)
        if cell_data:
            cell, offset = cell_data
            if not cell.walkable:
                # Return cell and its origin grid coordinates
                origin_x = grid_x - offset[0]
                origin_y = grid_y - offset[1]
                return (cell, origin_x, origin_y)
    
    return False
