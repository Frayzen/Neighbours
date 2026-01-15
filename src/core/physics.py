from config.settings import CELL_SIZE

def check_collision(x, y, width, height, bounds, world):
    min_x, min_y, max_x, max_y = bounds
    pixel_w = width * CELL_SIZE
    pixel_h = height * CELL_SIZE

    # 1. Fast Bounds Check
    if x < min_x or x > max_x - pixel_w: return True
    if y < min_y or y > max_y - pixel_h: return True

    # 2. Optimized Grid Check (No List Creation)
    start_gx = int((x - min_x) / CELL_SIZE)
    end_gx = int((x + pixel_w - 0.01 - min_x) / CELL_SIZE)
    start_gy = int((y - min_y) / CELL_SIZE)
    end_gy = int((y + pixel_h - 0.01 - min_y) / CELL_SIZE)
    
    grid = world.grid # Cache reference
    
    for gy in range(start_gy, end_gy + 1):
        for gx in range(start_gx, end_gx + 1):
            try:
                # Direct access is much faster than get_cell()
                cell_data = grid[gy][gx]
                if not cell_data[0].walkable:
                    cell, offset = cell_data
                    return (cell, gx - offset[0], gy - offset[1])
            except IndexError:
                pass 
    return False

def has_line_of_sight(start_x, start_y, end_x, end_y, world):
    x0, y0 = int(start_x / CELL_SIZE), int(start_y / CELL_SIZE)
    x1, y1 = int(end_x / CELL_SIZE), int(end_y / CELL_SIZE)
    
    dx = abs(x1 - x0); dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx - dy
    grid = world.grid

    while True:
        try:
            if not grid[y0][x0][0].walkable: return False
        except IndexError: return False

        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 < dx: err += dx; y0 += sy
            
    return True