from pygame import mouse
import numpy as np
from object import GridObject


class Enemy(GridObject):
    def __init__(self, x, y, w, h, speed=0.5):
        GridObject.__init__(self, x, y, w, h)
        self.speed = speed

    def update(self):
        GridObject.update(self)
        target = np.array(mouse.get_pos())
        cur = np.array((self.x, self.y))
        dir = target - cur
        norm = dir / np.linalg.norm(dir)
        self.x += norm[0] * self.speed
        self.y += norm[1] * self.speed
