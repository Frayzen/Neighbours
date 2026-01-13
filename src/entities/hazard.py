import pygame
import random
from entities.base import GridObject
from config.settings import CELL_SIZE
from core.debug import debug

class FireHazard(GridObject):
    def __init__(self, x, y, duration_min, duration_max, damage, game):
        # Fire is typically 1x1 tile size
        super().__init__(x, y, 1, 1, color=(255, 100, 0))
        self.game = game
        self.duration = random.randint(duration_min, duration_max)
        self.start_time = pygame.time.get_ticks()
        self.damage = damage
        self.damage_cooldown = 1000 # Damage once per second per tile? or static?
        self.last_damage_time = 0
        
        # Visuals
        self.flicker_timer = 0
        
        # Load Texture via Registry

        try:
            import os
            from core.registry import Registry
            
            path = os.path.normpath(os.path.join("src/assets/images/Lava.png"))
            
            raw_tex = Registry.get_texture(path)
            if raw_tex:
                 self.texture = pygame.transform.scale(raw_tex, (self.w * CELL_SIZE, self.h * CELL_SIZE))
            else:
                 # Fallback if not found (e.g. CWD mismatch)
                 # print(f"FireHazard: Texture not found in registry: {path}")
                 self.texture = None

        except Exception as e:
            # print(f"Failed to load Lava texture: {e}")
            self.texture = None

    def update(self, *args, **kwargs):
        current_time = pygame.time.get_ticks()
        
        # Check lifetime
        if current_time - self.start_time > self.duration:
            if self in self.game.gridObjects:
                self.game.gridObjects.remove(self)
            return

        # Check collision with player
        player_rect = pygame.Rect(
            self.game.player.x, 
            self.game.player.y, 
            self.game.player.w * CELL_SIZE, 
            self.game.player.h * CELL_SIZE
        )
        
        my_rect = pygame.Rect(
            self.x, 
            self.y, 
            self.w * CELL_SIZE, 
            self.h * CELL_SIZE
        )
        
        if player_rect.colliderect(my_rect):
            if current_time - self.last_damage_time > self.damage_cooldown:
                self.game.player.take_damage(self.damage)
                self.last_damage_time = current_time
                debug.log("Player burned by Final Ember!")

    def draw(self, screen):
        if self.texture:
             # Draw texture
             screen.blit(self.texture, (self.x, self.y))
        else:
             # Draw flickering fire (Fallback)
             self.flicker_timer += 1
             
             alpha = random.randint(150, 255)
             color = (255, random.randint(50, 150), 0)
             
             surf = pygame.Surface((self.w * CELL_SIZE, self.h * CELL_SIZE), pygame.SRCALPHA)
             surf.fill((*color, alpha))
             
             screen.blit(surf, (self.x, self.y))
