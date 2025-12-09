from typing import List
import pygame
from random import randint, randrange

from consts import *
from enemy import Enemy
from object import GridObject
from player_mvt import Player


class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.gridObjects: List[GridObject] = []
        self.player = Player(100,100,50,5)

    def run(self):
        running = True
        # Main game loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill("purple")
            self.player.draw(self.screen)
            self.player.move(pygame.key.get_pressed())

            for obj in self.gridObjects:
                obj.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)
            self.handleEvents()
        pygame.quit()

    def handleEvents(self):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE]:
            self.gridObjects.append(
                Enemy(
                    randint(0, SCREEN_WIDTH),
                    randint(0, SCREEN_HEIGHT),
                    CELL_SIZE,
                    CELL_SIZE,
                    randint(50, 200) / 100,
                )
            )

        for obj in self.gridObjects:
            obj.update()


gameInstance = Game()
