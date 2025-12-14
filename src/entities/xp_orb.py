import pygame
import math
from entities.base import GridObject
from core.debug import debug

class XPOrb(GridObject):
    def __init__(self, x, y, value):
        # Initialize with a small size (e.g., 4x4 pixels or half tile)
        # We don't really use w/h for collision in the grid the same way, 
        # but let's say it's 0.5 tile size for visual.
        super().__init__(x, y, 0.5, 0.5, color=(0, 255, 255)) 
        self.value = value
        self.creation_time = pygame.time.get_ticks()
        self.pulse_speed = 0.005
        
        # Magnet physics
        self.velocity = pygame.math.Vector2(0, 0)
        self.max_speed = 8
        self.acceleration = 0.5

    def update(self, target_pos=None):
        # We can implement the magnet movement logic here if we pass the player pos
        # But the plan suggested GameLogic handles it or calls a specific method.
        # Let's support an explicit "move_towards" method called by logic.
        pass

    def move_towards(self, target_x, target_y):
        # Direct movement behavior (no inertia)
        target = pygame.math.Vector2(target_x, target_y)
        pos = pygame.math.Vector2(self.x, self.y)
        
        direction = target - pos
        dist = direction.length()
        
        if dist > 0:
            direction = direction.normalize()
            
            # Move straight to target with high speed (or increasing speed based on closeness)
            # "Easier" pickup might imply fast snap.
            speed = 12 # Higher constant speed for snappy pickup
            
            # If close enough to overshoot, just snap to position (handled by collision logic in main loop usually, 
            # but let's ensure we move closely)
            move_dist = min(dist, speed)
            
            self.x += direction.x * move_dist
            self.y += direction.y * move_dist

    def draw(self, surface, tile_size):
        # Glittering effect
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.creation_time
        
        # Pulse size
        base_radius = (self.w * tile_size) / 2
        pulse = math.sin(elapsed * self.pulse_speed) * 2 # oscillating between -2 and 2
        radius = max(2, base_radius + pulse)
        
        # Pulse color (Cyan to White)
        color_val = int(127 + 127 * math.sin(elapsed * self.pulse_speed * 2))
        color = (color_val, 255, 255)
        
        center_x = self.x + (self.w * tile_size) / 2
        center_y = self.y + (self.h * tile_size) / 2
        
        # Draw glowing halo (transparent)
        # Pygame doesn't do accurate alpha on direct draw.circle without surface
        # For simplicity, just draw concentric circles
        pygame.draw.circle(surface, (0, 100, 100), (center_x, center_y), radius + 2)
        pygame.draw.circle(surface, color, (center_x, center_y), radius)
