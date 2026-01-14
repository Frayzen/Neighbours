import math
import pygame
from config.settings import CELL_SIZE

class RaycastResult:
    def __init__(self, distance, type_id):
        self.distance = distance
        self.type_id = type_id # 0: Nothing/MaxDist, 1: Wall, 2: Opponent

def cast_ray(game, start_x, start_y, angle_rad, max_dist, opponent=None):
    """
    Casts a ray from (start_x, start_y) in direction angle_rad.
    Returns a float: normalized distance (1.0 = close, 0.0 = far/nothing).
    
    If check_walls is True, stops at walls.
    If check_opponent is True, checks intersection with opponent.
    
    For simplicity in this phase, we return a normalized value where:
    - 1.0 means touching
    - 0.0 means at or beyond max_dist
    """
    
    # Step size for ray marching (smaller = more precision, more expensive)
    step_size = CELL_SIZE / 2.0 
    
    # Direction vector
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    
    current_dist = 0.0
    cx = start_x
    cy = start_y
    
    player_rect = None
    if opponent:
        # Create a rect for the opponent for collision checking
        # Assuming opponent has x, y, width (size), height (size)
        # Using a slightly larger hit box for visibility leniency? Or exact.
        player_rect = pygame.Rect(opponent.x, opponent.y, opponent.w * CELL_SIZE, opponent.h * CELL_SIZE)

    found_wall = False
    found_opponent = False
    
    while current_dist < max_dist:
        # Update position
        cx += dx * step_size
        cy += dy * step_size
        current_dist += step_size
        
        # Check Bounds
        if cx < 0 or cx >= game.world.width * CELL_SIZE or cy < 0 or cy >= game.world.height * CELL_SIZE:
             break # Out of bounds (Hit "Wall" effectively or just void)
             
        # Check Wall
        # Convert px to grid
        gx = int(cx // CELL_SIZE)
        gy = int(cy // CELL_SIZE)
        
        cell = game.world.get_cell(gx, gy)
        if cell and not cell.walkable: 
            found_wall = True
            # For wall ray, we stop here.
            # But wait, are we casting separate rays or one ray for everything?
            # The plan says "Call ... for Walls" and "Call ... for Opponent". 
            # So we should probably support modes or return what we hit first?
            # Creating separate functions might be cleaner, but let's stick to one engine.
            pass

        if found_wall:
             return 1.0 - (current_dist / max_dist)
             
    return 0.0

def cast_wall_ray(game, start_x, start_y, angle_rad, max_dist):
    """
    Casts a ray specifically looking for walls.
    Returns normalized proximity (1.0 = close, 0.0 = far).
    """
    step_size = CELL_SIZE / 2.0
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    
    current_dist = 0
    cx = start_x
    cy = start_y
    
    while current_dist < max_dist:
        cx += dx * step_size
        cy += dy * step_size
        current_dist += step_size
        
        gx = int(cx // CELL_SIZE)
        gy = int(cy // CELL_SIZE)
        
        # Check OOB
        if gx < 0 or gx >= game.world.width or gy < 0 or gy >= game.world.height:
            return 1.0 - (current_dist / max_dist) # Treated as wall
            
        cell = game.world.get_cell(gx, gy)
        if cell and not cell.walkable:
            return 1.0 - (current_dist / max_dist)
            
    return 0.0

def cast_entity_ray(game, start_x, start_y, angle_rad, max_dist, entity):
    """
    Casts a ray looking for a specific entity (e.g. opponent).
    Ignores walls (X-ray vision?) or stops at walls? 
    Usually, vision stops at walls. So we must check walls too.
    """
    if not entity: return 0.0
    
    step_size = CELL_SIZE / 2.0
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    
    current_dist = 0
    cx = start_x
    cy = start_y
    
    entity_rect = pygame.Rect(entity.x, entity.y, entity.w * CELL_SIZE, entity.h * CELL_SIZE)
    
    while current_dist < max_dist:
        cx += dx * step_size
        cy += dy * step_size
        current_dist += step_size
        
        # 1. Wall Check (Occlusion)
        gx = int(cx // CELL_SIZE)
        gy = int(cy // CELL_SIZE)
        if gx < 0 or gx >= game.world.width or gy < 0 or gy >= game.world.height:
            return 0.0 # Wall/World Edge blocks view of entity
        
        cell = game.world.get_cell(gx, gy)
        if cell and not cell.walkable:
            return 0.0 # Wall blocked view
            
        # 2. Entity Check
        # Simple point in rect check for the ray tip
        if entity_rect.collidepoint(cx, cy):
            return 1.0 - (current_dist / max_dist)
            
    return 0.0
