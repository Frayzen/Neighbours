import pygame

from core.setup import GameSetup
from core.renderer import GameRenderer
from core.logic import GameLogic
from config.settings import FPS
from core.damages_text import DamageTexts

"""Florian LAINE"""

class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Perform initial setup
        self.setup = GameSetup(self)
        self.setup.perform_setup()
        
        # Initialize subsystems
        self.renderer = GameRenderer(self)
        self.logic = GameLogic(self)
        self.current_time = 0
        self.camera = Camera()
        self.damage_texts = DamageTexts()
        self.enemies = []
        
        self.paused = False
        
        # Auto-load logic
        from core.save_manager import SaveManager
        print(f"DEBUG: Checking for save file at {SaveManager.SAVE_FILE_PATH}")
        if SaveManager.has_save_file():
            print("DEBUG: Save file found. Auto-loading...")
            if SaveManager.load_game(self):
                self.paused = True # Start in pause menu as requested
            else:
                print("DEBUG: Load failed. Starting fresh.")
                self.paused = False
        else:
            print("DEBUG: No save file. Starting fresh.")
            self.paused = False

    def restart_game(self):
        # Reset game state
        self.setup.perform_setup()
        self.logic = GameLogic(self)
        self.paused = False

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
                        self.paused = not self.paused
                
                # Handle Pause Menu Inputs (Mouse)
                if self.paused:
                    self.logic.handle_pause_input(event)
                
                if not self.paused:
                    self.logic.handle_event(event)

            if not self.paused:
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
