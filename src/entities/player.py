#0 at the top left corner of the screen
#moving a cube smothly using arrow
from typing import Tuple
import pygame
# Initialize Pygame
pygame.init()

# Set up the display
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_PLAYER, PLAYER_MAX_HEALTH, PLAYER_INVULNERABILITY_DURATION
from combat.combat_manager import CombatManager
from combat.factory import WeaponFactory
from entities.base import GridObject
from core.physics import check_collision
from core.debug import debug

class Player(GridObject):
    def __init__(self, game, x, y, size, speed):
        super().__init__(x, y, size, size, color=COLOR_PLAYER)
        self.game = game
        self.speed = speed
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.invulnerable = False
        self.invulnerability_duration = PLAYER_INVULNERABILITY_DURATION  # ms
        self.last_hit_time = 0
        
        # Combat setup
        self.combat = CombatManager(self)
        # Equip default weapons using the factory
        try:
            self.combat.add_weapon(WeaponFactory.create_weapon("fireball_staff"))
            self.combat.add_weapon(WeaponFactory.create_weapon("basic_sword"))
        except Exception as e:
            print(f"Failed to equip default weapons: {e}")

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        
        # Handle invulnerability
        if self.invulnerable:
            if current_time - self.last_hit_time > self.invulnerability_duration:
                self.invulnerable = False

        self.combat.update(enemies, current_time)

    def take_damage(self, amount):
        if self.invulnerable:
            return

        self.health -= amount
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)
        self.invulnerable = True
        self.last_hit_time = pygame.time.get_ticks()
        debug.log(f"Player took {amount} damage! Health: {self.health}/{self.max_health}")
        
        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Player died!")
        # TODO: Handle player death (restart game, show game over screen, etc.)

    def move(self, keys, bounds: Tuple[int, int, int, int], world, tile_size: int): #movement using arrow keys or WASD
#pygame.K_ DIRECTION is used to detect key presses on this precise touch
        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed

        # Try moving X
        new_x = self.x + dx
        collision_x = check_collision(new_x, self.y, self.w, self.h, bounds, world, tile_size)
        if not collision_x:
            self.x = new_x
        elif isinstance(collision_x, tuple):
             return collision_x

        # Try moving Y
        new_y = self.y + dy
        collision_y = check_collision(self.x, new_y, self.w, self.h, bounds, world, tile_size)
        if not collision_y:
            self.y = new_y
        elif isinstance(collision_y, tuple):
             return collision_y
        
        return None

    def draw(self, surface, tile_size):
        # Draw player
        pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.w * tile_size, self.h * tile_size))
        
        # Draw weapon
        weapon = self.combat.current_weapon
        if weapon:
            # Simple representation: a small colored rect next to the player
            weapon_color = (200, 200, 200)
            if "fire" in weapon.name.lower():
                weapon_color = (255, 100, 0)
            elif "bow" in weapon.name.lower():
                weapon_color = (100, 255, 100)
            
            # Draw slightly offset
            wx = self.x + (self.w * tile_size) * 0.8
            wy = self.y + (self.h * tile_size) * 0.2
            pygame.draw.rect(surface, weapon_color, (wx, wy, 4, 10))
