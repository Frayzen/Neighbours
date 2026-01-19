import pygame
from entities.base import GridObject
from core.director import Director
from config.settings import CELL_SIZE, COLOR_ENEMY
from core.debug import debug
from random import randint

class Spawner(GridObject):
    def __init__(self, game, x, y, trigger_distance=8, fixed_wave=None):
        super().__init__(x, y, 1, 1, color=(50, 50, 50)) 
        self.game = game
        self.trigger_distance_sq = (trigger_distance * CELL_SIZE) ** 2
        self.triggered = False
        self.director = Director(game)
        self.fixed_wave = fixed_wave
        
        # Load Ground Texture
        # We can use Registry or direct load. Let's try to match the world's ground style?
        # Or just use a generic one.
        try:
             import os
             from config.settings import BASE_DIR
             # Pick a random ground texture to blend in
             num = randint(1, 6)
             tex_path = os.path.join(BASE_DIR, "assets", "images", "Ground", f"Ground{num}.png")
             if os.path.exists(tex_path):
                 raw = pygame.image.load(tex_path).convert_alpha()
                 self.texture = pygame.transform.scale(raw, (int(self.w*CELL_SIZE), int(self.h*CELL_SIZE)))
                 self.color = None # Disable color rect drawing if texture exists
        except Exception as e:
            print(f"Failed to load Spawner texture: {e}")
        
    def update(self, *args, **kwargs):
        if self.triggered:
            return
            
        # Check distance to player
        player = self.game.player
        if not player:
            return
            
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx*dx + dy*dy
        
        if dist_sq <= self.trigger_distance_sq:
            self.trigger_wave()
            
    def trigger_wave(self):
        self.triggered = True
        debug.log(f"Spawner at ({int(self.x/CELL_SIZE)}, {int(self.y/CELL_SIZE)}) activated!")
        
        if self.fixed_wave:
            wave = self.fixed_wave
            debug.log(f"Spawner releasing FIXED wave: {wave}")
        else:
            # Calculate Budget
            budget = self.director.calculate_difficulty_budget()
            
            # Determine wave composition
            wave = self.director.generate_wave(budget)
            
            if not wave:
                debug.log("Director generated empty wave (Low budget?). Spawning fallback basic enemy.")
                wave = ["basic_enemy"]
            
        # Spawn enemies
        from entities.enemy import Enemy
        
        for enemy_type in wave:
            # Attempt to spawn in valid adjacent tile
            spawn_x, spawn_y = self._find_spawn_pos()
            if spawn_x is not None:
                enemy = Enemy(self.game, spawn_x, spawn_y, enemy_type)
                self.game.gridObjects.append(enemy)
                
    def _find_spawn_pos(self):
        # Try random positions around spawner
        gx = int(self.x / CELL_SIZE)
        gy = int(self.y / CELL_SIZE)
        
        for _ in range(5):
            off_x = randint(-2, 2)
            off_y = randint(-2, 2)
            
            tx = gx + off_x
            ty = gy + off_y
            
            # Bounds check
            if 0 <= tx < self.game.world.width and 0 <= ty < self.game.world.height:
                cell = self.game.world.get_cell(tx, ty)
                if cell and cell.walkable:
                     return tx * CELL_SIZE, ty * CELL_SIZE
                     
        return self.x, self.y # Fallback to on top of spawner
        
    def draw(self, screen):
        # Draw disguise texture (always visible if loaded)
        if hasattr(self, 'texture') and self.texture:
            screen.blit(self.texture, (self.x, self.y))
        elif getattr(self.game, 'show_debug_path', False):
             # Draw placeholder only in debug mode if no texture
             super().draw(screen)

        # Draw debug info
        if getattr(self.game, 'show_debug_path', False):
             # Draw range circle
             pygame.draw.circle(screen, (0, 255, 0), 
                                (int(self.x + self.w*CELL_SIZE/2), int(self.y + self.h*CELL_SIZE/2)), 
                                int(self.trigger_distance_sq**0.5), 1)
