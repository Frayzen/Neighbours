import pygame
from entities.base import GridObject
from core.debug import debug
from config.settings import ENEMY_SPEED, ENEMY_HEALTH, COLOR_ENEMY, ENEMY_DAMAGE



class Enemy(GridObject):
    def __init__(
        self,
        game,
        x, y,
        enemy_type="basic_enemy"
    ):
        from core.registry import Registry
        config = Registry.get_enemy_config(enemy_type)
        if not config:
            print(f"Warning: Enemy type '{enemy_type}' not found. Using defaults.")
            # Fallback defaults
            w, h = 1, 1
            color = COLOR_ENEMY
            speed = ENEMY_SPEED
            health = ENEMY_HEALTH
            damage = ENEMY_DAMAGE
            texture = None
        else:
            w = config.get('width', 1)
            h = config.get('height', 1)
            color = tuple(config.get('color', COLOR_ENEMY))
            speed = config.get('speed', ENEMY_SPEED)
            health = config.get('health', ENEMY_HEALTH)
            damage = config.get('damage', ENEMY_DAMAGE)
            texture = config.get('texture')

        super().__init__(x, y, w, h, color=color)
        self.game = game
        self.speed = speed
        self.health = health
        self.max_health = health
        self.damage = damage
        self.texture = texture

    def draw(self, screen, tile_size):
        if self.texture:
            # Scale texture if needed (or assume it's pre-scaled/correct size)
            # For now, let's scale it to the entity size
            scaled_texture = pygame.transform.scale(self.texture, (int(self.w * tile_size), int(self.h * tile_size)))
            screen.blit(scaled_texture, (self.x, self.y))
        else:
            super().draw(screen, tile_size)

        # Health bar settings
        bar_width = self.w * tile_size
        bar_height = 5
        bar_x = self.x
        bar_y = self.y - 10  # 10 pixels above the enemy

        # Draw background (red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Draw health (green)
        if self.health > 0:
            health_width = bar_width * (self.health / self.max_health)
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))

    def take_damage(self, amount):
        self.health -= amount
  

        # Spawn floating damage text
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)

        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Enemy died!")
        
        
    def update(self, target_pos):
        super().update(target_pos)

        target = pygame.math.Vector2(target_pos)
        cur = pygame.math.Vector2(self.x, self.y)

        if cur.distance_to(target) > 0:
            direction = (target - cur).normalize()
            self.x += direction.x * self.speed
            self.y += direction.y * self.speed

