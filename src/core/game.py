import pygame

from core.setup import GameSetup
from core.renderer import GameRenderer
from core.logic import GameLogic


class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Perform initial setup
        setup = GameSetup(self)
        setup.perform_setup()
        
        # Initialize subsystems
        self.renderer = GameRenderer(self)
        self.logic = GameLogic(self)

    def run(self):
        running = True
        # Main game loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                self.logic.handle_event(event)

            self.logic.update()
            self.renderer.draw()
            self.clock.tick(60)
        pygame.quit()

gameInstance = Game()
