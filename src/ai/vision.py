import math
from config.settings import CELL_SIZE

def cast_wall_ray(game, start_x, start_y, angle_rad, max_dist):
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    map_x, map_y = int(start_x / CELL_SIZE), int(start_y / CELL_SIZE)
    
    # DDA Setup
    delta_dist_x = abs(1.0 / cos_a) if abs(cos_a) > 1e-10 else 1e30
    delta_dist_y = abs(1.0 / sin_a) if abs(sin_a) > 1e-10 else 1e30
    step_x = 1 if cos_a >= 0 else -1
    step_y = 1 if sin_a >= 0 else -1
    
    side_dist_x = (map_x + 1.0 - start_x / CELL_SIZE) * delta_dist_x if step_x > 0 else (start_x / CELL_SIZE - map_x) * delta_dist_x
    side_dist_y = (map_y + 1.0 - start_y / CELL_SIZE) * delta_dist_y if step_y > 0 else (start_y / CELL_SIZE - map_y) * delta_dist_y
        
    grid = game.world.grid
    w, h = game.world.width, game.world.height
    
    for _ in range(int(max_dist / CELL_SIZE) + 4):
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x; map_x += step_x
            dist = side_dist_x - delta_dist_x
        else:
            side_dist_y += delta_dist_y; map_y += step_y
            dist = side_dist_y - delta_dist_y
            
        pixel_dist = dist * CELL_SIZE
        if pixel_dist > max_dist: return 0.0
        
        if not (0 <= map_x < w and 0 <= map_y < h): return 1.0 - (pixel_dist / max_dist)
        if not grid[map_y][map_x][0].walkable: return 1.0 - (pixel_dist / max_dist)

    return 0.0

def cast_entity_ray(game, start_x, start_y, angle_rad, max_dist, entity):
    if not entity: return 0.0
    
    # 1. Check Wall Occlusion (Reuse optimized wall ray)
    wall_val = cast_wall_ray(game, start_x, start_y, angle_rad, max_dist)
    dist_to_wall = max_dist * (1.0 - wall_val) if wall_val > 0 else max_dist
    
    # 2. Math Intersection (Ray vs Rect) - No Looping!
    dx, dy = math.cos(angle_rad), math.sin(angle_rad)
    rx, ry = entity.x, entity.y
    rw, rh = entity.w * CELL_SIZE, entity.h * CELL_SIZE
    
    p = [-dx, dx, -dy, dy]
    q = [start_x - rx, rx + rw - start_x, start_y - ry, ry + rh - start_y]
    
    t_min, t_max = 0.0, max_dist
    for i in range(4):
        if p[i] == 0: 
            if q[i] < 0: return 0.0
        else:
            t = q[i] / p[i]
            if p[i] < 0:
                if t > t_max: return 0.0
                if t > t_min: t_min = t
            else:
                if t < t_min: return 0.0
                if t < t_max: t_max = t
                
    if t_min >= max_dist: return 0.0
    
    # 3. Final Check
    if t_min < dist_to_wall:
        return 1.0 - (t_min / max_dist)
    return 0.0