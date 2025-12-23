import pygame

from core.setup import GameSetup
from core.renderer import GameRenderer
from core.logic import GameLogic
from config.settings import FPS
from core.damages_text import DamageTexts

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
        self.current_time = 0
        self.camera = Camera()
        self.damage_texts = DamageTexts()
        self.enemies = []

    def run(self):
        running = True
        # Main game loop
        while running:
            self.current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                self.logic.handle_event(event)

            self.logic.update()
            self.damage_texts.update()
            self.renderer.draw()
            self.clock.tick(FPS)
        pygame.quit()


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0


gameInstance = Game()
