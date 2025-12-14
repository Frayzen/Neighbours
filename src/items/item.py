from entities.base import GridObject
from config.settings import COLOR_RARITY, BASE_DIR
from core.debug import debug
import pygame
import os

class Item(GridObject):
    def __init__(self, x, y, item_data):
        self.rarity_color = COLOR_RARITY.get(item_data["rarity"], (255, 255, 255))
        self.item_color = item_data.get("color", self.rarity_color) # Default to rarity color if not specified
        super().__init__(x, y, 0.5, 0.5, color=self.item_color)
        
        self.name = item_data["name"]
        self.type = item_data["type"]
        self.rarity = item_data["rarity"]
        self.effects = item_data["effects"]
        self.description = item_data["description"]
        self.target_weapon = item_data.get("target_weapon", None)
        self.target_tag = item_data.get("target_tag", None)
        self.duration = item_data.get("duration", 0)
        
        # Texture handling
        self.image = None
        texture_path = item_data.get("texture_path", None)
        if texture_path:
            full_path = os.path.join(BASE_DIR, texture_path)
            if os.path.exists(full_path):
                try:
                    loaded_image = pygame.image.load(full_path).convert_alpha()
                    self.image = loaded_image
                    debug.log(f"Loaded texture for {self.name}: {texture_path}")
                except Exception as e:
                     debug.log(f"Failed to load texture {texture_path}: {e}")
            else:
                debug.log(f"Texture not found: {full_path}")

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

    def draw(self, screen, tile_size):
        rect = (self.x, self.y, self.w * tile_size, self.h * tile_size)
        
        if self.image:
            # Scale image to fit item size
            scaled_image = pygame.transform.scale(self.image, (int(self.w * tile_size), int(self.h * tile_size)))
            screen.blit(scaled_image, (self.x, self.y))
        else:
            # Draw item background (specific color)
            pygame.draw.rect(screen, self.item_color, rect)
            
            # Draw rarity border
            border_width = 2
            pygame.draw.rect(screen, self.rarity_color, rect, border_width)
