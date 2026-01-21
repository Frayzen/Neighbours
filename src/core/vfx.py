import pygame

class VFXManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VFXManager, cls).__new__(cls)
            cls._instance.effects = []
        return cls._instance

    def add_effect(self, effect):
        self.effects.append(effect)

    def update(self):
        current_time = pygame.time.get_ticks()
        self.effects = [e for e in self.effects if e.is_active(current_time)]

    def draw(self, surface, camera):
        for effect in self.effects:
            effect.draw(surface, camera)

class VisualEffect:
    def __init__(self, duration):
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

    def is_active(self, current_time):
        return current_time - self.start_time < self.duration

    def draw(self, surface, camera):
        pass

class ExplosionEffect(VisualEffect):
    def __init__(self, x, y, radius, color=(255, 100, 0), duration=500):
        super().__init__(duration)
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def draw(self, surface, camera):
        # Calculate progress (0.0 to 1.0)
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(1.0, max(0.0, elapsed / self.duration))
        
        # Fade out alpha
        alpha = int(255 * (1 - progress))
        
        # Expanding radius
        current_radius = self.radius * (0.5 + 0.5 * progress)
        
        # Draw circle
        size = int(current_radius * 2) + 4 # Add padding
        if size <= 0: return

        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (size // 2, size // 2), current_radius)
        # Apply camera offset
        draw_x = self.x - camera.x
        draw_y = self.y - camera.y
        surface.blit(s, (draw_x - size // 2, draw_y - size // 2))

class SlashEffect(VisualEffect):
    def __init__(self, x, y, target_x, target_y, width=5, color=(255, 255, 255), duration=200):
        super().__init__(duration)
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.width = width
        self.color = color

    def draw(self, surface, camera):
        # Apply camera offset
        start_pos = (self.x - camera.x, self.y - camera.y)
        end_pos = (self.target_x - camera.x, self.target_y - camera.y)
        pygame.draw.line(surface, self.color, start_pos, end_pos, self.width)

# Global accessor
vfx_manager = VFXManager()
