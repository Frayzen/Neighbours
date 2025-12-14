import pygame
from entities.base import GridObject
from core.debug import debug
from config.settings import ENEMY_SPEED, ENEMY_HEALTH, COLOR_ENEMY, ENEMY_DAMAGE


class Enemy(GridObject):
    def __init__(self, x, y, w, h, speed=ENEMY_SPEED, health=ENEMY_HEALTH, damage=ENEMY_DAMAGE):
        super().__init__(x, y, w, h, color=COLOR_ENEMY)
        self.speed = speed
        self.health = health
        self.max_health = health
        self.damage = damage
        self.xp_value = 10 # Default XP value

    def take_damage(self, amount):
        self.health -= amount
        debug.log(f"Enemy took {amount} damage. Health: {self.health}/{self.max_health}")
        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Enemy died!")
        # Logic to remove from game will be handled in GameLogic or here if we have reference

    def update(self, target_pos):
        super().update(target_pos)

        target = pygame.math.Vector2(target_pos)
        cur = pygame.math.Vector2(self.x, self.y)
        
        if cur.distance_to(target) > 0:
            direction = (target - cur).normalize()
            self.x += direction.x * self.speed
            self.y += direction.y * self.speed
