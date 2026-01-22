from entities.base import GridObject
import pygame
from config.settings import CELL_SIZE, BASE_DIR
import os

class Door(GridObject):
    def __init__(self, game, x, y):
        # Door covers the scaled area (e.g., 2x2)
        from config.settings import MAZE_SCALE_UP
        width = MAZE_SCALE_UP
        height = MAZE_SCALE_UP
        
        super().__init__(x, y, width, height, color=(139, 69, 19))
        self.game = game
        self.is_open = False
        self.texture_open = None
        self.texture_closed = None
        self.rotation = 0 # Degrees
        
        # Load textures
        self.load_textures()
        
        self.calculate_orientation()

    def calculate_orientation(self):
        if not self.game or not self.game.world:
            print("Door: World not ready for orientation calc")
            return

        cx = int((self.x + (self.w * CELL_SIZE)/2) // CELL_SIZE)
        cy = int((self.y + (self.h * CELL_SIZE)/2) // CELL_SIZE)
        
        world = self.game.world
        
        # Use simple int division above to be safe
        
        # Safety bounds check
        if cx < 2 or cx >= world.width - 2 or cy < 2 or cy >= world.height - 2:
             print(f"Door: Out of bounds for check at {cx},{cy}")
             return

        left_cell = world.get_cell(cx - 2, cy) 
        right_cell = world.get_cell(cx + 2, cy)
        top_cell = world.get_cell(cx, cy - 2)
        bottom_cell = world.get_cell(cx, cy + 2)
        
        is_wall_horyz = (left_cell and getattr(left_cell, 'name', '') == "Wall") or (right_cell and getattr(right_cell, 'name', '') == "Wall")
        is_wall_vert = (top_cell and getattr(top_cell, 'name', '') == "Wall") or (bottom_cell and getattr(bottom_cell, 'name', '') == "Wall")
        
        if is_wall_vert and not is_wall_horyz:
             self.rotation = 90
        elif is_wall_horyz and not is_wall_vert:
             self.rotation = 0
        else:
             if (left_cell and getattr(left_cell, 'walkable', False)) and (right_cell and getattr(right_cell, 'walkable', True)):
                 self.rotation = 90
             else:
                 self.rotation = 0

        # Apply rotation to textures
        if self.rotation != 0:
            if self.texture_open:
                self.texture_open = pygame.transform.rotate(self.texture_open, self.rotation)
            if self.texture_closed:
                self.texture_closed = pygame.transform.rotate(self.texture_closed, self.rotation)
                
        # Set initial
        self.texture = self.texture_closed

    def load_textures(self):
        try:
             import os
             from config.settings import BASE_DIR
             
             path_closed = os.path.join(BASE_DIR, "assets", "images", "Door", "ClosedDoor.png")
             path_open = os.path.join(BASE_DIR, "assets", "images", "Door", "OpenDoor.png")
             
             if os.path.exists(path_closed):
                 raw = pygame.image.load(path_closed).convert_alpha()
                 self.texture_closed = pygame.transform.scale(raw, (int(self.w*CELL_SIZE), int(self.h*CELL_SIZE)))
             else:
                 print(f"ClosedDoor texture not found at {path_closed}")
                 
             if os.path.exists(path_open):
                 raw = pygame.image.load(path_open).convert_alpha()
                 self.texture_open = pygame.transform.scale(raw, (int(self.w*CELL_SIZE), int(self.h*CELL_SIZE)))
             else:
                 print(f"OpenDoor texture not found at {path_open}")
                 
             self.texture = self.texture_closed
             
        except Exception as e:
            print(f"Failed to load Door textures: {e}")

    def update(self, *args, **kwargs):
        # Check proximity to player
        if not self.game.player:
            return
            
        player = self.game.player
        # Distance center to center
        cx = self.x + (self.w * CELL_SIZE)/2
        cy = self.y + (self.h * CELL_SIZE)/2
        px = player.x + (player.w * CELL_SIZE)/2
        py = player.y + (player.h * CELL_SIZE)/2
        
        dist_sq = (cx - px)**2 + (cy - py)**2
        threshold = (2.5 * CELL_SIZE) ** 2 # 2.5 tiles radius
        
        previous_state = self.is_open
        if dist_sq < threshold:
            self.is_open = True
        else:
            self.is_open = False
            
        if self.is_open != previous_state:
            self.texture = self.texture_open if self.is_open else self.texture_closed

    def draw(self, screen):
        if self.texture:
            screen.blit(self.texture, (self.x, self.y))
        else:
            super().draw(screen)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['texture'] = None
        state['texture_open'] = None
        state['texture_closed'] = None
        if 'game' in state:
            del state['game']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.texture = None
        self.texture_open = None
        self.texture_closed = None
        self.game = None

    def post_load(self):
        self.load_textures()
        # Rotation logic
        # We need to re-apply rotation because load_textures loads fresh (0 deg) images.
        # But we saved self.rotation, so just apply it.
        if hasattr(self, 'rotation') and self.rotation != 0:
            if self.texture_open:
                self.texture_open = pygame.transform.rotate(self.texture_open, self.rotation)
            if self.texture_closed:
                self.texture_closed = pygame.transform.rotate(self.texture_closed, self.rotation)
        
        # Restore current state texture
        if hasattr(self, 'is_open'):
             self.texture = self.texture_open if self.is_open else self.texture_closed
