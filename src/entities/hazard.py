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
            
            # Path logic: We need to construct the path that matches what preload_textures uses.
            # preload_textures walks src/assets.
            # So if we ask for "src/assets/images/Lava.png", it should be in cache if we run from root.
            # If we run from src, "assets/images/Lava.png" might be the key?
            # preload_textures uses full absolute path if os.walk returns valid roots.
            # Wait, os.walk returns relative paths? No, os.path.join(root, file)
            # If we pass BASE_DIR to preload, it uses that.
            
            # Let's try constructing the path assuming src/assets structure relative to CWD
            # or better, use relative path if we know CWD
            
            # Since we don't know exact CWD at runtime easily without helper, 
            # let's try the path referenced before: "src/assets/images/Lava.png"
            
            path = os.path.normpath(os.path.join("src/assets/images/Lava.png"))
            
            # If path resolution is tricky, Registry.get_texture will try to load it if missing.
            # But we want to hit the cache.
            # The cache key is os.path.normpath(full_path).
            # We need to construct the same full path.
            
            # Actually, let's just use "assets/images/Lava.png" and rely on Registry smarts?
            # Implemented Registry.get_texture takes a path, normalizes it, and checks cache.
            # If we pass "src/assets/images/Lava.png", it normalizes. 
            # Does preload use absolute paths? Yes "full_path = os.path.join(root, file)".
            # So we need to match that.
            
            # NOTE: For now, I will assume the previous path worked for loading, so it should work for lookup IF the preloader found it.
            
            raw_tex = Registry.get_texture(path)
            if raw_tex:
                 self.texture = pygame.transform.scale(raw_tex, (self.w * CELL_SIZE, self.h * CELL_SIZE))
            else:
                 # Fallback if not found (e.g. CWD mismatch)
                 print(f"FireHazard: Texture not found in registry: {path}")
                 self.texture = None

        except Exception as e:
            print(f"Failed to load Lava texture: {e}")
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
