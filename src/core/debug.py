import pygame
import time

class DebugOverlay:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugOverlay, cls).__new__(cls)
            cls._instance.messages = []
            cls._instance.font = None
        return cls._instance

    def log(self, text, duration=3.0):
        """Adds a message to the debug overlay."""
        expiration = time.time() + duration
        self.messages.append((text, expiration))
        print(f"[DEBUG] {text}")  # Also print to console

    def draw(self, surface):
        """Draws active messages to the surface."""
        if self.font is None:
            self.font = pygame.font.SysFont("Arial", 20)

        current_time = time.time()
        # Remove expired messages
        self.messages = [msg for msg in self.messages if msg[1] > current_time]

        y_offset = 10
        for text, _ in self.messages:
            text_surface = self.font.render(str(text), True, (255, 255, 255))
            
            # Draw background for better readability
            bg_rect = text_surface.get_rect(topleft=(10, y_offset))
            bg_surface = pygame.Surface((bg_rect.width + 4, bg_rect.height + 4))
            bg_surface.set_alpha(180) # Semi-transparent
            bg_surface.fill((0, 0, 0))
            
            surface.blit(bg_surface, (8, y_offset - 2))
            surface.blit(text_surface, (10, y_offset))
            
            y_offset += 25

# Global accessor
debug = DebugOverlay()
