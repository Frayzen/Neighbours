from pygame import mouse
import numpy as np
from entities.base import GridObject


class Enemy(GridObject):
    def __init__(self, x, y, w, h, speed=0.5):
        GridObject.__init__(self, x, y, w, h)
        self.speed = speed

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
