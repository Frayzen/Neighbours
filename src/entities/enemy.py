from pygame import mouse
import numpy as np
from entities.base import GridObject
from core.debug import debug


class Enemy(GridObject):
    def __init__(self, x, y, w, h, speed=0.5, health=100):
        GridObject.__init__(self, x, y, w, h)
        self.speed = speed
        self.health = health
        self.max_health = health

    def take_damage(self, amount):
        self.health -= amount
        debug.log(f"Enemy took {amount} damage. Health: {self.health}/{self.max_health}")
        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Enemy died!")
        # Logic to remove from game will be handled in GameLogic or here if we have reference

    def update(self, target_pos):
        GridObject.update(self)

        target = np.array(target_pos)
        cur = np.array((self.x, self.y))
        dir = target - cur
        distance = np.linalg.norm(dir)
        if distance > 0:
            norm = dir / distance
            self.x += norm[0] * self.speed
            self.y += norm[1] * self.speed
