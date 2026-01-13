import pygame
import math
from entities.base import GridObject
from config.settings import CELL_SIZE

class Projectile(GridObject):
    def __init__(self, x, y, direction, speed, damage, owner_type, texture=None, behavior="LINEAR", visual_type="ARROW", target_pos=None, color=(255, 255, 0), explode_radius=0, start_delay=0):
        super().__init__(x, y, 0.5, 0.5, color=color) 
        
        # Robust direction handling
        vec = pygame.math.Vector2(direction) if direction else pygame.math.Vector2(0,0)
        if vec.length_squared() > 0:
            self.direction = vec.normalize()
        else:
            self.direction = pygame.math.Vector2(0,0)
        self.speed = speed
        self.damage = damage
        self.owner_type = owner_type # "player" or "enemy"
        self.texture = texture
        self.behavior = behavior
        self.visual_type = visual_type
        self.target_pos = pygame.math.Vector2(target_pos) if target_pos else None
        self.explode_radius = explode_radius
        self.should_explode = False
        self.start_delay = start_delay
        
        # Visual state
        self.anim_timer = 0
        


    def update(self):
        if self.start_delay > 0:
            self.start_delay -= 16 # Approx ms per frame @ 60fps? Or just use frames if logic is fixed step.
            # actually logic update interval is varying but let's assume ms if passed as ms, or frames if passed as frames.
            # Existing code for timers uses pygame.time.get_ticks() which is ms.
            # But update is called every frame. 
            # If I want precise timing, I should decrease by delta time. 
            # But delta time isn't passed to update() in this game engine logic (yet).
            # Looking at logic.py loop, it runs as fast as possible or capped?
            # main.py usually caps FPS.
            # Let's assume start_delay is in "updates/frames" for simplicity or just decrement by 1 if usage is "delay N frames".
            # User asked for "slight delay".
            # Let's treat start_delay as integer frames for now.
            self.start_delay -= 1
            return
        if self.behavior == "TARGET_EXPLOSION" and self.target_pos:
            # Move towards target
            curr_pos = pygame.math.Vector2(self.x, self.y)
            dist = curr_pos.distance_to(self.target_pos)
            
            if dist <= self.speed:
                # Reached target
                self.x = self.target_pos.x
                self.y = self.target_pos.y
                self.should_explode = True
            else:
                # Move
                direction = (self.target_pos - curr_pos).normalize()
                self.x += direction.x * self.speed
                self.y += direction.y * self.speed
        else:
            # Linear movement
            self.x += self.direction.x * self.speed
            self.y += self.direction.y * self.speed

    def draw(self, screen):
        if self.start_delay > 0: return

        self.anim_timer += 1
        
        cx = int(self.x + (self.w * CELL_SIZE)/2)
        cy = int(self.y + (self.h * CELL_SIZE)/2)
        
        if self.visual_type == "FIREBALL":
            # Draw fireball visual
            # Core
            pygame.draw.circle(screen, (255, 100, 0), (cx, cy), 6)
            # Outer bloom
            pygame.draw.circle(screen, (255, 50, 0), (cx, cy), 10 + math.sin(self.anim_timer * 0.2) * 2, 2)
            
        elif self.visual_type == "METEOR":
            # HUGE Fireball
            # Core
            pygame.draw.circle(screen, (255, 69, 0), (cx, cy), 15) # Bigger Core
            # Inner Core (Hot)
            pygame.draw.circle(screen, (255, 255, 0), (cx, cy), 8) 
            # Outer bloom (Pulsing)
            pulse = math.sin(self.anim_timer * 0.3) * 4
            pygame.draw.circle(screen, (139, 0, 0), (cx, cy), 20 + pulse, 3) # Dark red outer ring
            
        elif self.visual_type == "ARROW":
             # Procedural Arrow
             # Calculate angle
             angle = math.atan2(self.direction.y, self.direction.x)
             
             # Define arrow shape (triangle) pointing right at (0,0)
             # Length 15, Width 8
             points = [
                 (10, 0),   # Tip
                 (-10, -5), # Back Top
                 (-5, 0),   # Notch
                 (-10, 5)   # Back Bottom
             ]
             
             # Rotate and translate points
             rotated_points = []
             for px, py in points:
                 # Rotate
                 # x' = x cos θ - y sin θ
                 # y' = x sin θ + y cos θ
                 rx = px * math.cos(angle) - py * math.sin(angle)
                 ry = px * math.sin(angle) + py * math.cos(angle)
                 
                 rotated_points.append((cx + rx, cy + ry))
                 
             pygame.draw.polygon(screen, self.color, rotated_points)
             
        else:
            # Default
            pygame.draw.circle(screen, self.color, (cx, cy), 4)
