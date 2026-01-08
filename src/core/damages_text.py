import pygame


class DamageText:
    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount
        self.timer = 60  # last 60 frames
        self.font = pygame.font.SysFont(None, 24)
        self.color = (255, 0, 0)

    def update(self):
        self.y -= 1  # upward movement
        self.timer -= 1

    def draw(self, screen, camera):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        text = self.font.render(f"-{self.amount}", True, self.color)
        screen.blit(text, (screen_x, screen_y))

    def is_alive(self):
        return self.timer > 0


class DamageTexts:
    def __init__(self):
        self.texts = []

    def spawn(self, x, y, amount):
        self.texts.append(DamageText(x, y, amount))

    def update(self):
        for text in self.texts[:]:
            text.update()
            if not text.is_alive():
                self.texts.remove(text)

    def draw(self, screen, camera):
        for text in self.texts:
            text.draw(screen, camera)
