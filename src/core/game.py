import pygame

from core.camera import Camera
from core.setup import GameSetup
from core.renderer import GameRenderer
from core.logic import GameLogic
from config.settings import FPS
from core.damages_text import DamageTexts


class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.player = None

        # Level Management
        from core.level_manager import LevelManager
        self.level_manager = LevelManager()

        # Perform initial setup
        self.current_layer_index = 0 # DEPRECATED: Use level_manager.get_level_index() logic
        self.setup = GameSetup(self)
        self.setup.perform_setup()

        # Initialize subsystems
        self.renderer = GameRenderer(self)
        self.logic = GameLogic(self)
        self.current_time = 0
        self.camera = Camera()
        self.damage_texts = DamageTexts()
        self.enemies = []
        self.projectiles = []

        self.paused = False

        # Debug
        self.show_debug_path = False
        self.debug_path_points = []

        # Auto-load logic
        from core.save_manager import SaveManager

        print(f"DEBUG: Checking for save file at {SaveManager.SAVE_FILE_PATH}")
        if SaveManager.has_save_file():
            print("DEBUG: Save file found. Auto-loading...")
            if SaveManager.load_game(self):
                self.paused = True  # Start in pause menu as requested
            else:
                print("DEBUG: Load failed. Starting fresh.")
                self.paused = False
                self.restart_game()
        else:
            print("DEBUG: No save file. Starting fresh.")
            self.paused = False

    def restart_game(self):
        # Reset game state
        self.current_layer_index = 0
        self.setup.perform_setup()
        self.logic = GameLogic(self)
        self.paused = False

    def next_layer(self):
        if not self.level_manager.advance_level():
            print("DEBUG: No more levels! Game Over or Loop?")
            return

        self.current_layer_index = self.level_manager.get_level_index()
        print(f"DEBUG: Generating level {self.current_layer_index}...")
        
        level_config = self.level_manager.get_current_level()
        
        # Determine player health and other persistent state if needed
        # For now, we just regenerate the world
        self.world = self.setup.world_loader.generate(level_config)
        
        # Re-initialize entities for the new layer (Preserve Player)
        self.setup.respawn_player() 
        
        # Important: Update logic with new references if needed
        self.logic = GameLogic(self)
        
        # Reload renderer cache
        self.renderer.reload_world()
        
        print(f"DEBUG: Layer {self.current_layer_index} generated.")

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
                self.camera.update(self.player)

            self.renderer.draw(self.camera)

            self.clock.tick(FPS)
            # print(self.clock.get_fps())
        pygame.quit()


gameInstance = Game()
