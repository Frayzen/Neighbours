from config.settings import CELL_SIZE


def check_collision(x, y, width, height, bounds, world):
    min_x, min_y, max_x, max_y = bounds

    pixel_w = width * CELL_SIZE
    pixel_h = height * CELL_SIZE

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
        (x + pixel_w - 0.1, y + pixel_h - 0.1),
    ]

    for cx, cy in corners:
        grid_x = int((cx - min_x) / CELL_SIZE)
        grid_y = int((cy - min_y) / CELL_SIZE)

        cell_data = world.get_cell_full(grid_x, grid_y)
        if cell_data:
            cell, offset = cell_data
            if not cell.walkable:
                # Return cell and its origin grid coordinates
                origin_x = grid_x - offset[0]
                origin_y = grid_y - offset[1]
                return (cell, origin_x, origin_y)

    return False

def has_line_of_sight(start_x, start_y, end_x, end_y, world):
    """
    Checks if there is a clear line of sight between two points using Bresenham's line algorithm.
    Coordinates are in pixels.
    """
    x0 = int(start_x / CELL_SIZE)
    y0 = int(start_y / CELL_SIZE)
    x1 = int(end_x / CELL_SIZE)
    y1 = int(end_y / CELL_SIZE)

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        # Check current cell
        cell = world.get_cell(x0, y0)
        if cell and not cell.walkable:
            return False

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
            
    return True
